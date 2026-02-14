"""
Microsoft AgentGen / Agent Network Integration
==============================================
Agentic Teams for EDEN Realism Engine
- Kling Expert: Photorealism configuration
- Error Handler: Auto-fix generation failures
- Detail Master: Skin/pore realism optimization
- Lighting Pro: Cinematic lighting setup
- Retry Bot: Auto-retry on failures
- Prompt Engineer: Prompt optimization
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re

class AgentType(Enum):
    KLING_EXPERT = "kling"
    ERROR_HANDLER = "error"
    DETAIL_MASTER = "detail"
    LIGHTING_PRO = "light"
    RETRY_BOT = "retry"
    PROMPT_ENGINEER = "prompt"

@dataclass
class Agent:
    """Base agent class for Agent Network"""
    name: str
    agent_type: AgentType
    role: str
    active: bool = True
    
    def process(self, context: Dict) -> Dict:
        """Process context and return enhanced/modified version"""
        raise NotImplementedError

@dataclass
class KlingExpertAgent(Agent):
    """Kling AI-style photorealism expert"""
    
    def __init__(self):
        super().__init__(
            name="Kling Expert",
            agent_type=AgentType.KLING_EXPERT,
            role="Photorealism configuration expert"
        )
    
    def process(self, context: Dict) -> Dict:
        """Apply Kling-style photorealism settings"""
        prompt = context.get("prompt", "")
        settings = context.get("settings", {})
        
        # Add photorealism keywords
        if "photorealistic" not in prompt.lower() and "realistic" not in prompt.lower():
            prompt = f"Ultra-photorealistic, {prompt}"
        
        # Add Kling-style keywords
        kling_keywords = [
            "8K UHD",
            "high detail",
            "natural skin texture" if "skin" in prompt.lower() or "face" in prompt.lower() else "",
            "cinematic lighting" if "lighting" not in prompt.lower() else "",
            "subsurface scattering" if "skin" in prompt.lower() or "face" in prompt.lower() else "",
            "hyperdetailed"
        ]
        
        # Only add non-empty keywords
        keywords_to_add = [k for k in kling_keywords if k]
        if keywords_to_add:
            prompt = f"{prompt}, {', '.join(keywords_to_add)}"
        
        # Optimize settings for photorealism
        settings["guidance_scale"] = min(settings.get("guidance_scale", 5.0), 7.0)
        settings["num_inference_steps"] = max(settings.get("num_inference_steps", 28), 28)
        
        context["prompt"] = prompt
        context["settings"] = settings
        context["applied_kling_config"] = True
        
        return context

@dataclass
class ErrorHandlerAgent(Agent):
    """Handles generation errors and provides recovery strategies"""
    
    def __init__(self):
        super().__init__(
            name="Error Handler",
            agent_type=AgentType.ERROR_HANDLER,
            role="Auto-fix generation failures"
        )
        self.error_patterns = {
            "timeout": ["timeout", "timed out", "connection error"],
            "rate_limit": ["rate limit", "too many requests", "429"],
            "gpu_unavailable": ["gpu", "cuda", "out of memory", "oom"],
            "invalid_prompt": ["prompt", "invalid", "nsfw", "blocked"],
            "space_down": ["space is down", "loading", "queue"]
        }
    
    def process(self, context: Dict) -> Dict:
        """Analyze error and provide recovery strategy"""
        error = context.get("error", "")
        error_lower = str(error).lower()
        
        strategy = {"action": "none", "delay": 0}
        
        for error_type, patterns in self.error_patterns.items():
            if any(p in error_lower for p in patterns):
                if error_type == "timeout":
                    strategy = {"action": "retry_with_wait", "delay": 5}
                elif error_type == "rate_limit":
                    strategy = {"action": "retry_with_wait", "delay": 30}
                elif error_type == "gpu_unavailable":
                    strategy = {"action": "downgrade_resolution", "delay": 2}
                elif error_type == "invalid_prompt":
                    strategy = {"action": "sanitize_prompt", "delay": 0}
                elif error_type == "space_down":
                    strategy = {"action": "retry_with_wait", "delay": 60}
                break
        
        context["recovery_strategy"] = strategy
        return context
    
    def sanitize_prompt(self, prompt: str) -> str:
        """Sanitize potentially problematic prompts"""
        # Remove extreme aspect ratio specifications that cause issues
        prompt = re.sub(r'\b(\d+):(\d+)\b', '', prompt)
        # Clean up multiple spaces
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        return prompt

@dataclass
class DetailMasterAgent(Agent):
    """Optimizes for skin and pore-level detail"""
    
    def __init__(self):
        super().__init__(
            name="Detail Master",
            agent_type=AgentType.DETAIL_MASTER,
            role="Skin/pore realism optimization"
        )
        
        self.detail_keywords = [
            "natural skin texture",
            "visible pores",
            "micro details",
            "subsurface scattering",
            "realistic imperfections",
            "fine wrinkles",
            "skin translucency"
        ]
    
    def process(self, context: Dict) -> Dict:
        """Enhance prompt with detail keywords"""
        prompt = context.get("prompt", "").lower()
        
        # Check if this is a portrait/person image
        if any(kw in prompt for kw in ["portrait", "person", "face", "skin", "woman", "man", "people"]):
            # Add detail keywords not already present
            existing = set(k.lower() for k in prompt.split())
            for keyword in self.detail_keywords:
                if keyword not in existing:
                    context["prompt"] = context["prompt"] + f", {keyword}"
        
        context["applied_detail_config"] = True
        return context

@dataclass
class LightingProAgent(Agent):
    """Cinematic lighting expert"""
    
    def __init__(self):
        super().__init__(
            name="Lighting Pro",
            agent_type=AgentType.LIGHTING_PRO,
            role="Cinematic light setup"
        )
        
        self.lighting_setups = {
            "golden_hour": "golden hour lighting, warm soft light",
            "studio": "professional studio lighting, softbox setup",
            "natural": "natural window light, soft diffused",
            "dramatic": "dramatic chiaroscuro lighting, strong shadows",
            "ambient": "ambient atmospheric lighting, volumetric",
            "rembrandt": "Rembrandt lighting, 45-degree key light"
        }
    
    def process(self, context: Dict) -> Dict:
        """Add lighting to prompt"""
        prompt = context.get("prompt", "").lower()
        
        # Check if lighting is already specified
        has_lighting = any(l in prompt for l in ["lighting", "light", "lit by", "illuminated"])
        
        if not has_lighting:
            # Infer best lighting based on prompt content
            if "cinematic" in prompt or "movie" in prompt:
                lighting = self.lighting_setups["cinematic"]
            elif "portrait" in prompt or "face" in prompt:
                lighting = self.lighting_setups["studio"]
            else:
                lighting = self.lighting_setups["natural"]
            
            context["prompt"] = f"{context['prompt']}, {lighting}"
            context["applied_lighting"] = lighting
        
        return context

@dataclass
class RetryBotAgent(Agent):
    """Auto-retry on failures"""
    
    def __init__(self, max_retries: int = 3):
        super().__init__(
            name="Retry Bot",
            agent_type=AgentType.RETRY_BOT,
            role="Auto-retry errors with backoff"
        )
        self.max_retries = max_retries
        self.retry_delays = [2, 5, 10]  # exponential backoff
    
    def process(self, context: Dict) -> Dict:
        """Calculate retry parameters"""
        current_attempt = context.get("attempt", 0)
        
        if current_attempt < self.max_retries:
            delay = self.retry_delays[min(current_attempt, len(self.retry_delays) - 1)]
            context["should_retry"] = True
            context["retry_delay"] = delay
            context["next_attempt"] = current_attempt + 1
        else:
            context["should_retry"] = False
            context["max_retries_reached"] = True
        
        return context

@dataclass
class PromptEngineerAgent(Agent):
    """Optimizes prompts for better results"""
    
    def __init__(self):
        super().__init__(
            name="Prompt Engineer",
            agent_type=AgentType.PROMPT_ENGINEER,
            role="Optimize prompts for quality"
        )
    
    def process(self, context: Dict) -> Dict:
        """Optimize the prompt structure"""
        prompt = context.get("prompt", "")
        
        # Clean up formatting
        prompt = prompt.strip()
        
        # Ensure quality keywords are present
        quality_keywords = ["high quality", "detailed", "8K"]
        prompt_lower = prompt.lower()
        
        for kw in quality_keywords:
            if kw not in prompt_lower:
                prompt = f"{kw}, {prompt}"
                prompt_lower = prompt.lower()
        
        # Optimize order: subject, action, setting, quality, style
        # This is a simplified version - full implementation would use NLP
        context["prompt"] = prompt
        context["prompt_optimized"] = True
        
        return context

class AgentNetwork:
    """
    Microsoft AgentGen-inspired Agent Network
    Orchestrates multiple agents for complex tasks
    """
    
    def __init__(self):
        self.agents: Dict[AgentType, Agent] = {}
        self.active_agents: List[AgentType] = []
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Register all available agents"""
        self.agents[AgentType.KLING_EXPERT] = KlingExpertAgent()
        self.agents[AgentType.ERROR_HANDLER] = ErrorHandlerAgent()
        self.agents[AgentType.DETAIL_MASTER] = DetailMasterAgent()
        self.agents[AgentType.LIGHTING_PRO] = LightingProAgent()
        self.agents[AgentType.RETRY_BOT] = RetryBotAgent()
        self.agents[AgentType.PROMPT_ENGINEER] = PromptEngineerAgent()
    
    def activate_agent(self, agent_type: AgentType):
        """Activate an agent"""
        if agent_type in self.agents and agent_type not in self.active_agents:
            self.active_agents.append(agent_type)
    
    def deactivate_agent(self, agent_type: AgentType):
        """Deactivate an agent"""
        if agent_type in self.active_agents:
            self.active_agents.remove(agent_type)
    
    def set_active_agents(self, agent_types: List[AgentType]):
        """Set multiple active agents"""
        self.active_agents = agent_types
    
    def process(self, context: Dict) -> Dict:
        """Run context through all active agents"""
        for agent_type in self.active_agents:
            agent = self.agents.get(agent_type)
            if agent and agent.active:
                context = agent.process(context)
        return context
    
    def process_error(self, error: str, context: Dict = None) -> Dict:
        """Process error with error handler agent"""
        ctx = context or {}
        ctx["error"] = error
        
        error_handler = self.agents.get(AgentType.ERROR_HANDLER)
        if error_handler:
            return error_handler.process(ctx)
        
        return ctx
    
    def should_retry(self, error: str, attempt: int) -> tuple[bool, int]:
        """Determine if should retry based on error and attempt count"""
        retry_bot = self.agents.get(AgentType.RETRY_BOT)
        if retry_bot and AgentType.RETRY_BOT in self.active_agents:
            ctx = retry_bot.process({"attempt": attempt})
            return ctx.get("should_retry", False), ctx.get("retry_delay", 5)
        return False, 0

# Global agent network instance
agent_network = AgentNetwork()

def apply_agentic_enhancement(prompt: str, settings: Dict, active_agents: List[str]) -> Dict:
    """
    Apply all active agents to enhance generation request
    
    Args:
        prompt: User prompt
        settings: Generation settings
        active_agents: List of agent names (e.g., ['kling', 'detail', 'light'])
    
    Returns:
        Enhanced context with modifications from all agents
    """
    # Map agent names to types
    agent_map = {
        "kling": AgentType.KLING_EXPERT,
        "error": AgentType.ERROR_HANDLER,
        "detail": AgentType.DETAIL_MASTER,
        "light": AgentType.LIGHTING_PRO,
        "retry": AgentType.RETRY_BOT,
        "prompt": AgentType.PROMPT_ENGINEER
    }
    
    # Set active agents
    agent_types = [agent_map.get(a) for a in active_agents if a in agent_map]
    agent_types = [a for a in agent_types if a is not None]
    agent_network.set_active_agents(agent_types)
    
    # Create context
    context = {
        "prompt": prompt,
        "settings": settings,
        "applied_agents": []
    }
    
    # Process through agents
    result = agent_network.process(context)
    result["applied_agents"] = active_agents
    
    return result

# Export
__all__ = [
    'AgentNetwork',
    'Agent',
    'AgentType',
    'KlingExpertAgent',
    'ErrorHandlerAgent',
    'DetailMasterAgent',
    'LightingProAgent',
    'RetryBotAgent',
    'PromptEngineerAgent',
    'apply_agentic_enhancement',
    'agent_network'
]
