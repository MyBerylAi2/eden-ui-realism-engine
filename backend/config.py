"""
EDEN UI REALISM ENGINE - Configuration with Seagate Storage
============================================================
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Dict, Any, Optional
from pathlib import Path
import os

# =============================================================================
# SEAGATE STORAGE SETUP - Redirect ALL model downloads to external drive
# =============================================================================
# Try Seagate first, fall back to local storage if not available
SEAGATE_PATH = "/media/letsgo/Seagate Backup Plus Drive/PINOKIO"
LOCAL_PATH = Path.home() / ".eden-ui"

# Check if Seagate is available
try:
    SEAGATE = Path(SEAGATE_PATH)
    if not SEAGATE.exists():
        SEAGATE = LOCAL_PATH
        USING_SEAGATE = False
    else:
        USING_SEAGATE = True
except:
    SEAGATE = LOCAL_PATH
    USING_SEAGATE = False

# Set up cache directories
HF_HOME = SEAGATE / "cache" / "HF_HOME"
TORCH_HOME = SEAGATE / "cache" / "TORCH_HOME"

# Create directories (with fallback)
try:
    HF_HOME.mkdir(parents=True, exist_ok=True)
    TORCH_HOME.mkdir(parents=True, exist_ok=True)
    (SEAGATE / "drive" / "checkpoints").mkdir(parents=True, exist_ok=True)
    (SEAGATE / "drive" / "loras").mkdir(parents=True, exist_ok=True)
    (SEAGATE / "drive" / "vae").mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fall back to local if no permission
    SEAGATE = LOCAL_PATH
    HF_HOME = SEAGATE / "cache" / "HF_HOME"
    TORCH_HOME = SEAGATE / "cache" / "TORCH_HOME"
    HF_HOME.mkdir(parents=True, exist_ok=True)
    TORCH_HOME.mkdir(parents=True, exist_ok=True)

# Set environment variables BEFORE any ML imports
os.environ["HF_HOME"] = str(HF_HOME)
os.environ["HUGGINGFACE_HUB_CACHE"] = str(HF_HOME)
os.environ["TORCH_HOME"] = str(TORCH_HOME)
os.environ["TRANSFORMERS_CACHE"] = str(HF_HOME)


class Settings(BaseSettings):
    """Application settings."""
    
    # App Info
    APP_NAME: str = "EDEN UI REALISM ENGINE"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Seagate Paths
    SEAGATE_BASE: str = str(SEAGATE)
    USING_SEAGATE: bool = USING_SEAGATE
    HF_HOME: str = str(HF_HOME)
    TORCH_HOME: str = str(TORCH_HOME)
    DRIVE_DIR: str = str(SEAGATE / "drive")
    MODELS_DIR: str = str(SEAGATE / "models")
    OUTPUTS_DIR: str = str(SEAGATE / "outputs")
    UPLOADS_DIR: str = str(SEAGATE / "uploads")
    COMFY_WORKFLOWS_DIR: str = str(SEAGATE / "comfy-workflows")
    
    # API Keys
    HF_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = f"sqlite:///{SEAGATE}/eden_ui.db"
    
    # GPU
    CUDA_VISIBLE_DEVICES: str = "0"
    MIXED_PRECISION: str = "fp16"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# =============================================================================
# IMAGE MODELS REGISTRY - FLUX Family
# =============================================================================
IMAGE_MODELS: Dict[str, Dict[str, Any]] = {
    "flux-schnell": {
        "name": "FLUX.1-schnell",
        "space": "black-forest-labs/FLUX.1-schnell",
        "steps": 4,
        "guidance": 3.5,
        "desc": "Fastest - 1-4 steps, Apache 2.0, daily driver",
        "type": "flux",
        "fast": True,
    },
    "flux-klein": {
        "name": "FLUX.2-klein-4B",
        "space": "black-forest-labs/FLUX.2-klein-4B", 
        "steps": 4,
        "guidance": 3.5,
        "desc": "New 2026 - 4B params, sub-second generation",
        "type": "flux",
        "fast": True,
    },
    "flux-dev": {
        "name": "FLUX.1-dev",
        "space": "black-forest-labs/FLUX.1-dev",
        "steps": 28,
        "guidance": 3.5,
        "desc": "Quality king - 12B params, 30-60s, final renders",
        "type": "flux",
        "fast": False,
    },
}

# =============================================================================
# IMAGE RESOLUTIONS - FLUX Native + Common Aspect Ratios
# =============================================================================
IMAGE_RESOLUTIONS: Dict[str, tuple] = {
    "1024 x 1024 (Square - FLUX Native)": (1024, 1024),
    "768 x 1344 (Portrait 9:16 - Phone)": (768, 1344),
    "1344 x 768 (Landscape 16:9 - Wide)": (1344, 768),
    "832 x 1216 (Portrait 2:3 - Photo)": (832, 1216),
    "1216 x 832 (Landscape 3:2 - Photo)": (1216, 832),
    "512 x 512 (Test/Fast)": (512, 512),
}

# =============================================================================
# ENHANCE MODELS - Post-Processing Pipeline
# =============================================================================
ENHANCE_MODELS: Dict[str, Dict[str, Any]] = {
    "none": {
        "name": "None (No Enhancement)",
        "type": "none",
        "space": None,
        "desc": "Use generated image as-is",
    },
    "flux-refine": {
        "name": "FLUX.1-dev Refine (img2img)",
        "type": "img2img",
        "space": "black-forest-labs/FLUX.1-dev",
        "strength": 0.25,
        "desc": "Low-strength re-run for skin/eye details",
    },
    "realesrgan": {
        "name": "RealESRGAN (Upscale 4x)",
        "type": "upscale", 
        "space": "ai-forever/Real-ESRGAN",
        "desc": "Neural 4x upscaler adds texture detail",
    },
    "codeformer": {
        "name": "CodeFormer (Face Fix)",
        "type": "face",
        "space": "sczhou/CodeFormer",
        "desc": "Fixes asymmetric eyes, blurry teeth, skin",
    },
}

# =============================================================================
# VIDEO MODELS - Wan2.1 Family
# =============================================================================
VIDEO_MODELS: Dict[str, Dict[str, Any]] = {
    "wan-t2v-1.3b": {
        "name": "Wan2.1-T2V-1.3B",
        "space": "Wan-AI/Wan2.1-T2V-1.3B",
        "private_space": "AIBRUH/video-studio",
        "desc": "Efficient text-to-video",
    },
    "wan-t2v-14b": {
        "name": "Wan2.1-T2V-14B",
        "space": "Wan-AI/Wan2.1-T2V-14B",
        "desc": "High quality text-to-video",
    },
    "wan-i2v-14b": {
        "name": "Wan2.1-I2V-14B",
        "space": "Wan-AI/Wan2.1-I2V-14B",
        "desc": "Image-to-video animation",
    },
}

# =============================================================================
# EDEN NEGATIVE KEYWORDS (200+ for Maximum Human Realism)
# =============================================================================
EDEN_NEGATIVE_KEYWORDS = {
    "base": [
        "deformed face", "asymmetric eyes", "extra fingers", "mutated hands",
        "blurry eyes", "cartoon", "3D render", "drawing", "sketch", "lowres",
        "low resolution", "bad anatomy", "disfigured", "ugly", "duplicate",
        "malformed hands", "bad proportions", "text", "watermark"
    ],
    "skin_quality": [
        "unnatural skin", "overexposed", "underexposed", "plastic skin",
        "waxy skin", "greasy sheen", "airbrushed skin", "smooth skin filter",
        "beauty filter", "poreless skin", "silicone skin", "rubber skin",
        "over-retouched skin", "dermabrasion effect", "uniform skin tone",
        "flat skin color", "missing pores", "missing skin wrinkles",
        "missing freckles", "missing moles", "painted skin texture",
        "matte skin finish", "skin without subsurface scattering",
        "blurred skin detail", "frequency separation artifact",
        "skin like clay", "skin like fondant", "missing vellus hair",
        "missing peach fuzz", "artificial skin sheen", "photoshop skin",
        "facetune skin", "instagram filter skin", "airbrushed", "perfect skin"
    ],
    "facial_features": [
        "face symmetry", "dead eyes", "glazed eyes", "unfocused eyes",
        "mannequin", "wax figure", "uncanny valley", "CGI", "video game",
        "deepfake artifacts", "perfect symmetry", "idealized features",
        "doll-like", "frozen expression", "stiff body", "blank stare",
        "emotionless face", "frozen smile", "dead expression",
        "performative expression", "fake moan face", "exaggerated expression",
        "disconnected eye contact", "vacant eyes", "robotic facial movement",
        "symmetrical expression", "uniform emotion across face"
    ],
    "body_anatomy": [
        "impossible body proportions", "anime proportions", "exaggerated curves",
        "balloon breasts", "tiny waist", "elongated legs", "uniform body tone",
        "missing body hair", "missing skin imperfections", "no stretch marks",
        "no veins visible", "no moles on body", "painted texture",
        "instagram body", "surgically enhanced look", "perfect body"
    ],
    "video_artifacts": [
        "flickering", "frame jitter", "motion warp", "morphing faces",
        "identity shift", "sudden identity change",
        "inconsistent facial features across frames", "lip sync desync",
        "eye blink artifacts", "temporal flicker", "morphing", "melting",
        "clipping artifacts", "choppy animation", "low framerate feel",
        "stutter", "ghosting", "trailing artifacts", "frame duplication",
        "interpolation errors"
    ],
    "style_filters": [
        "beauty mode", "glamour shot", "high-key lighting overkill",
        "soft focus filter", "skin smoothing algorithm", "neural denoising artifacts",
        "generated image", "AI generated", "synthetic human", "computer graphics",
        "rendered", "octane render style", "unreal engine look", "game asset",
        "digital painting", "anime", "anime style", "manga", "cartoon style",
        "glossy lips", "lip filler", "overfilled lips", "makeup-heavy",
        "full makeup", "glowing skin", "shiny face", "filtered", "beautified",
        "beauty shot", "porcelain", "retouched", "photoshopped",
        "heavy contour", "dramatic makeup", "stage makeup", "makeup lines",
        "makeup streaks", "lip gloss", "waxy", "matte overkill",
        "studio beauty lighting", "wonky eyes", "stick man", "stick woman",
        "stick people"
    ]
}


def get_eden_negative_prompt(category: str = "all", custom_additions: List[str] = None) -> str:
    """Get EDEN negative prompt for specified category."""
    keywords = []
    
    if category == "all":
        for cat_keywords in EDEN_NEGATIVE_KEYWORDS.values():
            keywords.extend(cat_keywords)
    elif category in EDEN_NEGATIVE_KEYWORDS:
        keywords.extend(EDEN_NEGATIVE_KEYWORDS[category])
    
    if custom_additions:
        keywords.extend(custom_additions)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = [k for k in keywords if not (k in seen or seen.add(k))]
    
    return ", ".join(unique_keywords)


# FLUX-style negative injection (appended to prompt)
def inject_flux_negative(prompt: str, negative: str) -> str:
    """FLUX doesn't have separate negative_prompt param, so we append it."""
    if not negative:
        return prompt
    return f"{prompt}. Avoid: {negative}"


# Model presets
EDEN_MODEL_PRESETS = {
    "kling_reference": {
        "name": "Kling-style Realism",
        "description": "Optimized settings to mimic Kling's human realness",
        "guidance_scale": 5.0,
        "num_inference_steps": 30,
        "negative_prompt_category": "all",
        "scheduler": "DPM++ 2M Karras",
    },
    "photorealistic": {
        "name": "Photorealistic",
        "description": "Maximum photorealism for still images",
        "guidance_scale": 7.5,
        "num_inference_steps": 50,
        "negative_prompt_category": "all",
    },
    "cinematic_video": {
        "name": "Cinematic Video",
        "description": "Cinematic quality video generation",
        "guidance_scale": 6.0,
        "num_inference_steps": 40,
        "negative_prompt_category": "all",
        "fps": 24,
    },
    "fast_preview": {
        "name": "Fast Preview",
        "description": "Quick preview generation for iteration",
        "guidance_scale": 5.0,
        "num_inference_steps": 20,
        "negative_prompt_category": "base",
    }
}
