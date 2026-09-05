from contextlib import asynccontextmanager
import json, os
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import init_db, get_session
from models import AnalysisResult
from routers import media, social, web
from config import OPENROUTER_MODEL

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return {"default_model": OPENROUTER_MODEL}

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

AVAILABLE_MODELS = [
    "cohere/north-mini-code:free", "dots-studio/dots-3-note-preview:free",
    "google/gemma-4-26b-a4b-it:free", "liquid/lfm-2.5-2.6b:free",
    "minimax/minimax-m2.7:free", "minimax/minimax-m3:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3.5-content-safety:free",
    "nvidia/nemotron-3.5-lightning:free",
    "thinkingmachines/inkling:free", "z-ai/glm-5.2:free",
    "aion-labs/aion-3.0-mini", "aion-labs/aion-3.0",
    "amazon/nova-2-lite-v1", "amazon/nova-micro-v1",
    "anthropic/claude-haiku-4.5",
    "bytedance-seed/seed-1.6", "bytedance-seed/seed-2.0-lite",
    "bytedance-seed/seed-2-1-turbo", "bytedance-seed/seed-2.0-mini",
    "deepseek/deepseek-chat", "deepseek/deepseek-chat-v3.1",
    "deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-r1-0528",
    "google/gemini-2.5-flash-lite", "google/gemini-3.5-flash-lite",
    "mistralai/mistral-medium-3", "mistralai/mistral-medium-3-5",
    "mistralai/mistral-medium-3.1", "mistralai/mistral-nemo",
    "mistralai/mistral-saba", "mistralai/mistral-large",
    "mistralai/mistral-large-2407", "mistralai/mistral-large-2512",
    "moonshotai/kimi-k2", "moonshotai/kimi-k2-0905",
    "kimi-k2-thinking", "moonshotai/kimi-k2.5",
    "moonshotai/kimi-k2.6", "moonshotai/kimi-k2.7-code",
    "moonshotai/kimi-k3",
    "morph/morph-v3-fast", "morph/morph-v3-large",
    "nex-agi/nex-n2-mini", "nex-agi/nex-n2-pro",
    "nousresearch/hermes-4-405b",
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nemotron-3.5-lightning",
    "openai/gpt-3.5-turbo", "openai/gpt-3.5-turbo-instruct",
    "openai/gpt-4-turbo", "openai/gpt-5-nano",
    "qwen/qwen3.7-flash", "qwen/qwen3.8-flash",
    "x-ai/grok-4.20", "x-ai/grok-4.20-multi-agent",
    "x-ai/grok-4.3", "x-ai/grok-4.5", "x-ai/grok-4.6",
    "z-ai/glm-4.7", "z-ai/glm-4.7-flash",
    "z-ai/glm-5", "z-ai/glm-5-turbo",
    "z-ai/glm-5.1", "z-ai/glm-5.2", "z-ai/glm-5.3",
    "z-ai/glm-5.3-flash", "z-ai/glm-5.3-flash:batch",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="OSINT App", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(media.router)
app.include_router(social.router)
app.include_router(web.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/models")
async def list_models():
    return {"models": AVAILABLE_MODELS, "default": load_settings().get("default_model", OPENROUTER_MODEL)}


@app.get("/api/settings/default-model")
async def get_default_model():
    return {"default_model": load_settings().get("default_model", OPENROUTER_MODEL)}


@app.put("/api/settings/default-model")
async def set_default_model(data: dict):
    settings = load_settings()
    settings["default_model"] = data.get("default_model", OPENROUTER_MODEL)
    save_settings(settings)
    return {"default_model": settings["default_model"]}


@app.get("/api/results")
async def list_results(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    stmt = select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).offset(offset).limit(limit)
    results = (await db.execute(stmt)).scalars().all()
    return [r.to_dict() for r in results]


@app.get("/api/results/{result_id}")
async def get_result(result_id: str, db: AsyncSession = Depends(get_session)):
    stmt = select(AnalysisResult).where(AnalysisResult.id == result_id)
    result = (await db.execute(stmt)).scalar_one_or_none()
    if not result:
        return {"error": "not found"}
    return result.to_dict()