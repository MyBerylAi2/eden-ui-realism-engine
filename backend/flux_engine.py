"""
EDEN UI REALISM ENGINE - FLUX Engine with Seagate Integration
===============================================================
Image generation, enhancement, and 3D conversion via HuggingFace Spaces.
"""
import os
import io
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import time

from config import (
    SEAGATE, HF_HOME, IMAGE_MODELS, IMAGE_RESOLUTIONS, 
    ENHANCE_MODELS, VIDEO_MODELS, get_eden_negative_prompt, inject_flux_negative
)

# Seagate paths
OUTPUT_DIR = SEAGATE / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DRIVE_DIR = SEAGATE / "drive"


def generate_image_fast(
    prompt: str,
    model_name: str = "flux-schnell",
    resolution: str = "1024 x 1024 (Square - FLUX Native)",
    steps: int = 4,
    guidance: float = 3.5,
    seed: int = -1,
    negative_prompt: str = "",
    hf_token: Optional[str] = None
) -> Tuple[str, str]:
    """
    Generate image using FLUX via HuggingFace Spaces.
    
    Returns: (image_path, status_message)
    """
    try:
        from gradio_client import Client, handle_file
        
        model = IMAGE_MODELS.get(model_name, IMAGE_MODELS["flux-schnell"])
        space_id = model["space"]
        
        # Resolve resolution
        width, height = IMAGE_RESOLUTIONS.get(resolution, (1024, 1024))
        
        # FLUX negative injection (appended to prompt)
        if negative_prompt:
            full_prompt = inject_flux_negative(prompt, negative_prompt)
        else:
            full_prompt = prompt
        
        # Connect to HF Space
        client = Client(space_id, hf_token=hf_token)
        
        # Call the inference endpoint
        seed_val = seed if seed >= 0 else int(time.time())
        
        result = client.predict(
            prompt=full_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance,
            seed=seed_val,
            randomize_seed=(seed < 0),
            api_name="/infer"
        )
        
        # Save result locally
        timestamp = int(time.time())
        output_path = OUTPUT_DIR / f"eden_{model_name}_{timestamp}.png"
        
        # Copy from temp to output dir
        if isinstance(result, tuple):
            temp_path = result[0]
        else:
            temp_path = result
            
        shutil.copy(temp_path, output_path)
        
        return str(output_path), f"✅ Generated with {model['name']} in {steps} steps"
        
    except Exception as e:
        return "", f"❌ Error: {str(e)}"


def enhance_image_realism(
    image_path: str,
    enhance_model: str = "flux-refine",
    strength: float = 0.25,
    hf_token: Optional[str] = None
) -> Tuple[str, str]:
    """
    Enhance an image using post-processing models.
    
    Returns: (enhanced_image_path, status_message)
    """
    try:
        from gradio_client import Client, handle_file
        
        if not image_path or not Path(image_path).exists():
            return "", "❌ No image to enhance"
        
        model = ENHANCE_MODELS.get(enhance_model)
        if not model or model["type"] == "none":
            return image_path, "ℹ️ No enhancement selected"
        
        # Handle different enhancement types
        if model["type"] == "img2img":
            # FLUX dev refinement
            client = Client(model["space"], hf_token=hf_token)
            
            realism_prompt = "photorealistic, 8K, detailed skin pores, subsurface scattering, professional photography"
            
            result = client.predict(
                image=handle_file(image_path),
                prompt=realism_prompt,
                strength=strength,
                guidance_scale=3.5,
                num_inference_steps=28,
                api_name="/img2img"
            )
            
        elif model["type"] == "upscale":
            # RealESRGAN
            client = Client(model["space"], hf_token=hf_token)
            result = client.predict(
                image=handle_file(image_path),
                scale=4,
                face_enhance=True,
                api_name="/predict"
            )
            
        elif model["type"] == "face":
            # CodeFormer
            client = Client(model["space"], hf_token=hf_token)
            result = client.predict(
                image=handle_file(image_path),
                codeformer_fidelity=0.7,
                background_enhance=True,
                face_upsample=True,
                api_name="/predict"
            )
        else:
            return image_path, "❌ Unknown enhancement type"
        
        # Save enhanced image
        timestamp = int(time.time())
        output_path = OUTPUT_DIR / f"eden_enhanced_{timestamp}.png"
        
        if isinstance(result, tuple):
            temp_path = result[0]
        else:
            temp_path = result
            
        shutil.copy(temp_path, output_path)
        
        return str(output_path), f"✅ Enhanced with {model['name']}"
        
    except Exception as e:
        return "", f"❌ Enhancement error: {str(e)}"


def generate_3d_trellis(
    image_path: str,
    hf_token: Optional[str] = None
) -> Tuple[str, str]:
    """
    Convert 2D image to 3D mesh using Microsoft's TRELLIS.2.
    
    Returns: (glb_path, status_message)
    """
    try:
        from gradio_client import Client, handle_file
        
        if not image_path or not Path(image_path).exists():
            return "", "❌ No image provided for 3D conversion"
        
        space_id = "microsoft/TRELLIS.2-4B"
        client = Client(space_id, hf_token=hf_token)
        
        # Call TRELLIS.2 API
        result = client.predict(
            image=handle_file(image_path),
            api_name="/image_to_3d"
        )
        
        # Save GLB file
        timestamp = int(time.time())
        output_path = OUTPUT_DIR / f"eden_3d_{timestamp}.glb"
        
        if isinstance(result, tuple):
            temp_path = result[0]
        else:
            temp_path = result
            
        shutil.copy(temp_path, output_path)
        
        return str(output_path), "✅ 3D mesh generated with TRELLIS.2"
        
    except Exception as e:
        return "", f"❌ 3D generation error: {str(e)}"


def scan_seagate_model_library() -> List[List[str]]:
    """
    Scan Seagate drive for all models.
    
    Returns: List of [category, name, size, path] entries
    """
    results = []
    
    # Categories to scan
    categories = [
        "checkpoints", "loras", "vae", "upscalers", "embeddings",
        "controlnet", "t2i_adapter", "inpaint", "diffusers", 
        "clip_vision", "gligen"
    ]
    
    # Scan each category folder
    for category in categories:
        cat_path = DRIVE_DIR / category
        if not cat_path.exists():
            continue
            
        for file_path in cat_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [
                ".safetensors", ".ckpt", ".pt", ".bin", ".gguf", ".onnx"
            ]:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                results.append([
                    category,
                    file_path.name,
                    f"{size_mb:.1f} MB",
                    str(file_path.relative_to(SEAGATE))
                ])
    
    # Scan HF cache for downloaded models
    hub_path = HF_HOME / "hub"
    if hub_path.exists():
        for model_dir in hub_path.iterdir():
            if model_dir.is_dir() and "models--" in model_dir.name:
                # Parse org--model-name format
                parts = model_dir.name.replace("models--", "").split("--")
                if len(parts) >= 2:
                    org, model = parts[0], parts[1]
                    size_mb = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file()) / (1024 * 1024)
                    results.append([
                        "hf_cache",
                        f"{org}/{model}",
                        f"{size_mb:.1f} MB",
                        str(model_dir.relative_to(SEAGATE))
                    ])
    
    return sorted(results, key=lambda x: x[0])


def pull_huggingface_model(
    model_id: str,
    category: str = "checkpoints",
    hf_token: Optional[str] = None
) -> str:
    """Download a model from HuggingFace to Seagate."""
    try:
        from huggingface_hub import snapshot_download
        
        target_dir = DRIVE_DIR / category / model_id.replace("/", "--")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_download(
            repo_id=model_id,
            local_dir=str(target_dir),
            token=hf_token,
            resume_download=True
        )
        
        return f"✅ Downloaded {model_id} to {target_dir}"
        
    except Exception as e:
        return f"❌ Download error: {str(e)}"


def pull_ollama_model(model_name: str) -> str:
    """Pull a model using Ollama."""
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return f"✅ Pulled {model_name} via Ollama"
        return f"❌ Ollama error: {result.stderr}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def pull_pinokio_app(git_url: str) -> str:
    """Clone a Pinokio app from git."""
    try:
        pinokio_api = Path.home() / "pinokio" / "api"
        pinokio_api.mkdir(parents=True, exist_ok=True)
        
        app_name = git_url.split("/")[-1].replace(".git", "")
        target_dir = pinokio_api / app_name
        
        if target_dir.exists():
            return f"ℹ️ {app_name} already exists"
        
        result = subprocess.run(
            ["git", "clone", git_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return f"✅ Cloned {app_name} to Pinokio"
        return f"❌ Git error: {result.stderr}"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


def generate_video_wan21(
    prompt: str,
    model_name: str = "wan-t2v-1.3b",
    width: int = 832,
    height: int = 480,
    num_frames: int = 16,
    fps: int = 16,
    cfg_high: float = 6.5,
    cfg_low: float = 4.0,
    seed: int = -1,
    use_private: bool = False,
    hf_token: Optional[str] = None
) -> Tuple[str, str]:
    """
    Generate video using Wan2.1 via HuggingFace Spaces.
    
    Args:
        prompt: Text prompt for video
        model_name: wan-t2v-1.3b or wan-t2v-14b
        width: Video width (256, 480, 512, 720, 832)
        height: Video height (256, 480, 512, 720, 832)
        num_frames: Number of frames (8-81)
        fps: Frames per second
        cfg_high: CFG for high-noise phase (composition)
        cfg_low: CFG for low-noise phase (detail)
        seed: Random seed (-1 for random)
        use_private: Use AIBRUH/video-studio (paid) vs Wan-AI/Wan2.1 (free queue)
        hf_token: HuggingFace API token
        
    Returns:
        (video_path, status_message)
    """
    try:
        from gradio_client import Client, handle_file
        
        # Get model config
        model = VIDEO_MODELS.get(model_name, VIDEO_MODELS["wan-t2v-1.3b"])
        
        # Choose space based on private flag
        if use_private and "private_space" in model:
            space_id = model["private_space"]
        else:
            space_id = model["space"]
        
        # Connect to HF Space
        client = Client(space_id, hf_token=hf_token)
        
        # Prepare seed
        seed_val = seed if seed >= 0 else int(time.time())
        
        # Calculate effective CFG (weighted average)
        effective_cfg = cfg_high * 0.6 + cfg_low * 0.4
        
        # Call the inference endpoint
        # Wan2.1 spaces typically use /generate or /predict endpoint
        result = client.predict(
            prompt=prompt,
            width=width,
            height=height,
            num_frames=num_frames,
            fps=fps,
            guidance_scale=effective_cfg,
            seed=seed_val,
            randomize_seed=(seed < 0),
            api_name="/generate"
        )
        
        # Save result locally
        timestamp = int(time.time())
        output_path = OUTPUT_DIR / f"eden_video_{model_name}_{timestamp}.mp4"
        
        # Copy from temp to output dir
        if isinstance(result, tuple):
            temp_path = result[0]
        else:
            temp_path = result
            
        shutil.copy(temp_path, output_path)
        
        gpu_type = "Private GPU" if use_private else "Free Queue"
        return str(output_path), f"✅ Generated {num_frames} frames @ {fps}fps using {model['name']} ({gpu_type})"
        
    except Exception as e:
        return "", f"❌ Video generation error: {str(e)}"
