"""
Pinokio Integration for EDEN Realism Engine
============================================
Scans and loads models from Pinokio folders on Seagate
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import subprocess

# Pinokio paths on Seagate
SEAGATE_PINOKIO = Path("/media/letsgo/9361ec48-323e-44ae-84d5-9060ae68b5751/PINOKIO")
LOCAL_PINOKIO = Path.home() / "pinokio"

def get_pinokio_paths() -> List[Path]:
    """Get all Pinokio installation paths"""
    paths = []
    if SEAGATE_PINOKIO.exists():
        paths.append(SEAGATE_PINOKIO)
    if LOCAL_PINOKIO.exists():
        paths.append(LOCAL_PINOKIO)
    return paths

def scan_pinokio_models() -> Dict[str, List[Dict]]:
    """
    Scan Pinokio folders for available models
    Returns categorized model list
    """
    models = {
        "checkpoints": [],
        "loras": [],
        "embeddings": [],
        "vae": [],
        "clip": [],
        "unet": [],
        "diffusers": [],
        "gguf": [],
        "ollama": []
    }
    
    for pinokio_path in get_pinokio_paths():
        # Check various model locations
        model_dirs = {
            "checkpoints": ["models", "checkpoints", "drive/models", "drive/checkpoints"],
            "loras": ["loras", "drive/loras", "models/loras"],
            "vae": ["vae", "drive/vae", "models/vae"],
            "embeddings": ["embeddings", "drive/embeddings", "models/embeddings"],
            "clip": ["clip", "drive/clip", "models/clip"],
            "unet": ["unet", "drive/unet", "models/unet"],
            "gguf": ["gguf", "drive/gguf", "models/gguf"],
            "ollama": ["ollama", "drive/ollama"]
        }
        
        for category, dirs in model_dirs.items():
            for dir_name in dirs:
                dir_path = pinokio_path / dir_name
                if dir_path.exists():
                    for file in dir_path.rglob("*"):
                        if file.suffix in ['.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.gguf']:
                            models[category].append({
                                "name": file.name,
                                "path": str(file),
                                "size": file.stat().st_size,
                                "modified": file.stat().st_mtime
                            })
    
    return models

def get_available_pinokio_apps() -> List[Dict]:
    """Get list of installed Pinokio apps"""
    apps = []
    
    for pinokio_path in get_pinokio_paths():
        apps_dir = pinokio_path / "apps"
        if apps_dir.exists():
            for app_dir in apps_dir.iterdir():
                if app_dir.is_dir():
                    app_json = app_dir / "pinokio.json"
                    if app_json.exists():
                        try:
                            with open(app_json) as f:
                                config = json.load(f)
                            apps.append({
                                "name": config.get("name", app_dir.name),
                                "path": str(app_dir),
                                "config": config
                            })
                        except:
                            apps.append({
                                "name": app_dir.name,
                                "path": str(app_dir)
                            })
    
    return apps

def generate_with_pinokio_model(
    prompt: str,
    model_path: str,
    output_dir: Path,
    steps: int = 28,
    guidance: float = 7.5,
    width: int = 1024,
    height: int = 1024,
    seed: int = -1
) -> Tuple[str, str]:
    """
    Generate image using a local Pinokio model via diffusers or ollama
    """
    try:
        import torch
        from diffusers import StableDiffusionPipeline, DiffusionPipeline
        from PIL import Image
        
        model_file = Path(model_path)
        
        # Determine model type
        if model_file.suffix == '.gguf':
            # Use Ollama for GGUF models
            return generate_with_ollama(prompt, model_file.stem, output_dir)
        
        # Load with diffusers
        if "xl" in model_file.name.lower() or "sdxl" in model_file.name.lower():
            # SDXL model
            pipe = DiffusionPipeline.from_pretrained(
                str(model_file.parent),
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                use_safetensors=True
            )
        else:
            # SD 1.5 or other
            pipe = StableDiffusionPipeline.from_single_file(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                use_safetensors=True
            )
        
        # Move to GPU if available
        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
        elif torch.backends.mps.is_available():
            pipe = pipe.to("mps")
        
        # Generate
        generator = torch.Generator(device=pipe.device)
        if seed >= 0:
            generator = generator.manual_seed(seed)
        
        result = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=generator
        )
        
        # Save
        timestamp = int(time.time())
        output_path = output_dir / f"eden_pinokio_{timestamp}.png"
        result.images[0].save(output_path)
        
        return str(output_path), f"✅ Generated with Pinokio model {model_file.name}"
        
    except Exception as e:
        return "", f"❌ Pinokio generation error: {str(e)}"

def generate_with_ollama(prompt: str, model_name: str, output_dir: Path) -> Tuple[str, str]:
    """Generate using Ollama for text-based models"""
    try:
        # Use Ollama to generate image description
        result = subprocess.run(
            ["ollama", "run", model_name, f"Generate a detailed image prompt for: {prompt}"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return "", f"❌ Ollama error: {result.stderr}"
        
        # Save the description
        timestamp = int(time.time())
        output_path = output_dir / f"eden_pinokio_ollama_{timestamp}.txt"
        
        with open(output_path, 'w') as f:
            f.write(f"Original prompt: {prompt}\n")
            f.write(f"Ollama ({model_name}) generated:\n")
            f.write(result.stdout)
        
        return str(output_path), f"✅ Generated prompt with Ollama {model_name}"
        
    except Exception as e:
        return "", f"❌ Ollama generation error: {str(e)}"

def pull_model_to_pinokio(model_id: str, category: str = "checkpoints") -> Dict:
    """Pull a model from HuggingFace to Pinokio"""
    try:
        from huggingface_hub import hf_hub_download, login
        
        target_dir = SEAGATE_PINOKIO / "models" / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Download model
        local_path = hf_hub_download(
            repo_id=model_id,
            filename="model.safetensors",
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

# Export
__all__ = [
    'scan_pinokio_models',
    'get_available_pinokio_apps',
    'generate_with_pinokio_model',
    'pull_model_to_pinokio',
    'get_pinokio_paths'
]
