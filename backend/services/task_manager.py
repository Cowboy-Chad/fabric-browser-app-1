import uuid
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models import AnalysisResult, AnalysisType, AnalysisStatus
from services.fabric_client import run_fabric
from services.youtube_client import get_youtube_transcript
from config import OPENROUTER_MODEL
from pricing import estimate_cost


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


async def run_analysis_task(
    db: AsyncSession,
    analysis_type: AnalysisType,
    target: str,
    pattern: Optional[str] = None,
    input_data: Optional[str] = None,
    youtube_url: Optional[str] = None,
    spotify_url: Optional[str] = None,
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

        transcript_text = None
        youtube_transcript_err = None
        if youtube_url:
            title, channel, channel_url, transcript_text, youtube_transcript_err = await get_youtube_transcript(youtube_url)

        t0 = time.monotonic()
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
        input_t = estimate_tokens(input_text_len)
        output_t = estimate_tokens(output)
        i_cost, o_cost, t_cost = estimate_cost(model_used, input_t, output_t)

        if title and output:
            header = f"[{title}]({youtube_url})"
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
                        hours = delta.seconds // 3600
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
            if pattern:
                header += f"\nFabric Pattern: {pattern}"
            header += f"\nModel: {model_used}"
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            if minutes > 0:
                header += f"\nProcessing Time: {minutes}m {seconds}s"
            else:
                header += f"\nProcessing Time: {seconds}s"
            if t_cost > 0:
                cost_str = f"${t_cost:.4f}" if t_cost >= 0.001 else "< $0.001"
                header += f"\nEstimated Cost: {cost_str}"
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

        if meta:
            db_result.metadata_json = json.dumps(meta)
    except Exception as e:
        db_result.status = AnalysisStatus.FAILED
        db_result.error_message = str(e)
        db_result.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(db_result)
    return db_result