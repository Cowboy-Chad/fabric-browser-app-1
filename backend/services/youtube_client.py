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
            timeout=15.0,
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


async def get_youtube_transcript(url: str) -> tuple[str, str, str, str, str]:
    video_id = extract_video_id(url)
    if not video_id:
        return "", "", "", "", "Could not parse video ID from URL"

    info = _fetch_video_info(url, video_id)

    try:
        transcript = await asyncio.to_thread(_fetch_transcript_text, video_id)
    except TranscriptsDisabled:
        return info["title"], info["channel"], info["channel_url"], "", "Transcripts are disabled for this video"
    except NoTranscriptFound:
        return info["title"], info["channel"], info["channel_url"], "", "No transcript found for this video"
    except VideoUnavailable:
        return info["title"], info["channel"], info["channel_url"], "", "Video unavailable"
    except Exception as e:
        print(f"[youtube_client] transcript fetch error for {url}: {type(e).__name__}: {e}", file=sys.stderr)
        return info["title"], info["channel"], info["channel_url"], "", f"Transcript error: {e}"

    if not transcript or not transcript.strip():
        return info["title"], info["channel"], info["channel_url"], "", "Empty transcript returned"

    return info["title"], info["channel"], info["channel_url"], transcript, ""
