from pydantic import BaseModel
from typing import Optional


class YouTubeRequest(BaseModel):
    url: str
    include_comments: bool = False
    include_transcript: bool = True
    pattern: Optional[str] = "youtube_summary"
    model: Optional[str] = None


class SpotifyRequest(BaseModel):
    url: str
    pattern: Optional[str] = "summarize"
    model: Optional[str] = None


class ScrapeRequest(BaseModel):
    url: str
    pattern: Optional[str] = "summarize"
    model: Optional[str] = None


class DomainRequest(BaseModel):
    domain: str
    pattern: Optional[str] = "extract_domains"
    model: Optional[str] = None


class EmailHeaderRequest(BaseModel):
    headers: str
    pattern: Optional[str] = "analyze_email_headers"
    model: Optional[str] = None


class LogRequest(BaseModel):
    logs: str
    pattern: Optional[str] = "analyze_logs"
    model: Optional[str] = None