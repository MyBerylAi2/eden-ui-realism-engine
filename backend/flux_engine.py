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
        
        # Connect to HF Space (token optional for public spaces)
        if hf_token:
            headers = {"Authorization": f"Bearer {hf_token}"}
            client = Client(space_id, headers=headers)
        else:
            client = Client(space_id)
        
        # Get API info to find correct endpoint
        try:
            api_info = client.view_api()
            print(f"API Info for {space_id}: {list(api_info.get('named_endpoints', {}).keys())[:5]}")
        except Exception as e:
            print(f"Could not view API: {e}")
        
        # Call the inference endpoint
        seed_val = seed if seed >= 0 else int(time.time())
        
        # Try different API endpoints for different FLUX models
        # FLUX schnell uses different parameters than FLUX dev
        if "schnell" in model_name:
            # FLUX schnell API - simpler, no guidance_scale
            result = client.predict(
                prompt=full_prompt,
                seed=seed_val,
                randomize_seed=(seed < 0),
                width=width,
                height=height,
                num_inference_steps=steps,
                api_name="/infer"
            )
        else:
            # FLUX dev API - includes guidance_scale
            result = client.predict(
                prompt=full_prompt,
                seed=seed_val,
                randomize_seed=(seed < 0),
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance,
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
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
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
            if hf_token:
                headers = {"Authorization": f"Bearer {hf_token}"}
                client = Client(model["space"], headers=headers)
            else:
                client = Client(model["space"])
            
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
            if hf_token:
                headers = {"Authorization": f"Bearer {hf_token}"}
                client = Client(model["space"], headers=headers)
            else:
                client = Client(model["space"])
            result = client.predict(
                image=handle_file(image_path),
                scale=4,
                face_enhance=True,
                api_name="/predict"
            )
            
        elif model["type"] == "face":
            # CodeFormer
            if hf_token:
                headers = {"Authorization": f"Bearer {hf_token}"}
                client = Client(model["space"], headers=headers)
            else:
                client = Client(model["space"])
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
    Convert 2D image to 3D mesh using Microsoft TRELLIS.2-4B.
    
    Returns: (glb_path, status_message)
    """
    try:
        from gradio_client import Client, handle_file
        
        if not image_path or not Path(image_path).exists():
            return "", "❌ No image provided for 3D conversion"
        
        space_id = "microsoft/TRELLIS.2-4B"
        if hf_token:
            headers = {"Authorization": f"Bearer {hf_token}"}
            client = Client(space_id, headers=headers)
        else:
            client = Client(space_id)
        
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
        
        return str(output_path), "✅ Generated 3D mesh with TRELLIS.2"
        
    except Exception as e:
        return "", f"❌ 3D conversion error: {str(e)}"


# =============================================================================
# SEAGATE MODEL LIBRARY MANAGEMENT
# =============================================================================

def scan_seagate_model_library() -> List[Dict]:
    """Scan Seagate drive for locally available models."""
    models = []
    
    # Scan ComfyUI-style directories
    comfy_dirs = ["checkpoints", "loras", "vae", "controlnet", "upscale_models"]
    for dir_name in comfy_dirs:
        dir_path = DRIVE_DIR / dir_name
        if dir_path.exists():
            for file in dir_path.iterdir():
                if file.suffix in ['.safetensors', '.ckpt', '.pt', '.pth', '.bin']:
                    models.append({
                        "name": file.name,
                        "path": str(file),
                        "category": dir_name,
                        "size": file.stat().st_size
                    })
    
    return models


def pull_huggingface_model(
    model_id: str,
    category: str = "checkpoints",
    hf_token: Optional[str] = None
) -> Dict:
    """Pull a model from HuggingFace to Seagate."""
    try:
        from huggingface_hub import hf_hub_download, login
        
        if hf_token:
            login(token=hf_token)
        
        target_dir = DRIVE_DIR / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Download model
        local_path = hf_hub_download(
            repo_id=model_id,
            filename="model.safetensors",  # Adjust based on actual filename
            local_dir=str(target_dir),
            local_dir_use_symlinks=False
        )
        
        return {
            "success": True,
            "path": local_path,
            "message": f"Downloaded {model_id} to {local_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def pull_ollama_model(model_name: str) -> Dict:
    """Pull a model using Ollama."""
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Pulled {model_name} via Ollama"
            }
        else:
            return {
                "success": False,
                "error": result.stderr
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def pull_pinokio_app(git_url: str) -> Dict:
    """Clone a Pinokio app from git."""
    try:
        target_dir = DRIVE_DIR / "pinokio" / Path(git_url).stem
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
            ["git", "clone", git_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "path": str(target_dir),
                "message": f"Cloned {git_url} to {target_dir}"
            }
        else:
            return {
                "success": False,
                "error": result.stderr
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# VIDEO GENERATION - Wan2.1 via HF Spaces
# =============================================================================

def generate_video_wan21(
    prompt: str,
    model_name: str = "wan-t2v-1.3b",
    width: int = 832,
    height: int = 480,
    num_frames: int = 81,
    fps: int = 24,
    cfg_high: float = 6.5,
    cfg_low: float = 4.0,
    seed: int = -1,
    use_private: bool = False,
    hf_token: Optional[str] = None
) -> Tuple[str, str]:
    """
    Generate video using Wan2.1 via HuggingFace Spaces.
    
    Returns: (video_path, status_message)
    """
    try:
        from gradio_client import Client
        
        model = VIDEO_MODELS.get(model_name, VIDEO_MODELS["wan-t2v-1.3b"])
        
        # Choose space based on private flag
        if use_private and "private_space" in model:
            space_id = model["private_space"]
        else:
            space_id = model["space"]
        
        # Connect to HF Space (token optional for public spaces)
        if hf_token:
            headers = {"Authorization": f"Bearer {hf_token}"}
            client = Client(space_id, headers=headers)
        else:
            client = Client(space_id)
        
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
            cfg_scale=effective_cfg,
            seed=seed_val,
            api_name="/generate"
        )
        
        # Save video locally
        timestamp = int(time.time())
        output_path = OUTPUT_DIR / f"eden_video_{model_name}_{timestamp}.mp4"
        
        if isinstance(result, tuple):
            temp_path = result[0]
        else:
            temp_path = result
            
        shutil.copy(temp_path, output_path)
        
        return str(output_path), f"✅ Generated {num_frames/fps:.1f}s video with {model['name']}"
        
    except Exception as e:
        return "", f"❌ Video generation error: {str(e)}"
