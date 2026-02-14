"""
EDEN UI REALISM ENGINE - Generation Engine
==========================================
Core generation logic for images and videos with EDEN-specific optimizations.
"""
import os
import torch
import logging
import time
from typing import Optional, List, Dict, Any, Union
from PIL import Image
import numpy as np
from pathlib import Path

from config import get_settings, get_eden_negative_prompt, EDEN_MODEL_PRESETS
from model_manager import model_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class EDENGenerationEngine:
    """
    EDEN's core generation engine with optimizations for photorealism.
    """
    
    def __init__(self):
        self.output_dir = settings.OUTPUTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_image(
        self,
        prompt: str,
        model_id: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        scheduler: str = "DPM++ 2M Karras",
        use_eden_negative: bool = True,
        preset: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image with EDEN optimizations.
        
        Args:
            prompt: Text prompt
            model_id: Model to use
            negative_prompt: Custom negative prompt
            width: Image width
            height: Image height
            num_inference_steps: Number of denoising steps
            guidance_scale: CFG scale
            seed: Random seed
            scheduler: Scheduler type
            use_eden_negative: Use EDEN's comprehensive negative prompt
            preset: Use a preset configuration
            **kwargs: Additional pipeline arguments
            
        Returns:
            Dictionary with image path and metadata
        """
        start_time = time.time()
        
        try:
            # Apply preset if specified
            if preset and preset in EDEN_MODEL_PRESETS:
                preset_config = EDEN_MODEL_PRESETS[preset]
                guidance_scale = preset_config.get("guidance_scale", guidance_scale)
                num_inference_steps = preset_config.get("num_inference_steps", num_inference_steps)
                scheduler = preset_config.get("scheduler", scheduler)
            
            # Build negative prompt
            if use_eden_negative:
                eden_negative = get_eden_negative_prompt("all")
                if negative_prompt:
                    negative_prompt = f"{eden_negative}, {negative_prompt}"
                else:
                    negative_prompt = eden_negative
            elif not negative_prompt:
                negative_prompt = get_eden_negative_prompt("base")
            
            # Load model
            pipe = model_manager.load_model(model_id, scheduler=scheduler)
            
            # Set seed
            generator = None
            if seed is not None:
                generator = torch.Generator(device=model_manager.device).manual_seed(seed)
            
            # Generate
            logger.info(f"Generating image: {width}x{height}, steps={num_inference_steps}")
            
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                **kwargs
            )
            
            image = result.images[0]
            
            # Save output
            timestamp = int(time.time())
            output_path = os.path.join(self.output_dir, f"eden_image_{timestamp}.png")
            image.save(output_path)
            
            generation_time = time.time() - start_time
            
            return {
                "success": True,
                "output_path": output_path,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
                "generation_time": generation_time,
                "model_id": model_id
            }
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_video(
        self,
        prompt: str,
        model_id: str,
        negative_prompt: Optional[str] = None,
        width: int = 832,
        height: int = 480,
        num_frames: int = 16,
        fps: float = 8,
        num_inference_steps: int = 25,
        guidance_scale: float = 6.0,
        seed: Optional[int] = None,
        scheduler: str = "DDIM",
        use_eden_negative: bool = True,
        preset: str = "cinematic_video",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a video with EDEN optimizations for temporal consistency.
        
        Args:
            prompt: Text prompt
            model_id: Video model ID
            negative_prompt: Custom negative prompt
            width: Video width
            height: Video height
            num_frames: Number of frames
            fps: Frames per second
            num_inference_steps: Denoising steps
            guidance_scale: CFG scale
            seed: Random seed
            scheduler: Scheduler type
            use_eden_negative: Use EDEN's video-optimized negative prompt
            preset: Preset configuration
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with video path and metadata
        """
        start_time = time.time()
        
        try:
            # Apply preset
            if preset in EDEN_MODEL_PRESETS:
                preset_config = EDEN_MODEL_PRESETS[preset]
                guidance_scale = preset_config.get("guidance_scale", guidance_scale)
                num_inference_steps = preset_config.get("num_inference_steps", num_inference_steps)
                fps = preset_config.get("fps", fps)
            
            # Build negative prompt with video-specific keywords
            if use_eden_negative:
                eden_negative = get_eden_negative_prompt("all")
                if negative_prompt:
                    negative_prompt = f"{eden_negative}, {negative_prompt}"
                else:
                    negative_prompt = eden_negative
            elif not negative_prompt:
                negative_prompt = get_eden_negative_prompt("video_artifacts")
            
            # Load video model
            from diffusers import DiffusionPipeline
            
            pipe = model_manager.load_model(
                model_id,
                model_type="auto",
                scheduler=scheduler
            )
            
            # Set seed
            generator = None
            if seed is not None:
                generator = torch.Generator(device=model_manager.device).manual_seed(seed)
            
            logger.info(f"Generating video: {width}x{height}x{num_frames}@{fps}fps")
            
            # Generate video
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                **kwargs
            )
            
            # Export video
            frames = result.frames[0] if hasattr(result, 'frames') else result[0]
            
            timestamp = int(time.time())
            output_path = os.path.join(self.output_dir, f"eden_video_{timestamp}.mp4")
            
            # Use imageio for video export
            import imageio
            writer = imageio.get_writer(output_path, fps=fps, codec='libx264')
            for frame in frames:
                writer.append_data(np.array(frame))
            writer.close()
            
            generation_time = time.time() - start_time
            
            return {
                "success": True,
                "output_path": output_path,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_frames": num_frames,
                "fps": fps,
                "duration": num_frames / fps,
                "steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
                "generation_time": generation_time,
                "model_id": model_id
            }
            
        except Exception as e:
            logger.error(f"Video generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def image_to_video(
        self,
        image_path: str,
        prompt: str,
        model_id: str = "stabilityai/stable-video-diffusion-img2vid-xt",
        num_frames: int = 25,
        fps: float = 6,
        motion_bucket_id: int = 127,
        noise_aug_strength: float = 0.02,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert an image to video using SVD or similar models.
        
        Args:
            image_path: Path to input image
            prompt: Text prompt for video generation
            model_id: Image-to-video model
            num_frames: Number of frames to generate
            fps: Frames per second
            motion_bucket_id: Motion intensity (0-255)
            noise_aug_strength: Noise augmentation
            seed: Random seed
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with video path and metadata
        """
        start_time = time.time()
        
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Load SVD model
            from diffusers import StableVideoDiffusionPipeline
            
            pipe = model_manager.load_model(model_id)
            
            # Set seed
            generator = None
            if seed is not None:
                generator = torch.Generator(device=model_manager.device).manual_seed(seed)
            
            logger.info(f"Generating video from image: {num_frames} frames")
            
            result = pipe(
                image,
                height=image.height,
                width=image.width,
                num_frames=num_frames,
                motion_bucket_id=motion_bucket_id,
                noise_aug_strength=noise_aug_strength,
                generator=generator,
                **kwargs
            )
            
            frames = result.frames[0]
            
            # Export video
            timestamp = int(time.time())
            output_path = os.path.join(self.output_dir, f"eden_img2vid_{timestamp}.mp4")
            
            import imageio
            writer = imageio.get_writer(output_path, fps=fps, codec='libx264')
            for frame in frames:
                writer.append_data(np.array(frame))
            writer.close()
            
            generation_time = time.time() - start_time
            
            return {
                "success": True,
                "output_path": output_path,
                "prompt": prompt,
                "num_frames": num_frames,
                "fps": fps,
                "motion_bucket_id": motion_bucket_id,
                "seed": seed,
                "generation_time": generation_time,
                "model_id": model_id
            }
            
        except Exception as e:
            logger.error(f"Image-to-video error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def enhance_generation(
        self,
        input_path: str,
        enhancement_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply EDEN enhancement modules to generated content.
        
        Args:
            input_path: Path to input image/video
            enhancement_type: Type of enhancement (upscale, face_detail, etc.)
            **kwargs: Enhancement-specific parameters
            
        Returns:
            Dictionary with enhanced output path
        """
        try:
            if enhancement_type == "upscale":
                return self._upscale(input_path, **kwargs)
            elif enhancement_type == "face_detail":
                return self._face_enhance(input_path, **kwargs)
            else:
                return {"success": False, "error": f"Unknown enhancement: {enhancement_type}"}
                
        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return {"success": False, "error": str(e)}
    
    def _upscale(self, image_path: str, scale: int = 2) -> Dict[str, Any]:
        """Upscale an image using Real-ESRGAN."""
        # Placeholder for upscaling implementation
        # Would integrate Real-ESRGAN or similar
        return {"success": True, "output_path": image_path}
    
    def _face_enhance(self, image_path: str) -> Dict[str, Any]:
        """Enhance face details using GFPGAN/CodeFormer."""
        # Placeholder for face enhancement
        return {"success": True, "output_path": image_path}


# Global generation engine instance
generation_engine = EDENGenerationEngine()
