"""
EDEN UI REALISM ENGINE - FastAPI Backend
========================================
Main FastAPI application with all endpoints for the EDEN diffusion model fine-tuner.
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

from config import get_settings, get_eden_negative_prompt, EDEN_MODEL_PRESETS, EDEN_NEGATIVE_KEYWORDS
from database import init_db, get_db, Generation, HFModel, ChatMessage
from model_manager import model_manager
from generation_engine import generation_engine
from chat_engine import chat_engine

settings = get_settings()

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
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

# Static files for uploads and outputs
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")
app.mount("/outputs", StaticFiles(directory=settings.OUTPUTS_DIR), name="outputs")


# ============== Pydantic Models ==============

class GenerateImageRequest(BaseModel):
    prompt: str
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    scheduler: str = "DPM++ 2M Karras"
    use_eden_negative: bool = True
    preset: Optional[str] = None


class GenerateVideoRequest(BaseModel):
    prompt: str
    model_id: str = "Wan-AI/Wan2.1-T2V-1.3B"
    negative_prompt: Optional[str] = None
    width: int = 832
    height: int = 480
    num_frames: int = 16
    fps: float = 8
    num_inference_steps: int = 25
    guidance_scale: float = 6.0
    seed: Optional[int] = None
    scheduler: str = "DDIM"
    use_eden_negative: bool = True
    preset: str = "cinematic_video"


class ImageToVideoRequest(BaseModel):
    image_path: str
    prompt: str
    model_id: str = "stabilityai/stable-video-diffusion-img2vid-xt"
    num_frames: int = 25
    fps: float = 6
    motion_bucket_id: int = 127
    seed: Optional[int] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    attachments: Optional[List[dict]] = None


class ModelSearchRequest(BaseModel):
    query: str = ""
    model_type: str = "text-to-image"
    limit: int = 50


class DownloadModelRequest(BaseModel):
    model_id: str


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


# ----- Model Management -----

@app.get("/api/models/search")
async def search_models(query: str = "", model_type: str = "text-to-image", limit: int = 50):
    """Search for models on HuggingFace Hub."""
    results = model_manager.search_models(query, model_type, limit)
    return {"models": results}


@app.get("/api/models/info/{model_id:path}")
async def get_model_info(model_id: str):
    """Get detailed information about a model."""
    info = model_manager.get_model_info(model_id)
    if not info:
        raise HTTPException(status_code=404, detail="Model not found")
    return info


@app.post("/api/models/download")
async def download_model(request: DownloadModelRequest, background_tasks: BackgroundTasks):
    """Download a model from HuggingFace."""
    try:
        path = model_manager.download_model(request.model_id)
        return {"status": "downloaded", "path": path, "model_id": request.model_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/downloaded")
async def list_downloaded_models():
    """List all locally downloaded models."""
    models = model_manager.list_downloaded_models()
    return {"models": models}


@app.get("/api/models/recommended")
async def get_recommended_models():
    """Get EDEN's recommended models."""
    return {"models": model_manager.get_recommended_models()}


# ----- Generation -----

@app.post("/api/generate/image")
async def generate_image(request: GenerateImageRequest):
    """Generate an image with EDEN optimizations."""
    result = generation_engine.generate_image(
        prompt=request.prompt,
        model_id=request.model_id,
        negative_prompt=request.negative_prompt,
        width=request.width,
        height=request.height,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=request.guidance_scale,
        seed=request.seed,
        scheduler=request.scheduler,
        use_eden_negative=request.use_eden_negative,
        preset=request.preset
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))
    
    return result


@app.post("/api/generate/video")
async def generate_video(request: GenerateVideoRequest):
    """Generate a video with EDEN optimizations."""
    result = generation_engine.generate_video(
        prompt=request.prompt,
        model_id=request.model_id,
        negative_prompt=request.negative_prompt,
        width=request.width,
        height=request.height,
        num_frames=request.num_frames,
        fps=request.fps,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=request.guidance_scale,
        seed=request.seed,
        scheduler=request.scheduler,
        use_eden_negative=request.use_eden_negative,
        preset=request.preset
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))
    
    return result


@app.post("/api/generate/image-to-video")
async def image_to_video(request: ImageToVideoRequest):
    """Convert an image to video."""
    result = generation_engine.image_to_video(
        image_path=request.image_path,
        prompt=request.prompt,
        model_id=request.model_id,
        num_frames=request.num_frames,
        fps=request.fps,
        motion_bucket_id=request.motion_bucket_id,
        seed=request.seed
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))
    
    return result


# ----- File Upload -----

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file (image or video)."""
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(settings.UPLOADS_DIR, f"{file_id}{file_ext}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "path": file_path,
        "url": f"/uploads/{file_id}{file_ext}"
    }


# ----- Chat -----

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Natural language chat with EDEN AI."""
    if not request.session_id:
        request.session_id = str(uuid.uuid4())
    
    result = await chat_engine.chat(
        message=request.message,
        session_id=request.session_id,
        attachments=request.attachments
    )
    
    return result


@app.websocket("/api/chat/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for real-time chat."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            attachments = data.get("attachments", [])
            
            result = await chat_engine.chat(
                message=message,
                session_id=session_id,
                attachments=attachments
            )
            
            await websocket.send_json(result)
    except Exception as e:
        await websocket.close()


# ----- EDEN Configuration -----

@app.get("/api/eden/negative-keywords")
async def get_negative_keywords(category: str = "all"):
    """Get EDEN's negative keywords."""
    keywords = get_eden_negative_prompt(category)
    return {"keywords": keywords, "category": category}


@app.get("/api/eden/negative-categories")
async def get_negative_categories():
    """Get all negative keyword categories."""
    return {"categories": list(EDEN_NEGATIVE_KEYWORDS.keys())}


@app.get("/api/eden/presets")
async def get_presets():
    """Get EDEN model presets."""
    return {"presets": EDEN_MODEL_PRESETS}


@app.get("/api/eden/presets/{preset_name}")
async def get_preset(preset_name: str):
    """Get a specific preset."""
    if preset_name not in EDEN_MODEL_PRESETS:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"preset": EDEN_MODEL_PRESETS[preset_name]}


@app.get("/api/eden/enhancements")
async def get_enhancements():
    """Get available enhancement modules."""
    from config import EDEN_ENHANCEMENTS
    return {"enhancements": EDEN_ENHANCEMENTS}


# ----- System Status -----

@app.get("/api/system/status")
async def system_status():
    """Get system status and GPU info."""
    import torch
    
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "available": True,
            "name": torch.cuda.get_device_name(0),
            "memory_total": torch.cuda.get_device_properties(0).total_memory,
            "memory_allocated": torch.cuda.memory_allocated(0),
            "memory_cached": torch.cuda.memory_reserved(0)
        }
    else:
        gpu_info = {"available": False}
    
    return {
        "gpu": gpu_info,
        "pytorch_version": torch.__version__,
        "loaded_models": list(model_manager.loaded_models.keys())
    }


@app.post("/api/system/unload-model")
async def unload_model(model_id: Optional[str] = None):
    """Unload a model to free VRAM."""
    model_manager.unload_model(model_id)
    return {"status": "unloaded"}


# ----- ComfyUI Integration -----

@app.get("/api/comfyui/status")
async def comfyui_status():
    """Check ComfyUI server status."""
    # Placeholder - would check if ComfyUI server is running
    return {"connected": False, "url": f"http://localhost:{settings.COMFYUI_PORT}"}


@app.post("/api/comfyui/execute")
async def execute_comfyui_workflow(workflow: dict):
    """Execute a ComfyUI workflow."""
    # Placeholder - would send workflow to ComfyUI API
    return {"status": "not_implemented"}


# ============== Main Entry Point ==============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
