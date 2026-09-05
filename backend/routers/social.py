from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import AnalysisType
from services.task_manager import run_analysis_task

router = APIRouter(prefix="/api/social", tags=["Social Media Analysis"])


@router.post("/twitter")
async def analyze_twitter(
    target: str = Query(...),
    pattern: str = Query("summarize"),
    model: str = Query(""),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.TWITTER, target, pattern, input_data=target,
        model=model or None,
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/reddit")
async def analyze_reddit(
    target: str = Query(...),
    pattern: str = Query("analyze_comments"),
    model: str = Query(""),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.REDDIT, target, pattern, input_data=target,
        model=model or None,
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/tiktok")
async def analyze_tiktok(
    target: str = Query(...),
    pattern: str = Query("summarize"),
    model: str = Query(""),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.TIKTOK, target, pattern, input_data=target,
        model=model or None,
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/instagram")
async def analyze_instagram(
    target: str = Query(...),
    pattern: str = Query("analyze_personality"),
    model: str = Query(""),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.INSTAGRAM, target, pattern, input_data=target,
        model=model or None,
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/linkedin")
async def analyze_linkedin(
    target: str = Query(...),
    pattern: str = Query("analyze_personality"),
    model: str = Query(""),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.LINKEDIN, target, pattern, input_data=target,
        model=model or None,
    )
    return {"result_id": result.id, "status": result.status.value}