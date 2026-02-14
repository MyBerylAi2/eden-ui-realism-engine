"""
EDEN UI REALISM ENGINE - Model Manager
======================================
HuggingFace model management with caching, loading, and optimization.
"""
import os
import torch
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from huggingface_hub import (
    HfApi, hf_hub_download, snapshot_download, 
    list_models, model_info as hf_model_info
)
from diffusers import (
    StableDiffusionPipeline, StableDiffusionXLPipeline,
    DPMSolverMultistepScheduler, EulerAncestralDiscreteScheduler,
    DDIMScheduler, DiffusionPipeline
)
from transformers import CLIPTextModel, CLIPTokenizer
import json

from config import get_settings, EDEN_MODEL_PRESETS
from database import HFModel, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class EDENModelManager:
    """
    Centralized model manager for EDEN UI.
    Handles HuggingFace model downloading, caching, and loading.
    """
    
    def __init__(self):
        self.api = HfApi(token=settings.HF_TOKEN)
        self.loaded_models: Dict[str, Any] = {}
        self.current_model_id: Optional[str] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        # Ensure directories exist
        os.makedirs(settings.MODELS_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)
        
    def search_models(
        self, 
        query: str = "", 
        model_type: str = "text-to-image",
        limit: int = 50,
        sort: str = "downloads"
    ) -> List[Dict[str, Any]]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query string
            model_type: Type of model (text-to-image, text-to-video, etc.)
            limit: Maximum results
            sort: Sort by (downloads, likes, created)
            
        Returns:
            List of model information dictionaries
        """
        try:
            models = list_models(
                search=query,
                filter=model_type,
                sort=sort,
                limit=limit,
                fetch_config=True
            )
            
            results = []
            for model in models:
                info = {
                    "id": model.modelId,
                    "author": model.author,
                    "downloads": model.downloads,
                    "likes": model.likes,
                    "tags": model.tags,
                    "pipeline_tag": model.pipeline_tag,
                    "description": model.cardData.get("description", "") if model.cardData else "",
                    "url": f"https://huggingface.co/{model.modelId}"
                }
                results.append(info)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching models: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific model."""
        try:
            info = hf_model_info(model_id, token=settings.HF_TOKEN)
            return {
                "id": info.id,
                "author": info.author,
                "downloads": info.downloads,
                "likes": info.likes,
                "tags": info.tags,
                "pipeline_tag": info.pipeline_tag,
                "siblings": [f.rfilename for f in info.siblings] if info.siblings else [],
                "config": info.config,
                "description": info.cardData.get("description", "") if info.cardData else "",
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}
    
    def download_model(
        self, 
        model_id: str, 
        local_dir: Optional[str] = None,
        use_safetensors: bool = True
    ) -> str:
        """
        Download a model from HuggingFace Hub.
        
        Args:
            model_id: HuggingFace model ID
            local_dir: Local directory to download to
            use_safetensors: Prefer SafeTensors format
            
        Returns:
            Path to downloaded model
        """
        if local_dir is None:
            local_dir = os.path.join(settings.MODELS_DIR, model_id.replace("/", "--"))
        
        os.makedirs(local_dir, exist_ok=True)
        
        try:
            logger.info(f"Downloading model {model_id} to {local_dir}")
            
            # Download the model
            snapshot_path = snapshot_download(
                repo_id=model_id,
                local_dir=local_dir,
                token=settings.HF_TOKEN,
                resume_download=True,
                local_files_only=False
            )
            
            logger.info(f"Model downloaded successfully to {snapshot_path}")
            return snapshot_path
            
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            raise
    
    def load_model(
        self, 
        model_id: str,
        model_type: str = "auto",
        scheduler: str = "DPM++ 2M Karras",
        **kwargs
    ) -> Any:
        """
        Load a diffusion model into memory.
        
        Args:
            model_id: Model ID or local path
            model_type: Type of model pipeline
            scheduler: Scheduler to use
            **kwargs: Additional pipeline arguments
            
        Returns:
            Loaded pipeline
        """
        # Check if already loaded
        if model_id in self.loaded_models:
            logger.info(f"Model {model_id} already loaded")
            self.current_model_id = model_id
            return self.loaded_models[model_id]
        
        try:
            logger.info(f"Loading model {model_id}")
            
            # Determine if it's a local path or HF model ID
            if os.path.exists(model_id):
                model_path = model_id
            else:
                # Try to download if not exists
                local_path = os.path.join(settings.MODELS_DIR, model_id.replace("/", "--"))
                if os.path.exists(local_path):
                    model_path = local_path
                else:
                    model_path = model_id  # Let diffusers handle download
            
            # Load appropriate pipeline
            pipeline_kwargs = {
                "torch_dtype": self.torch_dtype,
                "use_safetensors": True,
                **kwargs
            }
            
            if model_type == "sdxl":
                pipe = StableDiffusionXLPipeline.from_pretrained(
                    model_path,
                    **pipeline_kwargs
                )
            else:
                pipe = StableDiffusionPipeline.from_pretrained(
                    model_path,
                    **pipeline_kwargs
                )
            
            # Set scheduler
            pipe = self._set_scheduler(pipe, scheduler)
            
            # Move to device
            pipe = pipe.to(self.device)
            
            # Enable optimizations
            if self.device == "cuda":
                # Enable memory efficient attention
                if hasattr(pipe, "enable_xformers_memory_efficient_attention"):
                    pipe.enable_xformers_memory_efficient_attention()
                
                # Enable VAE slicing for memory efficiency
                if hasattr(pipe, "enable_vae_slicing"):
                    pipe.enable_vae_slicing()
                
                # Enable model CPU offloading if needed
                if hasattr(pipe, "enable_model_cpu_offload"):
                    # Uncomment for low VRAM systems
                    # pipe.enable_model_cpu_offload()
                    pass
            
            self.loaded_models[model_id] = pipe
            self.current_model_id = model_id
            
            logger.info(f"Model {model_id} loaded successfully")
            return pipe
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _set_scheduler(self, pipe: Any, scheduler_name: str) -> Any:
        """Set the scheduler for the pipeline."""
        scheduler_map = {
            "DPM++ 2M Karras": DPMSolverMultistepScheduler,
            "DPM++ 2M": DPMSolverMultistepScheduler,
            "Euler a": EulerAncestralDiscreteScheduler,
            "Euler": EulerAncestralDiscreteScheduler,
            "DDIM": DDIMScheduler,
        }
        
        scheduler_class = scheduler_map.get(scheduler_name, DPMSolverMultistepScheduler)
        
        if scheduler_name in ["DPM++ 2M Karras", "Euler a"]:
            pipe.scheduler = scheduler_class.from_config(
                pipe.scheduler.config,
                use_karras_sigmas=True
            )
        else:
            pipe.scheduler = scheduler_class.from_config(pipe.scheduler.config)
        
        return pipe
    
    def unload_model(self, model_id: Optional[str] = None):
        """Unload a model from memory to free VRAM."""
        if model_id is None:
            model_id = self.current_model_id
        
        if model_id and model_id in self.loaded_models:
            del self.loaded_models[model_id]
            torch.cuda.empty_cache()
            logger.info(f"Model {model_id} unloaded")
    
    def list_downloaded_models(self) -> List[Dict[str, Any]]:
        """List all locally downloaded models."""
        models = []
        
        if not os.path.exists(settings.MODELS_DIR):
            return models
        
        for item in os.listdir(settings.MODELS_DIR):
            model_path = os.path.join(settings.MODELS_DIR, item)
            if os.path.isdir(model_path):
                model_id = item.replace("--", "/")
                
                # Check for model config
                config_path = os.path.join(model_path, "model_index.json")
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        config = json.load(f)
                    model_type = config.get("_class_name", "Unknown")
                else:
                    model_type = "Unknown"
                
                models.append({
                    "id": model_id,
                    "local_path": model_path,
                    "type": model_type,
                    "size": self._get_dir_size(model_path)
                })
        
        return models
    
    def _get_dir_size(self, path: str) -> int:
        """Get total size of directory in bytes."""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
        return total
    
    def get_recommended_models(self) -> List[Dict[str, Any]]:
        """Get list of recommended models for EDEN UI."""
        recommendations = [
            {
                "id": "stabilityai/stable-diffusion-xl-base-1.0",
                "name": "SDXL Base 1.0",
                "type": "text-to-image",
                "description": "High-quality image generation",
                "category": "base"
            },
            {
                "id": "runwayml/stable-diffusion-v1-5",
                "name": "Stable Diffusion 1.5",
                "type": "text-to-image",
                "description": "Classic SD model, great for fine-tuning",
                "category": "base"
            },
            {
                "id": "stabilityai/sd-turbo",
                "name": "SD Turbo",
                "type": "text-to-image",
                "description": "Fast single-step generation",
                "category": "speed"
            },
            {
                "id": "madebyollin/sdxl-vae-fp16-fix",
                "name": "SDXL VAE Fix",
                "type": "vae",
                "description": "Fixed FP16 VAE for SDXL",
                "category": "component"
            },
            {
                "id": "stabilityai/stable-video-diffusion-img2vid-xt",
                "name": "SVD XT",
                "type": "image-to-video",
                "description": "Image to video generation",
                "category": "video"
            },
            {
                "id": "Wan-AI/Wan2.1-T2V-1.3B",
                "name": "Wan2.1 T2V 1.3B",
                "type": "text-to-video",
                "description": "Efficient text-to-video model",
                "category": "video"
            },
        ]
        return recommendations


# Global model manager instance
model_manager = EDENModelManager()
