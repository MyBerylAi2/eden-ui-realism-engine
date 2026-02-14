# EDEN Realism Engine - V5 AGENTIC TEAMS

## Quick Start

```bash
# Terminal 1: Start backend
cd backend && python3 main.py

# Terminal 2: Start frontend V5
python3 serve_v5.py
```

**URLs:**
- Frontend: http://localhost:3007
- Backend: http://localhost:8000

## V5 Features

### 1. Toast Notifications
- **Error toast** when generation fails with detailed message
- **Success toast** when content generates
- **Info toast** for system status
- **Warning toast** for retries

### 2. GPU Scaling (Functional!)
- Click **"⚡ SCALE GPU"** button in header
- Modal opens with GPU options:
  - Zero GPU (Free) - $0/hr
  - NVIDIA T4 - $0.45/hr
  - NVIDIA L4 - $0.80/hr
  - NVIDIA A10G - $1.20/hr
  - NVIDIA A100 - $4.50/hr
- Click **"APPLY GPU UPGRADE"** to scale

### 3. Agentic Teams (Microsoft AgentGen/Agent Network)

**Available Agents:**
- 👑 **Kling Expert** - Photorealism config (default ON)
- 🛡️ **Error Handler** - Auto-fix failures
- 🔍 **Detail Master** - Skin/pore realism
- 💡 **Lighting Pro** - Cinematic light
- 🔄 **Retry Bot** - Auto-retry errors (max 3 attempts)
- ✨ **Prompt Engineer** - Optimize prompts

**How it works:**
1. Click agents to activate/deactivate
2. Agents automatically enhance prompts
3. Error agents catch failures and suggest fixes
4. Retry bot auto-retries with backoff

## File Structure

```
eden-ui-realism-engine/
├── frontend_v5/
│   └── index.html          # V5 UI with agents & toasts
├── backend/
│   ├── main.py             # FastAPI with agent integration
│   ├── agentgen_integration.py  # Microsoft AgentGen implementation
│   ├── flux_engine.py      # FLUX, Wan2.1 generation
│   └── hf_gpu_manager.py   # GPU scaling
└── serve_v5.py             # Frontend server
```

## GitHub

```bash
git add .
git commit -m "V5: Agentic Teams, Toast Notifications, GPU Scaling"
git tag v5.0
git push origin v5.0
```

## Storage

**Seagate Drive:** `/media/letsgo/9361ec48-323e-44ae-84d5-9060ae68b5751/PINOKIO`
- Models cached via HF_HOME redirection
- BERYL_BUCKET for film projects
