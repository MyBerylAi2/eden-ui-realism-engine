/**
 * EDEN UI REALISM ENGINE - EDEN IMAGES Tab
 * ========================================
 * Image generation settings optimized for photorealism.
 */
import React, { useState } from 'react';
import { 
  Wand2, Settings, RefreshCw, Image as ImageIcon, 
  Sliders, Sparkles, Download, AlertTriangle 
} from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../hooks/useStore';
import { generateImage, getPresets } from '../services/api';

const EDENImagesTab = () => {
  const {
    imageSettings,
    setImageSettings,
    currentModel,
    setGenerating,
    setGenerationProgress,
    setLastGeneration,
    addToHistory,
    systemStatus,
  } = useStore();

  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    if (!systemStatus?.gpu?.available) {
      toast.error('GPU not available. Check system status.');
      return;
    }

    setIsGenerating(true);
    setGenerating(true);
    setGenerationProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setGenerationProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 15;
      });
    }, 1000);

    try {
      const response = await generateImage({
        prompt,
        model_id: currentModel,
        negative_prompt: negativePrompt || undefined,
        width: imageSettings.width,
        height: imageSettings.height,
        num_inference_steps: imageSettings.steps,
        guidance_scale: imageSettings.guidanceScale,
        seed: imageSettings.seed === -1 ? undefined : imageSettings.seed,
        scheduler: imageSettings.scheduler,
        use_eden_negative: imageSettings.useEdenNegative,
      });

      clearInterval(progressInterval);
      setGenerationProgress(100);

      if (response.data.success) {
        setLastGeneration(response.data);
        addToHistory(response.data);
        toast.success('Image generated successfully!');
      } else {
        throw new Error(response.data.error || 'Generation failed');
      }
    } catch (error) {
      clearInterval(progressInterval);
      toast.error(error.message || 'Failed to generate image');
      console.error(error);
    } finally {
      setIsGenerating(false);
      setGenerating(false);
    }
  };

  const applyPreset = async (presetName) => {
    try {
      const response = await getPresets();
      const preset = response.data.presets[presetName];
      if (preset) {
        setImageSettings({
          steps: preset.num_inference_steps || 30,
          guidanceScale: preset.guidance_scale || 7.5,
          scheduler: preset.scheduler || 'DPM++ 2M Karras',
        });
        toast.success(`Applied ${preset.name} preset`);
      }
    } catch (error) {
      console.error('Failed to load preset:', error);
    }
  };

  const imagePresets = [
    { name: 'photorealistic', label: 'Photorealistic', desc: 'Maximum detail' },
    { name: 'kling_reference', label: 'Kling Style', desc: 'Human realness' },
    { name: 'fast_preview', label: 'Fast Preview', desc: 'Quick iteration' },
  ];

  const schedulers = [
    'DPM++ 2M Karras',
    'DPM++ 2M',
    'Euler a',
    'Euler',
    'DDIM',
    'LMS',
    'Heun',
  ];

  const resolutions = [
    { label: 'Square (1:1)', width: 1024, height: 1024 },
    { label: 'Portrait (3:4)', width: 768, height: 1024 },
    { label: 'Portrait (9:16)', width: 576, height: 1024 },
    { label: 'Landscape (4:3)', width: 1024, height: 768 },
    { label: 'Landscape (16:9)', width: 1024, height: 576 },
    { label: 'Cinematic (21:9)', width: 1280, height: 548 },
  ];

  return (
    <div className="space-y-6">
      {/* Presets */}
      <div>
        <label className="text-sm font-medium text-[#a0a0b0] mb-2 block">
          Quick Presets
        </label>
        <div className="grid grid-cols-3 gap-2">
          {imagePresets.map((preset) => (
            <button
              key={preset.name}
              onClick={() => applyPreset(preset.name)}
              className="p-3 rounded-lg bg-[#1a1a25] border border-[#2a2a3a] hover:border-[#00d4aa] transition-all text-left"
            >
              <Sparkles className="w-4 h-4 text-[#00d4aa] mb-1" />
              <p className="text-sm font-medium">{preset.label}</p>
              <p className="text-xs text-[#a0a0b0]">{preset.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Prompt Inputs */}
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-[#a0a0b0] mb-1 block">
            Prompt
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to create..."
            className="input-eden min-h-[80px] resize-none"
          />
        </div>

        <div>
          <label className="text-sm font-medium text-[#a0a0b0] mb-1 block">
            Negative Prompt
            {imageSettings.useEdenNegative && (
              <span className="ml-2 text-xs text-[#00d4aa]">(EDEN defaults applied)</span>
            )}
          </label>
          <textarea
            value={negativePrompt}
            onChange={(e) => setNegativePrompt(e.target.value)}
            placeholder="Add additional negative keywords..."
            className="input-eden min-h-[60px] resize-none"
          />
        </div>
      </div>

      {/* Basic Settings */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium text-[#a0a0b0] mb-1 block">
            Resolution
          </label>
          <select
            value={`${imageSettings.width}x${imageSettings.height}`}
            onChange={(e) => {
              const [w, h] = e.target.value.split('x').map(Number);
              setImageSettings({ width: w, height: h });
            }}
            className="input-eden"
          >
            {resolutions.map((res) => (
              <option key={`${res.width}x${res.height}`} value={`${res.width}x${res.height}`}>
                {res.label} - {res.width}x{res.height}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-[#a0a0b0] mb-1 block">
            Scheduler
          </label>
          <select
            value={imageSettings.scheduler}
            onChange={(e) => setImageSettings({ scheduler: e.target.value })}
            className="input-eden"
          >
            {schedulers.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Advanced Settings Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-sm text-[#a0a0b0] hover:text-white transition-colors"
      >
        <Settings className="w-4 h-4" />
        Advanced Settings
        <span className="ml-auto">{showAdvanced ? '−' : '+'}</span>
      </button>

      {/* Advanced Settings */}
      {showAdvanced && (
        <div className="space-y-4 p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
          {/* Steps */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <label className="text-[#a0a0b0]">Inference Steps</label>
              <span>{imageSettings.steps}</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              value={imageSettings.steps}
              onChange={(e) => setImageSettings({ steps: Number(e.target.value) })}
              className="w-full"
            />
            <p className="text-xs text-[#a0a0b0] mt-1">
              20-30: Fast preview | 30-50: Quality | 50+: Maximum detail
            </p>
          </div>

          {/* CFG Scale */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <label className="text-[#a0a0b0]">CFG Scale (Guidance)</label>
              <span>{imageSettings.guidanceScale}</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              step="0.5"
              value={imageSettings.guidanceScale}
              onChange={(e) => setImageSettings({ guidanceScale: Number(e.target.value) })}
              className="w-full"
            />
            <p className="text-xs text-[#a0a0b0] mt-1">
              5-7: Creative | 7-9: Balanced (recommended) | 10+: Strict
            </p>
          </div>

          {/* Seed */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-sm text-[#a0a0b0]">Seed</label>
              <button
                onClick={() => setImageSettings({ seed: -1 })}
                className="text-xs text-[#00d4aa] hover:underline"
              >
                Randomize
              </button>
            </div>
            <input
              type="number"
              value={imageSettings.seed}
              onChange={(e) => setImageSettings({ seed: Number(e.target.value) })}
              className="input-eden"
              placeholder="-1 for random"
            />
          </div>

          {/* EDEN Negative Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm text-[#a0a0b0]">Use EDEN Negative</label>
              <p className="text-xs text-[#a0a0b0]">
                Comprehensive negative for maximum realness
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={imageSettings.useEdenNegative}
                onChange={(e) => setImageSettings({ useEdenNegative: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[#2a2a3a] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00d4aa]" />
            </label>
          </div>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={isGenerating || !prompt.trim()}
        className="w-full btn-eden flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Wand2 className="w-5 h-5" />
            Generate Image
          </>
        )}
      </button>

      {/* Tips */}
      <div className="p-3 rounded-lg bg-[#00d4aa]/10 border border-[#00d4aa]/30">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-[#00d4aa] mt-0.5" />
          <div className="text-xs text-[#a0a0b0]">
            <p className="text-white font-medium mb-1">For Maximum Human Realism:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>Use EDEN's full negative keywords</li>
              <li>Avoid "perfect" symmetry in prompts</li>
              <li>Include lighting details (natural, soft, golden hour)</li>
              <li>Camera settings help: "85mm lens, f/1.8"</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EDENImagesTab;
