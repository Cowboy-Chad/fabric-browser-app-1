from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_session, async_session
from schemas import YouTubeRequest, SpotifyRequest, RumbleRequest
from models import AnalysisType, RumbleTranscript, YouTubeTranscript
from services.task_manager import run_analysis_task
import os, shutil, uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/media", tags=["Media Analysis"])


@router.post("/youtube")
async def analyze_youtube(
    req: YouTubeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    target = req.url
    model_to_use = getattr(req, 'model', None)
    if req.include_transcript and req.include_comments:
        result = await run_analysis_task(
            db, AnalysisType.YOUTUBE_FULL, target, req.pattern,
            youtube_url=target,
            additional_args=["--comments"] if req.include_comments else None,
            model=model_to_use,
        )
    elif req.include_comments:
        result = await run_analysis_task(
            db, AnalysisType.YOUTUBE_COMMENTS, target, req.pattern,
            youtube_url=target, additional_args=["--comments"],
            model=model_to_use,
        )
    else:
        result = await run_analysis_task(
            db, AnalysisType.YOUTUBE_TRANSCRIPT, target, req.pattern,
            youtube_url=target,
            model=model_to_use,
        )
    return {"result_id": result.id, "status": result.status.value}


@router.get("/youtube/history")
async def list_youtube_history(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
):
    stmt = select(YouTubeTranscript).order_by(YouTubeTranscript.created_at.desc()).limit(limit)
    records = (await db.execute(stmt)).scalars().all()
    return [r.to_dict() for r in records]


@router.get("/youtube/history/{video_id}")
async def get_youtube_history_item(video_id: str, db: AsyncSession = Depends(get_session)):
    from services.youtube_client import get_youtube_history_transcript
    record = await get_youtube_history_transcript(db, video_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No YouTube transcript found for video_id {video_id}")
    return record.to_dict()


@router.post("/spotify")
async def analyze_spotify(
    req: SpotifyRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.SPOTIFY, req.url, req.pattern, spotify_url=req.url,
        model=getattr(req, 'model', None),
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/rumble")
async def analyze_rumble(
    req: RumbleRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.RUMBLE, req.url, req.pattern,
        rumble_url=req.url,
        model=getattr(req, 'model', None),
    )
    return {"result_id": result.id, "status": result.status.value}


@router.get("/rumble/history")
async def list_rumble_history(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
):
    stmt = select(RumbleTranscript).order_by(RumbleTranscript.created_at.desc()).limit(limit)
    records = (await db.execute(stmt)).scalars().all()
    return [r.to_dict() for r in records]


@router.get("/rumble/history/{video_id}")
async def get_rumble_history_item(video_id: str, db: AsyncSession = Depends(get_session)):
    from services.rumble_client import get_rumble_history_transcript
    record = await get_rumble_history_transcript(db, video_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No Rumble transcript found for video_id {video_id}")
    return record.to_dict()


@router.post("/transcribe")
async def transcribe_file(
    file: UploadFile = File(...),
    pattern: str = Form("summarize"),
    model: str = Form(""),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_session),
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = await run_analysis_task(
        db, AnalysisType.FILE_TRANSCRIBE, file.filename, pattern,
        additional_args=["--transcribe-file", file_path],
        model=model or None,
    )
    return {"result_id": result.id, "status": result.status.value}