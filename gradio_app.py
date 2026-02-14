"""
EDEN UI REALISM ENGINE - Gradio Interface
==========================================
Complete Gradio UI with FLUX image generation, video generation, and Seagate integration.
"""
import os
import sys
import time
import gradio as gr
from pathlib import Path
from typing import Optional, Tuple, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from config import (
    get_settings, IMAGE_MODELS, IMAGE_RESOLUTIONS, ENHANCE_MODELS,
    VIDEO_MODELS, EDEN_MODEL_PRESETS, get_eden_negative_prompt,
    inject_flux_negative, SEAGATE, USING_SEAGATE
)
from flux_engine import (
    generate_image_fast, enhance_image_realism, generate_3d_trellis,
    generate_video_wan21, scan_seagate_model_library, pull_huggingface_model,
    pull_ollama_model, pull_pinokio_app, OUTPUT_DIR
)

settings = get_settings()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def update_img_model_defaults(model_name: str) -> Tuple[int, float]:
    """Update steps and guidance defaults based on selected model."""
    model = IMAGE_MODELS.get(model_name, IMAGE_MODELS["flux-schnell"])
    return model["steps"], model["guidance"]


def generate_image_with_enhance(
    prompt: str,
    model_name: str,
    resolution: str,
    steps: int,
    guidance: float,
    seed: int,
    negative_prompt: str,
    enhance_model: str,
    enhance_strength: float,
    reference_image: Optional[str],
    reference_strength: float,
    hf_token: str
) -> Tuple[str, str]:
    """
    Generate image with optional reference injection and post-enhancement.
    """
    # Inject reference if provided
    full_prompt = prompt
    if reference_image and reference_strength > 0:
        ref_hint = f" Maintain face consistency with reference image (strength: {reference_strength:.1f})."
        full_prompt = prompt + ref_hint
    
    # Generate image
    image_path, status = generate_image_fast(
        prompt=full_prompt,
        model_name=model_name,
        resolution=resolution,
        steps=steps,
        guidance=guidance,
        seed=seed,
        negative_prompt=negative_prompt,
        hf_token=hf_token if hf_token else settings.HF_TOKEN
    )
    
    if not image_path:
        return None, status
    
    # Auto-enhance if selected
    if enhance_model != "none":
        image_path, enhance_status = enhance_image_realism(
            image_path=image_path,
            enhance_model=enhance_model,
            strength=enhance_strength,
            hf_token=hf_token if hf_token else settings.HF_TOKEN
        )
        status += f" | {enhance_status}"
    
    return image_path, status


def update_smart_negative(prompt: str, preset: str) -> str:
    """Auto-generate smart negative based on prompt and preset."""
    if preset == "kling_reference":
        negatives = get_eden_negative_prompt("all")
    elif preset == "photorealistic":
        negatives = get_eden_negative_prompt("all")
    elif preset == "fast_preview":
        negatives = get_eden_negative_prompt("base")
    else:
        negatives = get_eden_negative_prompt("all")
    
    # Add prompt-specific negatives
    prompt_lower = prompt.lower()
    if "face" in prompt_lower or "portrait" in prompt_lower:
        negatives += ", " + get_eden_negative_prompt("facial_features")
    if "video" in prompt_lower or "animation" in prompt_lower:
        negatives += ", " + get_eden_negative_prompt("video_artifacts")
    
    return negatives


def calculate_effective_cfg(cfg_high: float, cfg_low: float) -> str:
    """Calculate effective CFG score."""
    effective = cfg_high * 0.6 + cfg_low * 0.4
    return f"Effective CFG: {effective:.2f} (60% high-noise + 40% low-noise)"


def refresh_seagate_library() -> Tuple[List[List[str]], str]:
    """Scan and refresh Seagate model library."""
    models = scan_seagate_model_library()
    return models, f"Found {len(models)} models on Seagate"


def pull_model_wrapper(source: str, model_id: str, category: str, hf_token: str) -> str:
    """Wrapper for pulling models from various sources."""
    token = hf_token if hf_token else settings.HF_TOKEN
    
    if source == "huggingface":
        return pull_huggingface_model(model_id, category, token)
    elif source == "ollama":
        return pull_ollama_model(model_id)
    elif source == "pinokio":
        return pull_pinokio_app(model_id)
    else:
        return "❌ Unknown source"


# =============================================================================
# GRADIO UI CONSTRUCTION
# =============================================================================

def create_ui() -> gr.Blocks:
    """Create the complete Gradio UI."""
    
    with gr.Blocks(
        title="EDEN UI REALISM ENGINE"
    ) as app:
        
        # Header
        gr.Markdown("""
        <div class="eden-header">
        <h1>🌟 EDEN UI REALISM ENGINE</h1>
        <p>Maximum Human Realism | FLUX Image Generation | Wan2.1 Video | Seagate Storage</p>
        </div>
        """)
        
        # Status bar
        with gr.Row():
            seagate_status = gr.Textbox(
                value=f"✅ Seagate Connected: {USING_SEAGATE} | Path: {SEAGATE}",
                label="Storage Status",
                interactive=False
            )
            hf_token_input = gr.Textbox(
                label="HuggingFace Token",
                type="password",
                value=settings.HF_TOKEN or "",
                placeholder="hf_..."
            )
        
        # Main Tabs
        with gr.Tabs() as main_tabs:
            
            # =========================================================================
            # TAB 1: GENERATE (Images + Videos + My Models)
            # =========================================================================
            with gr.Tab("🎨 Generate", id="generate"):
                
                # Shared Toolbar
                with gr.Row():
                    preset_select = gr.Dropdown(
                        choices=["kling_reference", "photorealistic", "cinematic_video", "fast_preview"],
                        value="kling_reference",
                        label="🎭 Preset"
                    )
                    enhance_btn = gr.Button("✨ Enhance Realism", variant="secondary")
                    generate_3d_btn = gr.Button("🧊 Generate 3D", variant="secondary")
                
                # Shared Playground (Prompt + Output)
                with gr.Row():
                    # Left: Prompt Input
                    with gr.Column(scale=1):
                        prompt_input = gr.Textbox(
                            label="📝 Prompt",
                            placeholder="Describe your image or video...",
                            lines=4
                        )
                        
                        with gr.Accordion("🔒 Reference Lock", open=False):
                            reference_image = gr.Image(
                                label="Reference Image (for face consistency)",
                                type="filepath"
                            )
                            reference_strength = gr.Slider(
                                0.0, 1.0, value=0.5,
                                label="Reference Strength"
                            )
                        
                        # Smart Negatives (shared)
                        with gr.Accordion("⚡ Smart Negative Engine", open=True):
                            negative_output = gr.Textbox(
                                label="Auto-Generated Negatives",
                                lines=3,
                                interactive=True
                            )
                            regenerate_neg_btn = gr.Button("🔄 Regenerate Negatives")
                    
                    # Right: Output Panel
                    with gr.Column(scale=1):
                        image_output = gr.Image(
                            label="Generated Image",
                            type="filepath",
                            visible=True,
                            elem_classes=["output-image"]
                        )
                        video_output = gr.Video(
                            label="Generated Video",
                            visible=False
                        )
                        
                        with gr.Row():
                            enhance_image_btn = gr.Button("✨ Enhance Image")
                            gen_3d_from_img = gr.Button("🧊 Make 3D")
                        
                        status_output = gr.Textbox(
                            label="Status",
                            interactive=False
                        )
                
                # Sub-tabs for Image/Video/Models
                with gr.Tabs():
                    
                    # ---------------------------------------------------------------
                    # EDEN IMAGES Sub-Tab
                    # ---------------------------------------------------------------
                    with gr.Tab("🖼️ EDEN IMAGES"):
                        with gr.Row():
                            with gr.Column():
                                img_model_dd = gr.Dropdown(
                                    choices=list(IMAGE_MODELS.keys()),
                                    value="flux-schnell",
                                    label="AI Model"
                                )
                                img_resolution = gr.Dropdown(
                                    choices=list(IMAGE_RESOLUTIONS.keys()),
                                    value="1024 x 1024 (Square - FLUX Native)",
                                    label="Resolution"
                                )
                            
                            with gr.Column():
                                img_steps = gr.Slider(
                                    1, 50, value=4, step=1,
                                    label="Steps"
                                )
                                img_guidance = gr.Slider(
                                    1.0, 20.0, value=3.5, step=0.5,
                                    label="Guidance Scale"
                                )
                                img_seed = gr.Number(
                                    value=-1, label="Seed (-1 = random)"
                                )
                        
                        with gr.Row():
                            with gr.Column():
                                enhance_model_dd = gr.Dropdown(
                                    choices=list(ENHANCE_MODELS.keys()),
                                    value="none",
                                    label="Post-Gen Enhance"
                                )
                                enhance_strength = gr.Slider(
                                    0.0, 1.0, value=0.25,
                                    label="Enhance Strength"
                                )
                        
                        generate_img_btn = gr.Button(
                            "🚀 Generate Image",
                            variant="primary",
                            size="lg"
                        )
                    
                    # ---------------------------------------------------------------
                    # EDEN VIDEOS Sub-Tab
                    # ---------------------------------------------------------------
                    with gr.Tab("🎬 EDEN VIDEOS"):
                        with gr.Row():
                            with gr.Column():
                                video_model = gr.Dropdown(
                                    choices=list(VIDEO_MODELS.keys()),
                                    value="wan-t2v-1.3b",
                                    label="Video Model"
                                )
                                video_duration = gr.Slider(
                                    1, 5, value=2, step=1,
                                    label="Duration (seconds)"
                                )
                            
                            with gr.Column():
                                video_height = gr.Dropdown(
                                    choices=[256, 480, 512, 720, 832],
                                    value=480,
                                    label="Height"
                                )
                                video_width = gr.Dropdown(
                                    choices=[256, 480, 512, 720, 832],
                                    value=832,
                                    label="Width"
                                )
                                video_fps = gr.Slider(
                                    16, 30, value=24, step=1,
                                    label="FPS"
                                )
                        
                        # Dual-Phase CFG
                        gr.Markdown("### Dual-Phase CFG (for advanced control)")
                        with gr.Row():
                            cfg_high = gr.Slider(
                                1.0, 15.0, value=6.5, step=0.5,
                                label="CFG High-Noise (Composition)"
                            )
                            cfg_low = gr.Slider(
                                1.0, 10.0, value=4.0, step=0.5,
                                label="CFG Low-Noise (Detail)"
                            )
                        
                        effective_cfg_display = gr.Textbox(
                            value="Effective CFG: 5.50 (60% high-noise + 40% low-noise)",
                            label="Effective CFG",
                            interactive=False
                        )
                        
                        with gr.Row():
                            generate_video_private = gr.Button(
                                "🚀 Generate (Private GPU)",
                                variant="primary"
                            )
                            generate_video_free = gr.Button(
                                "🆓 Generate (Free Queue)",
                                variant="secondary"
                            )
                    
                    # ---------------------------------------------------------------
                    # MY MODELS Sub-Tab
                    # ---------------------------------------------------------------
                    with gr.Tab("💾 My Models"):
                        with gr.Row():
                            scan_btn = gr.Button("🔍 Scan Seagate Library")
                            refresh_models_btn = gr.Button("🔄 Refresh")
                        
                        models_df = gr.Dataframe(
                            headers=["Category", "Name", "Size", "Path"],
                            label="Seagate Model Library",
                            interactive=False
                        )
                        
                        scan_status = gr.Textbox(label="Scan Status", interactive=False)
                        
                        gr.Markdown("---")
                        gr.Markdown("### ⬇️ Pull New Model")
                        
                        with gr.Row():
                            pull_source = gr.Dropdown(
                                choices=["huggingface", "ollama", "pinokio"],
                                value="huggingface",
                                label="Source"
                            )
                            pull_category = gr.Dropdown(
                                choices=["checkpoints", "loras", "vae", "upscalers", 
                                        "embeddings", "controlnet", "t2i_adapter"],
                                value="checkpoints",
                                label="Category (HF only)"
                            )
                        
                        pull_model_id = gr.Textbox(
                            label="Model ID / Git URL",
                            placeholder="org/model-name or https://github.com/..."
                        )
                        
                        pull_btn = gr.Button("⬇️ Pull Model", variant="primary")
                        pull_status = gr.Textbox(label="Pull Status", interactive=False)
            
            # =========================================================================
            # TAB 2: GPU SCALING
            # =========================================================================
            with gr.Tab("⚡ GPU Scaling"):
                gr.Markdown("## HuggingFace GPU Scaling")
                
                with gr.Row():
                    with gr.Column():
                        space_id = gr.Textbox(
                            label="Space ID",
                            placeholder="username/space-name"
                        )
                        gpu_tier = gr.Dropdown(
                            choices=["zero", "t4-small", "t4-medium", "a10g-small", "a10g-large", "a100-large"],
                            value="t4-small",
                            label="GPU Tier"
                        )
                        sleep_minutes = gr.Slider(
                            5, 120, value=30, step=5,
                            label="Auto-Sleep After (minutes)"
                        )
                        
                        with gr.Row():
                            upgrade_btn = gr.Button("⬆️ Upgrade GPU", variant="primary")
                            downgrade_btn = gr.Button("⬇️ Downgrade to Zero", variant="secondary")
                    
                    with gr.Column():
                        gpu_status = gr.Textbox(
                            label="GPU Status",
                            lines=5,
                            interactive=False
                        )
                        extend_sleep_btn = gr.Button("⏱️ Extend Sleep Timer")
                        extend_minutes = gr.Slider(
                            5, 60, value=15, step=5,
                            label="Additional Minutes"
                        )
            
            # =========================================================================
            # TAB 3: SETTINGS
            # =========================================================================
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("## EDEN UI Settings")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Storage")
                        gr.Textbox(
                            value=str(SEAGATE),
                            label="Seagate Path",
                            interactive=False
                        )
                        gr.Textbox(
                            value=str(settings.HF_HOME),
                            label="HF Cache",
                            interactive=False
                        )
                    
                    with gr.Column():
                        gr.Markdown("### API Keys")
                        settings_hf_token = gr.Textbox(
                            label="HuggingFace Token",
                            type="password",
                            value=settings.HF_TOKEN or ""
                        )
                        settings_openai = gr.Textbox(
                            label="OpenAI API Key",
                            type="password",
                            value=settings.OPENAI_API_KEY or ""
                        )
                        save_settings_btn = gr.Button("💾 Save Settings")
        
        # =============================================================================
        # EVENT WIRING
        # =============================================================================
        
        # Image generation
        generate_img_btn.click(
            fn=generate_image_with_enhance,
            inputs=[
                prompt_input, img_model_dd, img_resolution,
                img_steps, img_guidance, img_seed, negative_output,
                enhance_model_dd, enhance_strength,
                reference_image, reference_strength, hf_token_input
            ],
            outputs=[image_output, status_output]
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=image_output
        ).then(
            fn=lambda: gr.update(visible=False),
            outputs=video_output
        )
        
        # Video generation - Private GPU
        generate_video_private.click(
            fn=lambda prompt, model, w, h, duration, fps, cfg_h, cfg_l, seed, token: generate_video_wan21(
                prompt=prompt,
                model_name=model,
                width=w,
                height=h,
                num_frames=int(duration * fps),
                fps=fps,
                cfg_high=cfg_h,
                cfg_low=cfg_l,
                seed=seed,
                use_private=True,
                hf_token=token if token else settings.HF_TOKEN
            ),
            inputs=[prompt_input, video_model, video_width, video_height, 
                    video_duration, video_fps, cfg_high, cfg_low, img_seed, hf_token_input],
            outputs=[video_output, status_output]
        ).then(
            fn=lambda: gr.update(visible=False),
            outputs=image_output
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=video_output
        )
        
        # Video generation - Free Queue
        generate_video_free.click(
            fn=lambda prompt, model, w, h, duration, fps, cfg_h, cfg_l, seed, token: generate_video_wan21(
                prompt=prompt,
                model_name=model,
                width=w,
                height=h,
                num_frames=int(duration * fps),
                fps=fps,
                cfg_high=cfg_h,
                cfg_low=cfg_l,
                seed=seed,
                use_private=False,
                hf_token=token if token else settings.HF_TOKEN
            ),
            inputs=[prompt_input, video_model, video_width, video_height,
                    video_duration, video_fps, cfg_high, cfg_low, img_seed, hf_token_input],
            outputs=[video_output, status_output]
        ).then(
            fn=lambda: gr.update(visible=False),
            outputs=image_output
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=video_output
        )
        
        # Model defaults update
        img_model_dd.change(
            fn=update_img_model_defaults,
            inputs=[img_model_dd],
            outputs=[img_steps, img_guidance]
        )
        
        # Smart negative generation
        def on_prompt_change(prompt, preset):
            return update_smart_negative(prompt, preset)
        
        prompt_input.change(
            fn=on_prompt_change,
            inputs=[prompt_input, preset_select],
            outputs=[negative_output]
        )
        
        preset_select.change(
            fn=on_prompt_change,
            inputs=[prompt_input, preset_select],
            outputs=[negative_output]
        )
        
        regenerate_neg_btn.click(
            fn=on_prompt_change,
            inputs=[prompt_input, preset_select],
            outputs=[negative_output]
        )
        
        # CFG calculation
        def update_cfg_display(high, low):
            effective = high * 0.6 + low * 0.4
            return f"Effective CFG: {effective:.2f} (60% high-noise + 40% low-noise)"
        
        cfg_high.change(
            fn=update_cfg_display,
            inputs=[cfg_high, cfg_low],
            outputs=[effective_cfg_display]
        )
        
        cfg_low.change(
            fn=update_cfg_display,
            inputs=[cfg_high, cfg_low],
            outputs=[effective_cfg_display]
        )
        
        # Seagate scanning
        scan_btn.click(
            fn=refresh_seagate_library,
            outputs=[models_df, scan_status]
        )
        
        refresh_models_btn.click(
            fn=refresh_seagate_library,
            outputs=[models_df, scan_status]
        )
        
        # Model pulling
        pull_btn.click(
            fn=pull_model_wrapper,
            inputs=[pull_source, pull_model_id, pull_category, hf_token_input],
            outputs=[pull_status]
        )
        
        # Enhancement
        enhance_image_btn.click(
            fn=lambda img, model, strength, token: enhance_image_realism(
                img, model, strength, token if token else settings.HF_TOKEN
            ),
            inputs=[image_output, enhance_model_dd, enhance_strength, hf_token_input],
            outputs=[image_output, status_output]
        )
        
        # 3D generation
        gen_3d_from_img.click(
            fn=lambda img, token: generate_3d_trellis(
                img, token if token else settings.HF_TOKEN
            ),
            inputs=[image_output, hf_token_input],
            outputs=[gr.File(label="3D Model"), status_output]
        )
        
        # GPU scaling (placeholders for now)
        def upgrade_gpu(space, tier, sleep_mins, token):
            return f"Upgrading {space} to {tier} (auto-sleep: {sleep_mins}m)..."
        
        def downgrade_gpu(space, token):
            return f"Downgrading {space} to Zero GPU..."
        
        upgrade_btn.click(
            fn=upgrade_gpu,
            inputs=[space_id, gpu_tier, sleep_minutes, hf_token_input],
            outputs=[gpu_status]
        )
        
        downgrade_btn.click(
            fn=downgrade_gpu,
            inputs=[space_id, hf_token_input],
            outputs=[gpu_status]
        )
        
    return app


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=0,  # Auto-find available port
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
        css="""
        .eden-header { text-align: center; margin-bottom: 20px; }
        .eden-header h1 { color: #6366f1; font-size: 2.5em; margin-bottom: 5px; }
        .eden-header p { color: #6b7280; font-size: 1.1em; }
        .output-image { max-height: 600px; }
        """
    )
