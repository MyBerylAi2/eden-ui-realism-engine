"""
EDEN UI REALISM ENGINE - Configuration
=======================================
Centralized configuration management for the EDEN diffusion model fine-tuner.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Dict, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # App Info
    APP_NAME: str = "EDEN UI REALISM ENGINE"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    MODELS_DIR: str = os.path.join(BASE_DIR, "..", "models")
    OUTPUTS_DIR: str = os.path.join(BASE_DIR, "..", "outputs")
    UPLOADS_DIR: str = os.path.join(BASE_DIR, "..", "uploads")
    COMFY_WORKFLOWS_DIR: str = os.path.join(BASE_DIR, "..", "comfy-workflows")
    
    # Hugging Face
    HF_TOKEN: Optional[str] = None
    HF_CACHE_DIR: str = os.path.expanduser("~/.cache/huggingface")
    
    # AI/LLM APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./eden_ui.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # GPU Settings
    CUDA_VISIBLE_DEVICES: str = "0"
    MIXED_PRECISION: str = "fp16"  # fp16, bf16, fp32
    
    # ComfyUI
    COMFYUI_PATH: Optional[str] = None
    COMFYUI_PORT: int = 8188
    
    # Security
    SECRET_KEY: str = "eden-ui-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# EDEN Negative Keywords - Comprehensive list for maximum human realness
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
    "contact_interaction": [
        "fused bodies", "merged limbs", "extra hands during contact",
        "phantom fingers", "body clipping through body", "overlapping torsos",
        "impossible joint angle", "missing contact shadows between bodies",
        "floating body parts during contact", "skin merging at contact points",
        "plastic skin contact", "no skin compression",
        "missing skin flush at pressure points", "no blood rush to skin",
        "uniform skin color during contact", "no warmth variation on skin",
        "missing goosebumps", "missing sweat", "dry skin during exertion"
    ],
    "movement_physics": [
        "rigid body movement", "robotic motion", "stiff hips", "locked joints",
        "weightless body", "no gravity on body", "no muscle tension",
        "no breathing movement", "static chest", "frozen torso",
        "no weight transfer between bodies", "puppet-like movement",
        "no muscle ripple", "no skin stretch during movement",
        "no natural jiggle physics", "weightless motion", "no inertia",
        "jerky transitions", "constant velocity", "locked gaze",
        "no micro-movements", "missing micro-expressions",
        "no subtle facial twitches", "no natural eye saccades",
        "no tear film/gloss variation", "no saliva sheen on lips/teeth"
    ],
    "lighting_rendering": [
        "flat lighting", "harsh CGI shadows", "volumetric god rays artifact",
        "lens flare fake", "bloom overkill", "halo glow", "rim lighting unnatural",
        "deepfake seams", "neural texture artifacts", "diffusion noise remnants",
        "latent grid patterns", "quantization banding", "compression macroblocks",
        "banding", "posterization", "color stepping", "halo around edges",
        "edge sharpening artifact", "aliasing", "moiré patterns",
        "floating in scene", "no interaction shadows", "no contact occlusion",
        "mismatched depth of field", "bokeh fake", "chromatic aberration missing",
        "desaturated skin tones", "hyper-saturated lips/cheeks", "uniform hue",
        "color bleeding", "halo fringing", "chromatic noise"
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
    """
    Get EDEN negative prompt for specified category.
    
    Args:
        category: Category of negative keywords ("all", "base", "skin_quality", etc.)
        custom_additions: Additional negative keywords to include
    
    Returns:
        Comma-separated negative prompt string
    """
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


# EDEN Model Presets
EDEN_MODEL_PRESETS = {
    "kling_reference": {
        "name": "Kling-style Realism",
        "description": "Optimized settings to mimic Kling's human realness",
        "guidance_scale": 5.0,
        "num_inference_steps": 30,
        "negative_prompt_category": "all",
        "scheduler": "DPM++ 2M Karras",
        "sampler": "dpmpp_2m",
        "cfg_rescale": 0.7,
    },
    "photorealistic": {
        "name": "Photorealistic",
        "description": "Maximum photorealism for still images",
        "guidance_scale": 7.5,
        "num_inference_steps": 50,
        "negative_prompt_category": "all",
        "scheduler": "Euler a",
        "sampler": "euler_ancestral",
        "high_res_fix": True,
    },
    "cinematic_video": {
        "name": "Cinematic Video",
        "description": "Cinematic quality video generation",
        "guidance_scale": 6.0,
        "num_inference_steps": 40,
        "negative_prompt_category": "all",
        "scheduler": "DDIM",
        "fps": 24,
        "motion_bucket_id": 127,
    },
    "fast_preview": {
        "name": "Fast Preview",
        "description": "Quick preview generation for iteration",
        "guidance_scale": 5.0,
        "num_inference_steps": 20,
        "negative_prompt_category": "base",
        "scheduler": "Euler",
        "sampler": "euler",
    }
}


# EDEN Enhancement Modules
EDEN_ENHANCEMENTS = {
    "face_detailer": {
        "name": "Face Detailer",
        "description": "Enhanced face detail restoration",
        "models": ["codeformer", "gfpgan", "restoreformer"],
    },
    "skin_texture": {
        "name": "Skin Texture",
        "description": "Realistic skin pore and texture synthesis",
        "models": ["skin_texture_gan"],
    },
    "lighting_enhancer": {
        "name": "Lighting Enhancer",
        "description": "Natural lighting and shadow correction",
        "models": ["hdr_enhancer"],
    },
    "motion_smoothing": {
        "name": "Motion Smoothing",
        "description": "Temporal consistency for video",
        "models": ["rife", "film"],
    },
    "upscaler": {
        "name": "EDEN Upscaler",
        "description": "Intelligent upscaling with detail preservation",
        "models": ["esrgan", "real-esrgan", "swinir"],
        "scales": [2, 4]
    }
}
