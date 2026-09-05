from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from schemas import YouTubeRequest, SpotifyRequest
from models import AnalysisType
from services.task_manager import run_analysis_task
import os, shutil

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