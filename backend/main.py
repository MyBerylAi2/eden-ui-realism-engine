"""
EDEN UI REALISM ENGINE - FastAPI Backend
========================================
Main FastAPI application with FLUX, GPU scaling, and Seagate integration.
"""
import os
import uuid
import asyncio
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from config import (
    get_settings, get_eden_negative_prompt, EDEN_MODEL_PRESETS,
    IMAGE_MODELS, IMAGE_RESOLUTIONS, ENHANCE_MODELS
)
from database import init_db, get_db, Generation, HFModel, ChatMessage
from model_manager import model_manager
from generation_engine import generation_engine
from chat_engine import chat_engine
from flux_engine import (
    generate_image_fast, enhance_image_realism, generate_3d_trellis,
    scan_seagate_model_library, pull_huggingface_model,
    pull_ollama_model, pull_pinokio_app, OUTPUT_DIR
)
from hf_gpu_manager import gpu_manager

settings = get_settings()

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")
app.mount("/outputs", StaticFiles(directory=settings.OUTPUTS_DIR), name="outputs")


# ============== Pydantic Models ==============

class GenerateImageRequest(BaseModel):
    prompt: str
    model_name: str = "flux-schnell"
    resolution: str = "1024 x 1024 (Square - FLUX Native)"
    steps: int = 4
    guidance: float = 3.5
    seed: int = -1
    negative_prompt: Optional[str] = None


class EnhanceImageRequest(BaseModel):
    image_path: str
    enhance_model: str = "flux-refine"
    strength: float = 0.25


class Generate3DRequest(BaseModel):
    image_path: str


class GPUUpgradeRequest(BaseModel):
    space_id: str
    gpu_tier: str
    sleep_after_minutes: Optional[int] = 10


class GPUSleepExtendRequest(BaseModel):
    space_id: str
    additional_minutes: int = 10


class PullModelRequest(BaseModel):
    model_id: str
    category: str = "checkpoints"


class PullOllamaRequest(BaseModel):
    model_name: str


class PullPinokioRequest(BaseModel):
    git_url: str


# ============== API Endpoints ==============

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "seagate_connected": os.path.exists(settings.SEAGATE_BASE),
        "status": "running"
    }


# ----- FLUX Image Generation -----

@app.get("/api/flux/models")
async def get_flux_models():
    """Get available FLUX models."""
    return {"models": IMAGE_MODELS}


@app.get("/api/flux/resolutions")
async def get_image_resolutions():
    """Get available image resolutions."""
    return {"resolutions": IMAGE_RESOLUTIONS}


@app.get("/api/flux/enhance-models")
async def get_enhance_models():
    """Get available enhancement models."""
    return {"models": ENHANCE_MODELS}


@app.post("/api/flux/generate")
async def flux_generate(request: GenerateImageRequest):
    """Generate image using FLUX via HF Spaces."""
    image_path, status = generate_image_fast(
        prompt=request.prompt,
        model_name=request.model_name,
        resolution=request.resolution,
        steps=request.steps,
        guidance=request.guidance,
        seed=request.seed,
        negative_prompt=request.negative_prompt or "",
        hf_token=settings.HF_TOKEN
    )
    
    if not image_path:
        raise HTTPException(status_code=500, detail=status)
    
    return {
        "success": True,
        "image_path": image_path,
        "status": status,
        "url": f"/outputs/{Path(image_path).name}"
    }


@app.post("/api/flux/enhance")
async def flux_enhance(request: EnhanceImageRequest):
    """Enhance an image using post-processing."""
    image_path, status = enhance_image_realism(
        image_path=request.image_path,
        enhance_model=request.enhance_model,
        strength=request.strength,
        hf_token=settings.HF_TOKEN
    )
    
    return {
        "success": bool(image_path),
        "image_path": image_path,
        "status": status,
        "url": f"/outputs/{Path(image_path).name}" if image_path else None
    }


@app.post("/api/flux/3d")
async def flux_3d(request: Generate3DRequest):
    """Convert 2D image to 3D mesh using TRELLIS."""
    glb_path, status = generate_3d_trellis(
        image_path=request.image_path,
        hf_token=settings.HF_TOKEN
    )
    
    return {
        "success": bool(glb_path),
        "glb_path": glb_path,
        "status": status,
        "url": f"/outputs/{Path(glb_path).name}" if glb_path else None
    }


# ----- HF GPU Scaling -----

@app.get("/api/gpu/pricing")
async def get_gpu_pricing():
    """Get current HF GPU pricing."""
    return {"pricing": gpu_manager.get_gpu_pricing()}


@app.post("/api/gpu/estimate")
async def estimate_gpu_cost(gpu_tier: str, estimated_minutes: int = 10):
    """Calculate estimated GPU cost."""
    return gpu_manager.calculate_cost_estimate(gpu_tier, estimated_minutes)


@app.post("/api/gpu/upgrade")
async def upgrade_gpu(request: GPUUpgradeRequest):
    """Upgrade HF Space to specific GPU tier."""
    result = gpu_manager.upgrade_space_gpu(
        space_id=request.space_id,
        gpu_tier=request.gpu_tier,
        sleep_after_minutes=request.sleep_after_minutes,
        hf_token=settings.HF_TOKEN
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@app.post("/api/gpu/downgrade")
async def downgrade_gpu(space_id: str):
    """Downgrade space to Zero GPU."""
    result = gpu_manager.downgrade_to_zero(
        space_id=space_id,
        hf_token=settings.HF_TOKEN
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@app.post("/api/gpu/extend")
async def extend_gpu_sleep(request: GPUSleepExtendRequest):
    """Extend auto-sleep timer."""
    result = gpu_manager.extend_sleep_timer(
        space_id=request.space_id,
        additional_minutes=request.additional_minutes
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@app.get("/api/gpu/status/{space_id:path}")
async def get_space_gpu_status(space_id: str):
    """Get current GPU status of a space."""
    return gpu_manager.get_space_status(space_id, settings.HF_TOKEN)


@app.get("/api/gpu/active-upgrades")
async def get_active_upgrades():
    """Get list of currently upgraded spaces."""
    return {"upgrades": gpu_manager.get_active_upgrades()}


# ----- Seagate Model Management -----

@app.get("/api/seagate/scan")
async def scan_seagate():
    """Scan Seagate drive for models."""
    models = scan_seagate_model_library()
    return {"models": models, "count": len(models)}


@app.post("/api/seagate/pull/huggingface")
async def pull_hf_model(request: PullModelRequest):
    """Pull model from HuggingFace."""
    result = pull_huggingface_model(
        model_id=request.model_id,
        category=request.category,
        hf_token=settings.HF_TOKEN
    )
    return {"result": result}


@app.post("/api/seagate/pull/ollama")
async def pull_ollama(request: PullOllamaRequest):
    """Pull model using Ollama."""
    result = pull_ollama_model(request.model_name)
    return {"result": result}


@app.post("/api/seagate/pull/pinokio")
async def pull_pinokio(request: PullPinokioRequest):
    """Clone Pinokio app from git."""
    result = pull_pinokio_app(request.git_url)
    return {"result": result}


# ----- Legacy Endpoints (keep for compatibility) -----

@app.post("/api/generate/image")
async def generate_image_legacy(prompt: str, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"):
    """Legacy SD image generation."""
    result = generation_engine.generate_image(
        prompt=prompt,
        model_id=model_id,
        use_eden_negative=True
    )
    return result


@app.get("/api/models/search")
async def search_models(query: str = "", model_type: str = "text-to-image", limit: int = 50):
    results = model_manager.search_models(query, model_type, limit)
    return {"models": results}


@app.post("/api/chat")
async def chat(message: str, session_id: Optional[str] = None):
    if not session_id:
        session_id = str(uuid.uuid4())
    result = await chat_engine.chat(message, session_id)
    return result


@app.get("/api/eden/negative-keywords")
async def get_negative_keywords(category: str = "all"):
    keywords = get_eden_negative_prompt(category)
    return {"keywords": keywords}


@app.get("/api/system/status")
async def system_status():
    import torch
    
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "available": True,
            "name": torch.cuda.get_device_name(0),
            "memory_total": torch.cuda.get_device_properties(0).total_memory,
        }
    else:
        gpu_info = {"available": False}
    
    return {
        "gpu": gpu_info,
        "seagate": {
            "connected": os.path.exists(settings.SEAGATE_BASE),
            "path": settings.SEAGATE_BASE,
            "hf_cache": settings.HF_HOME,
        },
        "loaded_models": list(model_manager.loaded_models.keys())
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
