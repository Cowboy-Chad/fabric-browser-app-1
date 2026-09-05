import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum
from database import Base
import enum


class AnalysisType(str, enum.Enum):
    YOUTUBE_TRANSCRIPT = "youtube_transcript"
    YOUTUBE_COMMENTS = "youtube_comments"
    YOUTUBE_FULL = "youtube_full"
    SPOTIFY = "spotify"
    FILE_TRANSCRIBE = "file_transcribe"
    TWITTER = "twitter"
    REDDIT = "reddit"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    WEB_SCRAPE = "web_scrape"
    DOMAIN_ANALYSIS = "domain_analysis"
    EMAIL_HEADER = "email_header"
    LOG_ANALYSIS = "log_analysis"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(SAEnum(AnalysisType), nullable=False)
    status = Column(SAEnum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    target = Column(String(1024), nullable=True)
    pattern = Column(String(256), nullable=True)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    raw_fabric_command = Column(String(2048), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    metadata_json = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type.value if self.type else None,
            "status": self.status.value if self.status else None,
            "target": self.target,
            "pattern": self.pattern,
            "input_data": self.input_data[:200] + "..." if self.input_data and len(self.input_data) > 200 else self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "raw_fabric_command": self.raw_fabric_command,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at and self.created_at.tzinfo is None else self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at and self.completed_at.tzinfo is None else self.completed_at.isoformat() if self.completed_at else None,
            "metadata_json": self.metadata_json,
        }