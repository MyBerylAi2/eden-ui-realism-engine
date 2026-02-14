"""
EDEN UI REALISM ENGINE - Natural Language Chat Engine
=====================================================
AI-powered chat for generating prompts, settings suggestions, and controlling EDEN.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

from config import get_settings, EDEN_NEGATIVE_KEYWORDS, EDEN_MODEL_PRESETS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class ChatContext:
    """Context for chat sessions."""
    session_id: str
    current_model: Optional[str] = None
    current_mode: str = "general"
    conversation_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


class EDENChatEngine:
    """
    EDEN's natural language chat engine for prompt engineering and control.
    """
    
    SYSTEM_PROMPT = """You are EDEN, an expert AI assistant specialized in diffusion models, 
image generation, video generation, and AI art creation. You help users create photorealistic 
content using the EDEN UI REALISM ENGINE.

Your expertise includes:
- Writing effective prompts for photorealistic human generation
- Understanding negative prompts to avoid AI artifacts
- Recommending optimal settings (CFG, steps, samplers)
- Knowledge of model architectures (SD, SDXL, SVD, etc.)
- Video generation techniques and temporal consistency
- Fine-tuning and model merging concepts

When users describe what they want to create:
1. Analyze their description for key visual elements
2. Suggest detailed, optimized prompts
3. Recommend appropriate models and settings
4. Include relevant negative prompts to avoid common AI artifacts
5. Be helpful, creative, and technically accurate

EDEN NEGATIVE KEYWORDS PHILOSOPHY:
The user seeks MAXIMUM HUMAN REALNESS. Always emphasize:
- Natural skin with pores, freckles, imperfections
- Asymmetry (perfect symmetry looks fake)
- Natural lighting and shadows
- Realistic body proportions
- Avoiding "plastic", "airbrushed", "beauty filter" looks
- Avoiding "doll-like", "mannequin", "wax figure" appearances

Keep responses concise but informative."""
    
    def __init__(self):
        self.contexts: Dict[str, ChatContext] = {}
        self.use_openai = bool(settings.OPENAI_API_KEY)
        self.use_anthropic = bool(settings.ANTHROPIC_API_KEY)
        
    def get_or_create_context(self, session_id: str) -> ChatContext:
        """Get existing chat context or create new one."""
        if session_id not in self.contexts:
            self.contexts[session_id] = ChatContext(session_id=session_id)
        return self.contexts[session_id]
    
    async def chat(self, message: str, session_id: str,
                   attachments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process a chat message and generate response."""
        context = self.get_or_create_context(session_id)
        context.conversation_history.append({"role": "user", "content": message})
        
        command_response = self._parse_command(message)
        if command_response:
            return command_response
        
        if self.use_openai:
            response = await self._openai_chat(message, context)
        elif self.use_anthropic:
            response = await self._anthropic_chat(message, context)
        else:
            response = self._local_chat(message, context)
        
        parsed = self._parse_generation_request(response, message)
        context.conversation_history.append({"role": "assistant", "content": response})
        
        return {
            "response": response,
            "suggested_prompt": parsed.get("prompt"),
            "suggested_settings": parsed.get("settings"),
            "attachments": attachments,
            "session_id": session_id
        }
    
    def _parse_command(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse special slash commands."""
        message_lower = message.lower().strip()
        
        if message_lower.startswith("/enhance"):
            prompt = message[8:].strip()
            enhanced = self.enhance_prompt(prompt)
            return {
                "response": f"Enhanced prompt:\n\n{enhanced}",
                "suggested_prompt": enhanced,
                "type": "enhancement"
            }
        
        if message_lower.startswith("/negative"):
            category = message[9:].strip() or "all"
            from config import get_eden_negative_prompt
            negative = get_eden_negative_prompt(category)
            return {
                "response": f"EDEN Negative Keywords ({category}):\n\n{negative[:1000]}...",
                "type": "negative_prompt"
            }
        
        if message_lower.startswith("/preset"):
            preset_name = message[7:].strip()
            if preset_name in EDEN_MODEL_PRESETS:
                preset = EDEN_MODEL_PRESETS[preset_name]
                return {
                    "response": f"Preset: {preset['name']}\n{preset['description']}\n\nSettings: {json.dumps(preset, indent=2)}",
                    "suggested_settings": preset,
                    "type": "preset"
                }
            else:
                presets = ", ".join(EDEN_MODEL_PRESETS.keys())
                return {"response": f"Available presets: {presets}", "type": "preset_list"}
        
        return None
    
    async def _openai_chat(self, message: str, context: ChatContext) -> str:
        """Generate response using OpenAI API."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                *context.conversation_history[-10:]
            ]
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return self._local_chat(message, context)
    
    async def _anthropic_chat(self, message: str, context: ChatContext) -> str:
        """Generate response using Anthropic API."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            
            conversation = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context.conversation_history[-10:]
            ])
            
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.7,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": conversation}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            return self._local_chat(message, context)
    
    def _local_chat(self, message: str, context: ChatContext) -> str:
        """Generate response using local heuristics."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["generate", "create", "make", "draw"]):
            if any(word in message_lower for word in ["image", "picture", "photo"]):
                return self._generate_image_suggestion(message)
            elif any(word in message_lower for word in ["video", "animation", "movie"]):
                return self._generate_video_suggestion(message)
        
        if any(word in message_lower for word in ["model", "checkpoint", "lora"]):
            return self._model_suggestion(message)
        
        if any(word in message_lower for word in ["setting", "cfg", "steps", "guidance"]):
            return self._settings_explanation(message)
        
        return self._default_response(message)
    
    def enhance_prompt(self, prompt: str) -> str:
        """Enhance a basic prompt with EDEN-style photorealistic details."""
        enhanced = prompt.strip()
        if not any(style in enhanced.lower() for style in ["photorealistic", "realistic", "photo"]):
            enhanced += ", photorealistic"
        if "skin" not in enhanced.lower():
            enhanced += ", detailed skin with natural pores"
        if "lighting" not in enhanced.lower():
            enhanced += ", natural lighting"
        enhanced += ", shot on Canon EOS R5, 85mm lens, f/1.8"
        return enhanced
    
    def _generate_image_suggestion(self, message: str) -> str:
        """Generate image creation suggestions."""
        prompt = self._extract_prompt(message)
        enhanced = self.enhance_prompt(prompt)
        
        return f"""I'd be happy to help you create that image!

Prompt:
{enhanced}

Recommended Settings:
- Model: SDXL Base or RealVisXL for photorealism
- Steps: 30-40
- CFG Scale: 7-8
- Sampler: DPM++ 2M Karras
- Resolution: 1024x1024 or 1216x832

Use EDEN's full negative set to avoid AI artifacts."""
    
    def _generate_video_suggestion(self, message: str) -> str:
        """Generate video creation suggestions."""
        prompt = self._extract_prompt(message)
        return f"""Let's create that video!

Prompt:
{prompt}, smooth motion, cinematic lighting, 24fps quality

Recommended Settings:
- Model: Wan2.1-T2V or SVD for image-to-video
- Steps: 25-30
- CFG Scale: 6-7
- Frames: 16-25 (longer with merging)
- FPS: 8-24

For longer videos: Generate multiple clips and use EDEN's merging feature.

Negative: Include temporal flicker, morphing, and identity shift keywords."""
    
    def _model_suggestion(self, message: str) -> str:
        """Suggest appropriate models."""
        return """Recommended Models for EDEN:

Photorealistic Images:
- stabilityai/stable-diffusion-xl-base-1.0 - Best base model
- SG161222/RealVisXL_V4.0 - Specialized for realism
- RunDiffusion/Juggernaut-XL-v9 - Great details

Video Generation:
- Wan-AI/Wan2.1-T2V-1.3B - Efficient T2V
- stabilityai/stable-video-diffusion-img2vid-xt - Image to video

Import any model from HuggingFace using the Model Manager!"""
    
    def _settings_explanation(self, message: str) -> str:
        """Explain generation settings."""
        return """EDEN Settings Guide:

CFG Scale (Guidance):
- 5-7: More creative, natural results
- 7-9: Balanced (recommended for realism)
- 10-15: Strict prompt adherence (may look artificial)

Steps:
- 20-30: Fast preview
- 30-50: Quality generation
- 50+: Maximum detail

Sampler:
- DPM++ 2M Karras: Best quality/speed balance
- Euler a: Good for artistic styles
- DDIM: Fast, fewer steps needed"""
    
    def _default_response(self, message: str) -> str:
        """Default helpful response."""
        return """I can help you with:

Image Generation - Describe what you want to create
Video Generation - Animate your ideas
Model Management - Import from HuggingFace
Fine-tuning - Train custom models
Prompt Engineering - Use /enhance [prompt]

What would you like to create today? You can also drag & drop images!"""
    
    def _extract_prompt(self, message: str) -> str:
        """Extract the creative prompt from user message."""
        command_words = ["generate", "create", "make", "draw", "render",
                        "an image of", "a picture of", "a video of", "an animation of"]
        prompt = message
        for word in command_words:
            prompt = re.sub(word, "", prompt, flags=re.IGNORECASE)
        return prompt.strip().strip(".,!?")
    
    def _parse_generation_request(self, response: str, original_message: str) -> Dict[str, Any]:
        """Parse response for automatic generation parameters."""
        result = {"prompt": None, "settings": None}
        
        prompt_match = re.search(r'[Pp]rompt:\s*\n(.*?)(?:\n\n|\Z)', response, re.DOTALL)
        if prompt_match:
            result["prompt"] = prompt_match.group(1).strip()
        
        settings = {}
        if "Steps:" in response:
            steps_match = re.search(r'Steps:\s*(\d+)', response)
            if steps_match:
                settings["num_inference_steps"] = int(steps_match.group(1))
        
        if "CFG" in response or "Guidance" in response:
            cfg_match = re.search(r'(?:CFG|Guidance).*?(\d+(?:\.\d+)?)', response)
            if cfg_match:
                settings["guidance_scale"] = float(cfg_match.group(1))
        
        if settings:
            result["settings"] = settings
        
        return result


chat_engine = EDENChatEngine()
