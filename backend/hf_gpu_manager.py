"""
EDEN UI REALISM ENGINE - HuggingFace GPU Manager
================================================
Manage HF Spaces GPU scaling with pricing and auto-sleep.
"""
import os
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from config import get_settings

settings = get_settings()


@dataclass
class GPUOption:
    """GPU tier option with pricing."""
    name: str
    gpu_type: str
    vram_gb: int
    price_per_hour: float
    description: str
    recommended: bool = False


# HF GPU Pricing (updated periodically)
HF_GPU_OPTIONS: Dict[str, GPUOption] = {
    "zero": GPUOption(
        name="Zero GPU",
        gpu_type="CPU/Shared",
        vram_gb=0,
        price_per_hour=0.0,
        description="Free tier - shared CPU, enters sleep after inactivity"
    ),
    "t4": GPUOption(
        name="NVIDIA T4",
        gpu_type="Tesla T4",
        vram_gb=16,
        price_per_hour=0.45,
        description="Entry GPU - good for FLUX schnell, 16GB VRAM",
        recommended=True
    ),
    "l4": GPUOption(
        name="NVIDIA L4",
        gpu_type="L4",
        vram_gb=24,
        price_per_hour=0.80,
        description="Mid-range - great for FLUX dev, 24GB VRAM"
    ),
    "a10g": GPUOption(
        name="NVIDIA A10G",
        gpu_type="A10G",
        vram_gb=24,
        price_per_hour=1.20,
        description="High-performance - fastest inference, 24GB VRAM"
    ),
    "a100": GPUOption(
        name="NVIDIA A100",
        gpu_type="A100",
        vram_gb=80,
        price_per_hour=4.50,
        description="Data center - 80GB VRAM, batch processing"
    ),
    "h100": GPUOption(
        name="NVIDIA H100",
        gpu_type="H100",
        vram_gb=80,
        price_per_hour=8.00,
        description="Latest gen - maximum performance, 80GB VRAM"
    ),
}


class HFGPUManager:
    """
    Manages HuggingFace GPU scaling with auto-sleep functionality.
    """
    
    def __init__(self):
        self.active_upgrades: Dict[str, Dict] = {}  # space_id -> upgrade info
        self.sleep_timers: Dict[str, threading.Timer] = {}
        self.default_sleep_minutes = 10  # Auto-sleep after 10 min by default
        self.price_per_minute_cache: Dict[str, float] = {}
        
    def get_gpu_pricing(self) -> List[Dict[str, Any]]:
        """Get current GPU pricing options."""
        pricing = []
        for key, gpu in HF_GPU_OPTIONS.items():
            pricing.append({
                "id": key,
                "name": gpu.name,
                "gpu_type": gpu.gpu_type,
                "vram_gb": gpu.vram_gb,
                "price_per_hour": gpu.price_per_hour,
                "price_per_minute": round(gpu.price_per_hour / 60, 4),
                "description": gpu.description,
                "recommended": gpu.recommended,
            })
        return pricing
    
    def calculate_cost_estimate(
        self, 
        gpu_tier: str, 
        estimated_minutes: int = 10
    ) -> Dict[str, Any]:
        """Calculate estimated cost for a GPU tier."""
        gpu = HF_GPU_OPTIONS.get(gpu_tier)
        if not gpu:
            return {"error": "Invalid GPU tier"}
        
        cost_per_minute = gpu.price_per_hour / 60
        estimated_cost = cost_per_minute * estimated_minutes
        
        return {
            "gpu_tier": gpu_tier,
            "gpu_name": gpu.name,
            "price_per_hour": gpu.price_per_hour,
            "estimated_minutes": estimated_minutes,
            "estimated_cost": round(estimated_cost, 4),
            "vram_gb": gpu.vram_gb,
        }
    
    def upgrade_space_gpu(
        self, 
        space_id: str, 
        gpu_tier: str,
        sleep_after_minutes: Optional[int] = None,
        hf_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upgrade a HF Space to a specific GPU tier.
        
        Args:
            space_id: HuggingFace Space ID (e.g., "user/space-name")
            gpu_tier: GPU tier key (zero, t4, l4, a10g, a100, h100)
            sleep_after_minutes: Auto-sleep after N minutes (default: 10)
            hf_token: HuggingFace API token
        """
        try:
            from huggingface_hub import HfApi
            
            api = HfApi(token=hf_token or settings.HF_TOKEN)
            gpu = HF_GPU_OPTIONS.get(gpu_tier)
            
            if not gpu:
                return {"success": False, "error": f"Unknown GPU tier: {gpu_tier}"}
            
            # Map tier to HF hardware type
            hardware_map = {
                "zero": "cpu-basic",
                "t4": "t4-small",
                "l4": "l4x1",
                "a10g": "a10g-largex1", 
                "a100": "a100-large",
                "h100": "h100-large",
            }
            
            hardware = hardware_map.get(gpu_tier, "cpu-basic")
            
            # Update space hardware
            api.request_space_hardware(
                repo_id=space_id,
                hardware=hardware
            )
            
            # Track the upgrade
            upgrade_info = {
                "space_id": space_id,
                "gpu_tier": gpu_tier,
                "gpu_name": gpu.name,
                "upgraded_at": datetime.now().isoformat(),
                "price_per_hour": gpu.price_per_hour,
                "auto_sleep_minutes": sleep_after_minutes or self.default_sleep_minutes,
            }
            self.active_upgrades[space_id] = upgrade_info
            
            # Cancel any existing timer
            if space_id in self.sleep_timers:
                self.sleep_timers[space_id].cancel()
            
            # Set auto-sleep timer if not Zero GPU
            if gpu_tier != "zero" and sleep_after_minutes != 0:
                timer = threading.Timer(
                    (sleep_after_minutes or self.default_sleep_minutes) * 60,
                    self._auto_sleep,
                    args=[space_id, hf_token]
                )
                timer.daemon = True
                timer.start()
                self.sleep_timers[space_id] = timer
                
                upgrade_info["sleep_scheduled_at"] = (
                    datetime.now() + timedelta(minutes=sleep_after_minutes or self.default_sleep_minutes)
                ).isoformat()
            
            return {
                "success": True,
                "message": f"Upgraded {space_id} to {gpu.name}",
                "upgrade_info": upgrade_info,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def downgrade_to_zero(
        self, 
        space_id: str, 
        hf_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Downgrade space to Zero GPU (free tier)."""
        try:
            from huggingface_hub import HfApi
            
            api = HfApi(token=hf_token or settings.HF_TOKEN)
            
            api.request_space_hardware(
                repo_id=space_id,
                hardware="cpu-basic"
            )
            
            # Cancel auto-sleep timer
            if space_id in self.sleep_timers:
                self.sleep_timers[space_id].cancel()
                del self.sleep_timers[space_id]
            
            # Remove from active upgrades
            if space_id in self.active_upgrades:
                del self.active_upgrades[space_id]
            
            return {
                "success": True,
                "message": f"Downgraded {space_id} to Zero GPU",
                "cost_saved": "GPU released, no longer billing",
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _auto_sleep(self, space_id: str, hf_token: Optional[str] = None):
        """Internal: Auto-sleep callback."""
        print(f"[HF GPU Manager] Auto-sleeping {space_id}...")
        self.downgrade_to_zero(space_id, hf_token)
        
        # Could add notification here (webhook, etc.)
    
    def get_space_status(
        self, 
        space_id: str, 
        hf_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get current GPU status of a space."""
        try:
            from huggingface_hub import HfApi
            
            api = HfApi(token=hf_token or settings.HF_TOKEN)
            runtime = api.get_space_runtime(repo_id=space_id)
            
            hardware = runtime.hardware or "cpu-basic"
            
            # Map HF hardware names back to our tiers
            hardware_to_tier = {
                "cpu-basic": "zero",
                "t4-small": "t4",
                "l4x1": "l4",
                "a10g-largex1": "a10g",
                "a100-large": "a100",
                "h100-large": "h100",
            }
            
            tier = hardware_to_tier.get(hardware, "unknown")
            gpu_info = HF_GPU_OPTIONS.get(tier)
            
            status = {
                "space_id": space_id,
                "hardware": hardware,
                "tier": tier,
                "gpu_name": gpu_info.name if gpu_info else hardware,
                "vram_gb": gpu_info.vram_gb if gpu_info else 0,
                "price_per_hour": gpu_info.price_per_hour if gpu_info else 0,
                "is_upgraded": tier != "zero",
            }
            
            # Add active upgrade info if tracked
            if space_id in self.active_upgrades:
                status["upgrade_info"] = self.active_upgrades[space_id]
            
            return status
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_active_upgrades(self) -> List[Dict[str, Any]]:
        """Get list of currently upgraded spaces."""
        return list(self.active_upgrades.values())
    
    def extend_sleep_timer(
        self, 
        space_id: str, 
        additional_minutes: int = 10
    ) -> Dict[str, Any]:
        """Extend the auto-sleep timer for an upgraded space."""
        if space_id not in self.active_upgrades:
            return {"success": False, "error": "Space not currently upgraded"}
        
        # Cancel existing timer
        if space_id in self.sleep_timers:
            self.sleep_timers[space_id].cancel()
        
        # Set new timer
        timer = threading.Timer(
            additional_minutes * 60,
            self._auto_sleep,
            args=[space_id, settings.HF_TOKEN]
        )
        timer.daemon = True
        timer.start()
        self.sleep_timers[space_id] = timer
        
        # Update info
        self.active_upgrades[space_id]["auto_sleep_minutes"] += additional_minutes
        new_sleep_time = datetime.now() + timedelta(minutes=additional_minutes)
        self.active_upgrades[space_id]["sleep_scheduled_at"] = new_sleep_time.isoformat()
        
        return {
            "success": True,
            "message": f"Extended sleep timer by {additional_minutes} minutes",
            "new_sleep_time": new_sleep_time.isoformat(),
        }


# Global GPU manager instance
gpu_manager = HFGPUManager()
