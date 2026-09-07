import uuid
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models import AnalysisResult, AnalysisType, AnalysisStatus
from services.fabric_client import run_fabric
from services.youtube_client import (
    get_youtube_transcript,
    get_youtube_history_transcript,
    save_youtube_transcript_to_history,
    extract_video_id,
)
from services.rumble_client import (
    get_rumble_transcript,
    get_rumble_history_transcript,
    save_rumble_transcript_to_history,
    extract_rumble_id,
    MAI_TRANSCRIBE_MODEL,
    MAI_TRANSCRIBE_RATE_PER_HOUR,
)
from config import OPENROUTER_MODEL
from pricing import estimate_cost, refresh_live_pricing
import tiktoken
import re


def _parse_duration_to_seconds(duration: str) -> float:
    if not duration:
        return 0.0
    candidate = (duration or "").strip()
    candidate = candidate.lower()
    for prefix in ("min ", "min", "hrs ", "hrs", "hr ", "sec ", "sec", "s "):
        candidate = candidate.replace(prefix, "")
    parts = [p for p in re.split(r"[:hm\.\s]", candidate) if p != ""]
    if not parts:
        return 0.0
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            minutes, seconds = float(parts[0]), float(parts[1])
            return minutes * 60 + seconds
        if len(parts) == 3:
            hours, minutes, seconds = float(parts[0]), float(parts[1]), float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return float(parts[0])
    except (ValueError, TypeError):
        return 0.0


async def _update_progress(db: AsyncSession, result: AnalysisResult, message: str):
    result.progress = message
    await db.commit()
    await db.refresh(result)


_MODEL_ENCODING_CACHE = {}


def _get_encoding_for_model(model: str):
    if model in _MODEL_ENCODING_CACHE:
        return _MODEL_ENCODING_CACHE[model]
    model_lower = model.lower()
    try:
        if any(k in model_lower for k in ("gpt-5", "o1-", "o3-", "o4-", "o1-pro", "o3-pro", "o4-mini")):
            enc = tiktoken.get_encoding("o200k_base")
        elif any(k in model_lower for k in ("gpt-4", "gpt-3.5", "gpt-audio", "gpt-chat")):
            enc = tiktoken.get_encoding("cl100k_base")
        elif any(k in model_lower for k in ("deepseek", "mistral", "mixtral", "codestral", "ministral", "voxtral")):
            enc = tiktoken.get_encoding("cl100k_base")
        elif "text-embedding" in model_lower:
            enc = tiktoken.get_encoding("cl100k_base")
        elif "gpt-3" in model_lower and "turbo" not in model_lower and "instruct" not in model_lower:
            enc = tiktoken.get_encoding("r50k_base")
        else:
            enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        enc = None
    _MODEL_ENCODING_CACHE[model] = enc
    return enc


def count_tokens(text: str, model: str) -> tuple[int, str]:
    if not text:
        return 0, "heuristic"
    text = text.strip()
    if not text:
        return 0, "heuristic"
    enc = _get_encoding_for_model(model)
    if enc is not None:
        try:
            tokens = len(enc.encode(text))
            return max(1, tokens), "tiktoken"
        except Exception:
            pass
    return max(1, len(text) // 3), "heuristic"


async def run_analysis_task(
    db: AsyncSession,
    analysis_type: AnalysisType,
    target: str,
    pattern: Optional[str] = None,
    input_data: Optional[str] = None,
    youtube_url: Optional[str] = None,
    spotify_url: Optional[str] = None,
    rumble_url: Optional[str] = None,
    scrape_url: Optional[str] = None,
    additional_args: Optional[list[str]] = None,
    model: Optional[str] = None,
):
    result_id = str(uuid.uuid4())
    db_result = AnalysisResult(
        id=result_id,
        type=analysis_type,
        status=AnalysisStatus.RUNNING,
        target=target,
        pattern=pattern,
        input_data=input_data or target,
    )
    db.add(db_result)
    await db.commit()

    try:
        title = ""
        view_count = ""
        timestamp = ""
        channel = ""
        channel_url = ""
        subs = ""
        duration = ""
        model_used = model or OPENROUTER_MODEL

        t0 = time.monotonic()

        transcript_text = None
        youtube_transcript_err = None
        yt_video_id = None
        if youtube_url:
            yt_video_id = extract_video_id(youtube_url)
            await _update_progress(db, db_result, "Checking for existing transcript in YouTube history...")
            yt_existing = None
            if yt_video_id:
                yt_existing = await get_youtube_history_transcript(db, yt_video_id)
            if yt_existing and yt_existing.transcript:
                info = {
                    "title": yt_existing.title,
                    "channel": yt_existing.channel,
                    "channel_url": yt_existing.channel_url,
                    "view_count": yt_existing.view_count,
                    "timestamp": yt_existing.timestamp,
                    "subs": yt_existing.subs,
                    "duration": yt_existing.duration,
                    "transcript": yt_existing.transcript,
                    "error": "",
                }
                await _update_progress(db, db_result, "Found existing transcript in YouTube history. Reusing it.")
            else:
                info = await get_youtube_transcript(youtube_url)
                if info.get("transcript") and yt_video_id:
                    await save_youtube_transcript_to_history(db, youtube_url, yt_video_id, info)
                await _update_progress(db, db_result, "Transcript fetched and saved to YouTube history.")
            title = info.get("title", "")
            channel = info.get("channel", "")
            channel_url = info.get("channel_url", "")
            view_count = info.get("view_count", "")
            timestamp = info.get("timestamp", "")
            subs = info.get("subs", "")
            duration = info.get("duration", "")
            transcript_text = info.get("transcript")
            youtube_transcript_err = info.get("error")

        rumble_transcript_err = None
        transcription_seconds = 0.0
        if rumble_url:
            video_id = extract_rumble_id(rumble_url)
            transcript_source = "none"
            await _update_progress(db, db_result, "Checking for existing transcript in history...")

            existing = None
            if video_id:
                existing = await get_rumble_history_transcript(db, video_id)

            if existing and existing.transcript:
                info = {
                    "title": existing.title,
                    "channel": existing.channel,
                    "channel_url": existing.channel_url,
                    "view_count": existing.view_count,
                    "timestamp": existing.timestamp,
                    "subs": existing.subs,
                    "duration": existing.duration,
                    "transcript": existing.transcript,
                    "error": "",
                }
                transcript_source = "history"
                await _update_progress(db, db_result, "Found existing transcript in history. Skipping audio download and transcription.")
            else:
                info = await get_rumble_transcript(
                    rumble_url,
                    progress_cb=lambda msg: _update_progress(db, db_result, msg),
                )
                transcript_source = "downloaded"
                if video_id and info.get("transcript"):
                    await save_rumble_transcript_to_history(db, rumble_url, video_id, info)

            title = info.get("title", "")
            channel = info.get("channel", "")
            channel_url = info.get("channel_url", "")
            view_count = info.get("view_count", "")
            timestamp = info.get("timestamp", "")
            subs = info.get("subs", "")
            duration = info.get("duration", "")
            transcript_text = info.get("transcript")
            rumble_transcript_err = info.get("error")

            if transcript_source == "downloaded" and info.get("method") == "mai_transcription":
                transcription_seconds = _parse_duration_to_seconds(duration)

        if (youtube_url or rumble_url) and transcript_text:
            await _update_progress(db, db_result, f"Running {pattern} analysis with {model_used}...")

        if youtube_url and transcript_text:
            output, err, cmd_str = await run_fabric(
                pattern=pattern,
                input_text=transcript_text,
                model=model_used,
            )
        elif youtube_url:
            output = ""
            err = youtube_transcript_err or "No transcript available"
            cmd_str = ""
        elif rumble_url and transcript_text:
            output, err, cmd_str = await run_fabric(
                pattern=pattern,
                input_text=transcript_text,
                model=model_used,
            )
        elif rumble_url:
            output = ""
            err = rumble_transcript_err or "No transcript available"
            cmd_str = ""
        else:
            output, err, cmd_str = await run_fabric(
                pattern=pattern,
                input_text=input_data if not any([spotify_url, scrape_url]) else None,
                spotify_url=spotify_url,
                scrape_url=scrape_url,
                additional_args=additional_args,
                model=model_used,
            )
        elapsed = time.monotonic() - t0

        input_text_len = transcript_text or input_data or target or ""
        input_t, input_method = count_tokens(input_text_len, model_used)
        output_t, output_method = count_tokens(output, model_used)

        await refresh_live_pricing()
        i_cost, o_cost, t_cost, pricing_source = estimate_cost(model_used, input_t, output_t)

        if title and output:
            video_url = youtube_url or rumble_url
            header = f"[{title}]({video_url})"
            if view_count:
                header += f"\nViews: {int(view_count):,}" if view_count.isdigit() else f"\nViews: {view_count}"
            if channel and channel_url:
                sub_str = ""
                if subs and subs.isdigit():
                    sub_str = f" ({int(subs):,} subscribers)"
                header += f"\nChannel: [{channel}]({channel_url}){sub_str}"
            elif channel:
                sub_str = ""
                if subs and subs.isdigit():
                    sub_str = f" ({int(subs):,} subscribers)"
                header += f"\nChannel: {channel}{sub_str}"
            if timestamp and timestamp.isdigit():
                try:
                    published = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
                    now = datetime.now(timezone.utc)
                    delta = now - published
                    if delta.days >= 365:
                        years = delta.days // 365
                        relative = f"{years} year{'s' if years != 1 else ''} ago"
                    elif delta.days >= 30:
                        months = delta.days // 30
                        relative = f"{months} month{'s' if months != 1 else ''} ago"
                    elif delta.days >= 1:
                        relative = f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
                    elif delta.seconds >= 3600:
                        hours = delta.seconds // 60
                        relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
                    elif delta.seconds >= 60:
                        minutes = delta.seconds // 60
                        relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                    else:
                        relative = "less than a minute ago"
                    header += f"\nPublished: {published.strftime('%Y-%m-%d %H:%M UTC')} ({relative})"
                except (ValueError, OSError):
                    pass
            if duration:
                header += f"\nDuration: {duration}"
            if rumble_url:
                if transcript_source == "history":
                    header += "\nTranscript: Reused from Rumble history"
                elif info.get("method"):
                    transc_cost = (transcription_seconds / 3600.0) * MAI_TRANSCRIBE_RATE_PER_HOUR
                    header += f"\nTranscript: Audio downloaded and transcribed with {MAI_TRANSCRIBE_MODEL}"
                    if transc_cost > 0:
                        header += f" (${transc_cost:.4f} @ $0.10/hr)"
            if pattern:
                header += f"\nFabric Pattern: {pattern}"
            header += f"\nModel: {model_used}"
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            if minutes > 0:
                header += f"\nProcessing Time: {minutes}m {seconds}s"
            else:
                header += f"\nProcessing Time: {seconds}s"
            token_method = input_method if input_method == output_method else f"{input_method}/{output_method}"
            header += f"\nTokens: {input_t} in / {output_t} out (via {token_method})"
            if t_cost > 0:
                cost_str = f"${t_cost:.4f}" if t_cost >= 0.001 else "< $0.001"
                header += f"\nEstimated Cost: {cost_str}"
                header += f"\nPricing Source: {pricing_source}"
            output = f"{header}\n{'-' * 40}\n\n{output}"

        db_result.status = AnalysisStatus.COMPLETED if (output and not err) else AnalysisStatus.FAILED
        db_result.output_data = output
        db_result.error_message = err if err else None
        db_result.raw_fabric_command = cmd_str
        db_result.completed_at = datetime.now(timezone.utc)

        meta = {}
        if title:
            meta["video_title"] = title
        meta["input_tokens"] = input_t
        meta["output_tokens"] = output_t
        meta["cost_estimate"] = t_cost
        meta["cost_input"] = i_cost
        meta["cost_output"] = o_cost
        meta["model"] = model_used
        meta["processing_time_seconds"] = round(elapsed, 2)
        meta["token_method"] = input_method if input_method == output_method else f"{input_method}/{output_method}"
        meta["pricing_source"] = pricing_source
        if rumble_url:
            meta["transcript_source"] = transcript_source
            if info.get("method"):
                meta["transcription_model"] = MAI_TRANSCRIBE_MODEL
                meta["transcription_seconds"] = round(transcription_seconds, 2)
                meta["transcription_cost"] = round(
                    (transcription_seconds / 3600.0) * MAI_TRANSCRIBE_RATE_PER_HOUR, 6
                )
            meta["transcript_contains"] = len(transcript_text or "")

        if meta:
            db_result.metadata_json = json.dumps(meta)

        if db_result.status == AnalysisStatus.COMPLETED:
            await _update_progress(db, db_result, "Analysis complete.")

    except Exception as e:
        db_result.status = AnalysisStatus.FAILED
        db_result.error_message = str(e)
        db_result.progress = f"Failed: {e}"
        db_result.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(db_result)
    return db_result