from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from schemas import ScrapeRequest, DomainRequest, EmailHeaderRequest, LogRequest
from models import AnalysisType
from services.task_manager import run_analysis_task

router = APIRouter(prefix="/api/web", tags=["Web & Domain Analysis"])


@router.post("/scrape")
async def scrape_and_analyze(
    req: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.WEB_SCRAPE, req.url, req.pattern, scrape_url=req.url,
        model=getattr(req, 'model', None),
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/domain")
async def analyze_domain(
    req: DomainRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.DOMAIN_ANALYSIS, req.domain, req.pattern, input_data=req.domain,
        model=getattr(req, 'model', None),
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/email-headers")
async def analyze_email_headers(
    req: EmailHeaderRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.EMAIL_HEADER, "email_headers", req.pattern, input_data=req.headers,
        model=getattr(req, 'model', None),
    )
    return {"result_id": result.id, "status": result.status.value}


@router.post("/logs")
async def analyze_logs(
    req: LogRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    result = await run_analysis_task(
        db, AnalysisType.LOG_ANALYSIS, "logs", req.pattern, input_data=req.logs,
        model=getattr(req, 'model', None),
    )
    return {"result_id": result.id, "status": result.status.value}