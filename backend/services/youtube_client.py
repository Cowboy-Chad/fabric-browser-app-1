import asyncio
import re
import sys
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config import YOUTUBE_COOKIES_BROWSER
from models import YouTubeTranscript


def extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:v=|\/embed\/|\/shorts\/|\/live\/|youtu\.be\/)([0-9A-Za-z_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _fetch_transcript_text(video_id: str) -> str:
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id)
    return " ".join(segment.text for segment in transcript)


def _fetch_video_info(url: str, video_id: str) -> dict:
    info = {"title": "", "channel": "", "channel_url": ""}
    try:
        resp = httpx.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            follow_redirects=True,
        )
        if resp.status_code == 200:
            data = resp.json()
            info["title"] = data.get("title", "")
            info["channel"] = data.get("author_name", "")
            info["channel_url"] = data.get("author_url", "")
    except Exception:
        pass
    return info


async def get_youtube_metadata(url: str) -> dict:
    info = {"title": "", "view_count": "", "timestamp": "", "channel": "", "channel_url": "", "subs": "", "duration": ""}
    try:
        cmd = ["yt-dlp"]
        if YOUTUBE_COOKIES_BROWSER:
            cmd.extend(["--cookies-from-browser", YOUTUBE_COOKIES_BROWSER])
        cmd.extend(["--print", "title", "--print", "view_count", "--print", "timestamp",
            "--print", "channel", "--print", "channel_url", "--print", "channel_follower_count",
            "--print", "duration_string", url])
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
        print(f"[youtube_client] yt-dlp metadata fetch error for {url}: {type(e).__name__}: {e}", file=sys.stderr)
    return info


def _result(title="", channel="", channel_url="", view_count="", timestamp="", subs="", duration="", transcript="", error=""):
    return {
        "title": title,
        "channel": channel,
        "channel_url": channel_url,
        "view_count": view_count,
        "timestamp": timestamp,
        "subs": subs,
        "duration": duration,
        "transcript": transcript,
        "error": error,
    }





async def get_youtube_transcript(url: str) -> dict:
    video_id = extract_video_id(url)
    if not video_id:
        return _result(error="Could not parse video ID from URL")

    oembed = _fetch_video_info(url, video_id)
    meta = await get_youtube_metadata(url)

    title = meta["title"] or oembed["title"]
    channel = meta["channel"] or oembed["channel"]
    channel_url = meta["channel_url"] or oembed["channel_url"]
    view_count = meta["view_count"]
    timestamp = meta["timestamp"]
    subs = meta["subs"]
    duration = meta["duration"]

    try:
        transcript = await asyncio.to_thread(_fetch_transcript_text, video_id)
    except TranscriptsDisabled:
        return _result(title, channel, channel_url, view_count, timestamp, subs, duration, "", "Transcripts are disabled for this video")
    except NoTranscriptFound:
        return _result(title, channel, channel_url, view_count, timestamp, subs, duration, "", "No transcript found for this video")
    except VideoUnavailable:
        return _result(title, channel, channel_url, view_count, timestamp, subs, duration, "", "Video unavailable")
    except Exception as e:
        print(f"[youtube_client] transcript fetch error for {url}: {type(e).__name__}: {e}", file=sys.stderr)
        return _result(title, channel, channel_url, view_count, timestamp, subs, duration, "", f"Transcript error: {e}")

    if not transcript or not transcript.strip():
        return _result(title, channel, channel_url, view_count, timestamp, subs, duration, "", "Empty transcript returned")

    return _result(title, channel, channel_url, view_count, timestamp, subs, duration, transcript, "")


async def get_youtube_history_transcript(db: AsyncSession, video_id: str) -> Optional[YouTubeTranscript]:
    stmt = select(YouTubeTranscript).where(YouTubeTranscript.video_id == video_id)
    result = (await db.execute(stmt)).scalar_one_or_none()
    return result


async def save_youtube_transcript_to_history(
    db: AsyncSession,
    url: str,
    video_id: str,
    info: dict,
) -> YouTubeTranscript:
    record = YouTubeTranscript(
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
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
