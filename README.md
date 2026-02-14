# EDEN UI REALISM ENGINE

**EDEN UI REALISM ENGINE** is a comprehensive diffusion model fine-tuner built for maximum human photorealism. Import any model from HuggingFace and generate stunning, realistic images and videos with advanced controls.

![EDEN UI](https://img.shields.io/badge/EDEN-REALISM%20ENGINE-00d4aa?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-00d4aa?style=for-the-badge)

## Features

### Core Capabilities
- **HuggingFace Integration** - Import any diffusion model from HuggingFace Hub
- **Natural Language Chat** - AI-powered assistant for prompt engineering
- **Drag & Drop Support** - Easy image/video upload for processing
- **Real-time Preview** - See generations as they happen

### Generation Modes
- **Text to Image** - Create photorealistic images from descriptions
- **Text to Video** - Generate cinematic videos with temporal consistency
- **Image to Video** - Animate static images with motion controls
- **Video to Video** - Transform and enhance existing videos

### EDEN Special Features

#### Comprehensive Negative Keywords
EDEN includes an extensive negative keyword system targeting AI artifacts:
- **Skin Quality** - Prevents plastic, airbrushed, poreless skin
- **Facial Features** - Avoids dead eyes, wax figure appearance, uncanny valley
- **Body Anatomy** - Prevents impossible proportions, anime characteristics
- **Video Artifacts** - Eliminates flickering, morphing, temporal inconsistencies
- **Contact Physics** - Realistic body interaction rendering
- **Movement** - Natural motion without robotic/jerky qualities

#### Model Mimicry
Settings optimized to replicate models like **Kling** for maximum human realness:
- Specialized CFG scales and schedulers
- Aspect ratio recommendations
- Negative prompt combinations

#### Playground & ComfyUI Integration
- Seamless ComfyUI workflow support
- Enhancement module search and integration
- Model merging and distillation tools

## Architecture

```
eden-ui-realism-engine/
├── backend/              # FastAPI backend
│   ├── main.py          # Main application
│   ├── config.py        # Configuration & EDEN keywords
│   ├── database.py      # SQLAlchemy models
│   ├── model_manager.py # HuggingFace integration
│   ├── generation_engine.py  # Image/Video generation
│   └── chat_engine.py   # Natural language AI
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Zustand store
│   │   └── services/    # API client
│   └── public/
├── models/              # Downloaded models (auto-created)
├── outputs/             # Generated content (auto-created)
└── uploads/             # User uploads (auto-created)
```

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- CUDA-capable GPU (recommended)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will start on `http://localhost:3000`

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# HuggingFace
HF_TOKEN=your_huggingface_token

# AI/LLM APIs (optional but recommended)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Paths
COMFYUI_PATH=/path/to/comfyui

# Development
DEBUG=false
```

## Usage

### 1. Import Models
- Go to **MODELS** tab
- Search for models on HuggingFace (e.g., "stabilityai/stable-diffusion-xl-base-1.0")
- Click download to cache locally

### 2. Generate Images
- Click **EDEN IMAGES** tab
- Enter your prompt in natural language
- Select a preset (Kling-style, Photorealistic, Fast Preview)
- Adjust settings (CFG, steps, resolution)
- Click Generate

### 3. Generate Videos
- Click **EDEN VIDEOS** tab
- Choose Text-to-Video or Image-to-Video
- Set duration and FPS
- Enable EDEN negative for temporal consistency
- Generate

### 4. Chat with EDEN
- Use the left sidebar to chat with the AI assistant
- Type `/enhance [prompt]` to improve prompts
- Type `/negative` to see negative keywords
- Drag & drop images for analysis

### 5. Playground (ComfyUI)
- Click **PLAYGROUND** tab
- Launch ComfyUI for node-based workflows
- Search and add enhancement modules

## EDEN Negative Keywords Reference

EDEN uses 200+ negative keywords organized into categories:

### Base Keywords
```
deformed face, asymmetric eyes, extra fingers, mutated hands,
blurry eyes, cartoon, 3D render, drawing, sketch, lowres...
```

### Skin Quality
```
plastic skin, waxy skin, airbrushed skin, poreless skin,
silicone skin, rubber skin, frequency separation artifact...
```

### Facial Features
```
dead eyes, glazed eyes, uncanny valley, wax figure,
mannequin, perfect symmetry, doll-like...
```

### Video-Specific
```
flickering, frame jitter, motion warp, morphing faces,
identity shift, temporal flicker, lip sync desync...
```

See all keywords in the Settings tab or use `/negative` in chat.

## API Endpoints

### Generation
- `POST /api/generate/image` - Generate image
- `POST /api/generate/video` - Generate video
- `POST /api/generate/image-to-video` - Animate image

### Models
- `GET /api/models/search` - Search HuggingFace
- `POST /api/models/download` - Download model
- `GET /api/models/downloaded` - List local models

### Chat
- `POST /api/chat` - Send message
- `WS /api/chat/ws/{session_id}` - WebSocket chat

### EDEN Config
- `GET /api/eden/negative-keywords` - Get negative keywords
- `GET /api/eden/presets` - Get model presets
- `GET /api/eden/enhancements` - Get enhancement modules

## Development

### Adding New Enhancement Modules

Edit `backend/config.py`:

```python
EDEN_ENHANCEMENTS = {
    "your_module": {
        "name": "Your Module",
        "description": "What it does",
        "models": ["model1", "model2"],
    }
}
```

### Custom Presets

```python
EDEN_MODEL_PRESETS = {
    "your_preset": {
        "name": "Your Preset",
        "description": "Description",
        "guidance_scale": 7.5,
        "num_inference_steps": 30,
        "scheduler": "DPM++ 2M Karras",
    }
}
```

## GPU Optimization

For best performance:
- Use CUDA 12.1+
- Enable xFormers: `pip install xformers`
- Use mixed precision (fp16/bf16)
- Enable VAE slicing for large images

## Troubleshooting

### Out of Memory
- Reduce image resolution
- Lower batch size
- Enable model CPU offloading
- Clear cache: Settings > System > Unload Models

### Slow Generation
- Use Turbo models (SD Turbo, Lightning)
- Reduce inference steps (20-30)
- Use faster samplers (Euler, DPM++ 2M)

### Poor Quality
- Increase steps (40-50)
- Raise CFG scale (7-9)
- Use EDEN's full negative keywords
- Try different schedulers

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- HuggingFace Diffusers team
- ComfyUI contributors
- The open-source AI community

---

Built with ❤️ for photorealistic AI generation.
