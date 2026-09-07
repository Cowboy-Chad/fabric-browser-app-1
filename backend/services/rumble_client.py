import asyncio
import os
import re
import sys
import uuid
import mimetypes
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import OPENROUTER_API_KEY, OPENROUTER_API_BASE_URL
from models import RumbleTranscript

RUMBLE_HEADER = ["--add-header", "Referer:https://rumble.com"]

MAI_TRANSCRIBE_MODEL = "microsoft/mai-transcribe-2"
MAI_TRANSCRIBE_RATE_PER_HOUR = 0.10
UPLOAD_DIR = "uploads"


def extract_rumble_id(url: str) -> Optional[str]:
    m = re.search(r"rumble\.com/v([a-z0-9]+)", url)
    if m:
        return m.group(1)
    return None


def _load_openrouter_key() -> Optional[str]:
    if OPENROUTER_API_KEY:
        return OPENROUTER_API_KEY
    env_file = Path.home() / ".config" / "fabric" / ".env"
    try:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip() or None
    except Exception as e:
        print(f"[rumble_client] error reading fabric .env: {e}", file=sys.stderr)
    return None


async def _fetch_metadata(url: str) -> dict:
    info = {
        "title": "", "view_count": "", "timestamp": "", "channel": "",
        "channel_url": "", "subs": "", "duration": "",
    }
    try:
        cmd = [
            "yt-dlp",
            *RUMBLE_HEADER,
            "--print", "title",
            "--print", "view_count",
            "--print", "timestamp",
            "--print", "channel",
            "--print", "channel_url",
            "--print", "channel_follower_count",
            "--print", "duration_string",
            url,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode("utf-8", errors="replace").strip().split("\n")
        info["title"] = lines[0] if len(lines) > 0 else ""
        info["view_count"] = lines[1] if len(lines) > 1 else ""
        info["timestamp"] = lines[2] if len(lines) > 2 else ""
        info["channel"] = lines[3] if len(lines) > 3 else ""
        info["channel_url"] = lines[4] if len(lines) > 4 else ""
        info["subs"] = lines[5] if len(lines) > 5 else ""
        info["duration"] = lines[6] if len(lines) > 6 else ""
    except Exception as e:
        print(f"[rumble_client] metadata fetch error: {e}", file=sys.stderr)
    return info


async def _download_audio(url: str, tag: str) -> Optional[str]:
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        outtmpl = os.path.join(UPLOAD_DIR, f"rumble_{tag}.%(ext)s")
        cmd = [
            "yt-dlp", "-x", "--audio-format", "mp3",
            *RUMBLE_HEADER,
            "-o", outtmpl,
            url,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        for fname in os.listdir(UPLOAD_DIR):
            if fname.startswith(f"rumble_{tag}") and fname.endswith((".mp3", ".aac", ".m4a", ".wav", ".opus", ".webm")):
                return os.path.join(UPLOAD_DIR, fname)
    except Exception as e:
        print(f"[rumble_client] audio download error: {e}", file=sys.stderr)
    return None


async def _transcribe_with_mai(audio_path: str) -> Optional[str]:
    key = _load_openrouter_key()
    if not key:
        print("[rumble_client] no OpenRouter API key available for transcription", file=sys.stderr)
        return None

    base = (OPENROUTER_API_BASE_URL or "https://openrouter.ai/api/v1").rstrip("/")
    url = f"{base}/audio/transcriptions"

    mime, _ = mimetypes.guess_type(audio_path)
    mime = mime or "audio/mpeg"

    try:
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, mime)}
            data = {"model": MAI_TRANSCRIBE_MODEL}
            headers = {"Authorization": f"Bearer {key}"}
            async with httpx.AsyncClient(timeout=1200) as client:
                resp = await client.post(url, headers=headers, data=data, files=files)
                resp.raise_for_status()
                payload = resp.json()
        text = (payload.get("text") or "").strip()
        return text if text else None
    except Exception as e:
        print(f"[rumble_client] MAI transcription error: {e}", file=sys.stderr)
        return None


async def get_rumble_transcript(url: str, progress_cb=None) -> dict:
    video_id = extract_rumble_id(url)
    if not video_id:
        return {"title": "", "channel": "", "channel_url": "",
                "view_count": "", "timestamp": "", "subs": "",
                "duration": "", "transcript": "", "method": "",
                "error": "Could not parse Rumble video ID from URL"}

    meta = await _fetch_metadata(url)
    if not meta["title"]:
        return {"title": "", "channel": "", "channel_url": "",
                "view_count": "", "timestamp": "", "subs": "",
                "duration": "", "transcript": "", "method": "",
                "error": "Could not fetch video metadata (Rumble may be blocking the request)"}

    tag = uuid.uuid4().hex[:8]

    if progress_cb:
        await progress_cb("Downloading audio from Rumble...")
    audio_path = await _download_audio(url, tag)
    if not audio_path:
        return {
            "title": meta["title"], "channel": meta["channel"],
            "channel_url": meta["channel_url"],
            "view_count": meta["view_count"], "timestamp": meta["timestamp"],
            "subs": meta["subs"], "duration": meta["duration"],
            "transcript": "", "method": "",
            "error": "Failed to download audio from Rumble",
        }

    if progress_cb:
        await progress_cb(f"Transcribing with {MAI_TRANSCRIBE_MODEL} ($0.10/hour)...")
    transcript = await _transcribe_with_mai(audio_path)

    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        print(f"[rumble_client] cleanup error: {e}", file=sys.stderr)

    if not transcript:
        return {
            "title": meta["title"], "channel": meta["channel"],
            "channel_url": meta["channel_url"],
            "view_count": meta["view_count"], "timestamp": meta["timestamp"],
            "subs": meta["subs"], "duration": meta["duration"],
            "transcript": "", "method": "",
            "error": "Audio transcription failed (Microsoft MAI-Transcribe 2 returned no text)",
        }

    return {
        "title": meta["title"], "channel": meta["channel"],
        "channel_url": meta["channel_url"],
        "view_count": meta["view_count"], "timestamp": meta["timestamp"],
        "subs": meta["subs"], "duration": meta["duration"],
        "transcript": transcript, "method": "mai_transcription", "error": "",
    }


async def get_rumble_history_transcript(db: AsyncSession, video_id: str) -> Optional[RumbleTranscript]:
    stmt = select(RumbleTranscript).where(RumbleTranscript.video_id == video_id)
    result = (await db.execute(stmt)).scalar_one_or_none()
    return result


async def save_rumble_transcript_to_history(
    db: AsyncSession,
    url: str,
    video_id: str,
    info: dict,
) -> RumbleTranscript:
    record = RumbleTranscript(
        video_id=video_id,
        url=url,
        title=info.get("title"),
        channel=info.get("channel"),
        channel_url=info.get("channel_url"),
        view_count=info.get("view_count"),
        timestamp=info.get("timestamp"),
        subs=info.get("subs"),
        duration=info.get("duration"),
        transcript=info.get("transcript"),
        method=info.get("method") or "mai_transcription",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record