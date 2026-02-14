"""
EDEN UI REALISM ENGINE - FastAPI Backend
========================================
Main FastAPI application with FLUX, GPU scaling, and Seagate integration.
"""
import os
import uuid
import asyncio
import time
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from PIL import Image, ImageDraw, ImageFont

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
    generate_video_local, scan_seagate_model_library, pull_huggingface_model,
    pull_ollama_model, pull_pinokio_app, OUTPUT_DIR
)
from hf_gpu_manager import gpu_manager
from agentgen_integration import apply_agentic_enhancement, agent_network, AgentType
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class StrictModeSettings(BaseModel):
    render_exact: bool = True
    no_filter: bool = True
    preserve_all: bool = True

class GenerateImageRequest(BaseModel):
    prompt: str
    model_name: str = "flux-schnell"
    resolution: str = "1024 x 1024 (Square - FLUX Native)"
    steps: int = 4
    guidance: float = 3.5
    temperature: float = 0.5
    seed: int = -1
    negative_prompt: Optional[str] = None
    active_agents: List[str] = []
    reference_images: List[str] = []
    adherence: str = "Normal"
    strict_mode: bool = False
    strict_settings: Optional[StrictModeSettings] = None


class EnhanceImageRequest(BaseModel):
    image_path: str
    enhance_model: str = "flux-refine"
    strength: float = 0.25


class Generate3DRequest(BaseModel):
    image_path: str


class GenerateVideoRequest(BaseModel):
    prompt: str
    model_name: str = "wan-t2v-1.3b"
    width: int = 832
    height: int = 480
    duration: int = 5
    fps: int = 24
    seed: int = -1
    active_agents: List[str] = []


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
async def flux_generate(request: GenerateImageRequest, mock: bool = False):
    """Generate image using FLUX via HF Spaces with Agentic Teams."""
    
    # Apply strict mode enhancements
    enhanced_prompt = request.prompt
    enhanced_steps = request.steps
    enhanced_guidance = request.guidance
    applied_agents = []
    
    # STRICT MODE: Add prompt enforcement
    if request.strict_mode:
        # Increase guidance for strict adherence
        enhanced_guidance = max(request.guidance, 12.0)
        
        # Add strict mode keywords to negative prompt
        strict_negative_additions = [
            "deviation from prompt", "ignoring instructions", "modified composition",
            "altered pose", "changed clothing", "different hairstyle",
            "wrong colors", "incorrect lighting", "creative interpretation"
        ]
        
        logger.info(f"STRICT MODE activated: {request.adherence}")
        logger.info(f"Strict settings: {request.strict_settings}")
    
    # Apply agentic enhancement if agents are active
    if request.active_agents:
        agent_settings = {
            "steps": request.steps,
            "guidance_scale": enhanced_guidance,
            "num_inference_steps": request.steps,
            "temperature": request.temperature
        }
        
        enhanced = apply_agentic_enhancement(
            prompt=enhanced_prompt,
            settings=agent_settings,
            active_agents=request.active_agents
        )
        
        enhanced_prompt = enhanced.get("prompt", enhanced_prompt)
        enhanced_steps = enhanced.get("settings", {}).get("num_inference_steps", enhanced_steps)
        enhanced_guidance = enhanced.get("settings", {}).get("guidance_scale", enhanced_guidance)
        applied_agents = enhanced.get("applied_agents", [])
        
        logger.info(f"Applied agents: {applied_agents}")
        logger.info(f"Enhanced prompt: {enhanced_prompt[:100]}...")
    
    # REAL GENERATION - Check for Pinokio local models first
    try:
        # Check if using Pinokio local model
        if request.model_name.startswith("pinokio-"):
            from pinokio_integration import generate_with_pinokio_model
            from config import settings as app_settings
            
            # Find the model path
            model_path = None
            from config import IMAGE_MODELS
            if request.model_name in IMAGE_MODELS:
                model_path = IMAGE_MODELS[request.model_name].get("path")
            
            if model_path and Path(model_path).exists():
                image_path, status = generate_with_pinokio_model(
                    prompt=enhanced_prompt,
                    model_path=model_path,
                    output_dir=Path(app_settings.OUTPUTS_DIR),
                    steps=enhanced_steps,
                    guidance=enhanced_guidance,
                    seed=request.seed
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail={"error": f"Pinokio model not found: {request.model_name}", "message": "Run scan to refresh models"}
                )
        else:
            # Use HF Spaces
            image_path, status = generate_image_fast(
                prompt=enhanced_prompt,
                model_name=request.model_name,
                resolution=request.resolution,
                steps=enhanced_steps,
                guidance=enhanced_guidance,
                seed=request.seed,
                negative_prompt=request.negative_prompt or "",
                hf_token=settings.HF_TOKEN
            )
        
        if not image_path:
            raise HTTPException(
                status_code=500,
                detail={"error": status, "message": "Image generation failed"}
            )
        
        return {
            "success": True,
            "image_path": image_path,
            "status": status,
            "url": f"/outputs/{Path(image_path).name}",
            "applied_agents": applied_agents,
            "enhanced_prompt": enhanced_prompt if applied_agents else None,
            "strict_mode": request.strict_mode,
            "adherence": request.adherence,
            "guidance": enhanced_guidance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        logger.error(f"Image generation failed: {error_str}")
        
        # Check for HF authentication error
        if "401" in error_str or "Invalid username" in error_str or "authentication" in error_str.lower():
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "HF Authentication Required",
                    "message": "HuggingFace login needed. Select 📦 LOCAL model or check HF token.",
                    "hint": "Use 🔍 Scan Pinokio Folder to find local models that don't require HF auth"
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={"error": error_str, "message": "Generation failed - try again"}
        )


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


@app.post("/api/video/generate")
async def video_generate(request: GenerateVideoRequest):
    """Generate video using Wan2.1 via HF Spaces with Agentic Teams."""
    try:
        # Apply agentic enhancement if agents are active
        enhanced_prompt = request.prompt
        applied_agents = []
        
        if request.active_agents:
            agent_settings = {"cfg_high": 6.5, "cfg_low": 4.0}
            
            enhanced = apply_agentic_enhancement(
                prompt=request.prompt,
                settings=agent_settings,
                active_agents=request.active_agents
            )
            
            enhanced_prompt = enhanced.get("prompt", request.prompt)
            applied_agents = enhanced.get("applied_agents", [])
            
            logger.info(f"Applied agents to video: {applied_agents}")
        
        video_path, status = generate_video_local(
            prompt=enhanced_prompt,
            model_name=request.model_name,
            width=request.width,
            height=request.height,
            num_frames=request.duration * request.fps,
            fps=request.fps,
            seed=request.seed,
            hf_token=settings.HF_TOKEN
        )
        
        if not video_path:
            error_result = agent_network.process_error(status)
            strategy = error_result.get("recovery_strategy", {})
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error": status,
                    "recovery_strategy": strategy,
                    "should_retry": strategy.get("action") != "none"
                }
            )
        
        return {
            "success": True,
            "video_path": video_path,
            "status": status,
            "url": f"/outputs/{Path(video_path).name}",
            "applied_agents": applied_agents,
            "enhanced_prompt": enhanced_prompt if applied_agents else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": "unexpected_error",
                "message": "An unexpected error occurred. Agents are analyzing..."
            }
        )


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


# ----- Ollama Integration -----

class OllamaActivateRequest(BaseModel):
    seagate_path: str = "/media/letsgo/9361ec48-323e-44ae-84d5-9060ae68b5751/PINOKIO/ollama"


@app.post("/api/ollama/activate")
async def activate_ollama(request: OllamaActivateRequest):
    """Activate Ollama from Seagate storage."""
    import subprocess
    import os
    
    try:
        ollama_path = Path(request.seagate_path)
        
        # Check if Ollama binary exists in Seagate
        ollama_bin = ollama_path / "bin" / "ollama"
        if not ollama_bin.exists():
            ollama_bin = ollama_path / "ollama"  # Try root level
        
        if ollama_bin.exists():
            # Start Ollama from Seagate
            env = os.environ.copy()
            env["OLLAMA_MODELS"] = str(ollama_path / "models")
            
            # Check if already running
            result = subprocess.run(
                ["pgrep", "-f", "ollama serve"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Already running, get available models
                models_result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True
                )
                models = []
                if models_result.returncode == 0:
                    lines = models_result.stdout.strip().split('\n')[1:]  # Skip header
                    models = [line.split()[0] for line in lines if line.strip()]
                
                return {
                    "success": True,
                    "message": "Ollama already running from Seagate",
                    "models": models,
                    "path": str(ollama_bin)
                }
            
            # Start Ollama
            subprocess.Popen(
                [str(ollama_bin), "serve"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            return {
                "success": True,
                "message": "Ollama activated from Seagate",
                "models": [],
                "path": str(ollama_bin)
            }
        
        # Fallback to system Ollama
        result = subprocess.run(
            ["which", "ollama"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Check if running
            check = subprocess.run(
                ["pgrep", "-f", "ollama serve"],
                capture_output=True,
                text=True
            )
            
            if check.returncode != 0:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            # Get models
            models_result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            models = []
            if models_result.returncode == 0:
                lines = models_result.stdout.strip().split('\n')[1:]
                models = [line.split()[0] for line in lines if line.strip()]
            
            return {
                "success": True,
                "message": "Using system Ollama (Seagate copy not found)",
                "models": models,
                "path": "system"
            }
        
        return {
            "success": False,
            "error": "Ollama not found on Seagate or system"
        }
        
    except Exception as e:
        logger.error(f"Ollama activation error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


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


@app.get("/api/pinokio/scan")
async def scan_pinokio():
    """Scan Pinokio folders for available models."""
    from pinokio_integration import scan_pinokio_models, get_pinokio_paths
    
    paths = get_pinokio_paths()
    models = scan_pinokio_models()
    
    # Count total models
    total = sum(len(m) for m in models.values())
    
    return {
        "paths": [str(p) for p in paths],
        "models": models,
        "total": total,
        "message": f"Found {total} models in Pinokio folders"
    }


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
