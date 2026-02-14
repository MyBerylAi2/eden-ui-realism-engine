/**
 * EDEN UI REALISM ENGINE - EDEN VIDEOS Tab
 * ========================================
 * Video generation settings optimized for temporal consistency.
 */
import React, { useState } from 'react';
import { 
  Film, Settings, RefreshCw, Image as ImageIcon, 
  Clock, Zap, Layers, AlertTriangle, Wand2,
  ChevronRight, Video
} from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../hooks/useStore';
import { generateVideo, imageToVideo, getPresets } from '../services/api';

const EDENVideosTab = () => {
  const {
    videoSettings,
    setVideoSettings,
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
  const [generationMode, setGenerationMode] = useState('text2video'); // 'text2video' | 'image2video'
  const [inputImage, setInputImage] = useState(null);
  const [motionBucket, setMotionBucket] = useState(127);

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

    // Simulate progress for longer generation
    const progressInterval = setInterval(() => {
      setGenerationProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 8;
      });
    }, 2000);

    try {
      let response;

      if (generationMode === 'text2video') {
        response = await generateVideo({
          prompt,
          model_id: 'Wan-AI/Wan2.1-T2V-1.3B',
          negative_prompt: negativePrompt || undefined,
          width: videoSettings.width,
          height: videoSettings.height,
          num_frames: videoSettings.numFrames,
          fps: videoSettings.fps,
          num_inference_steps: videoSettings.steps,
          guidance_scale: videoSettings.guidanceScale,
          seed: videoSettings.seed === -1 ? undefined : videoSettings.seed,
          scheduler: videoSettings.scheduler,
          use_eden_negative: videoSettings.useEdenNegative,
          preset: 'cinematic_video',
        });
      } else {
        // Image to video
        if (!inputImage) {
          toast.error('Please upload an image first');
          setIsGenerating(false);
          setGenerating(false);
          clearInterval(progressInterval);
          return;
        }

        response = await imageToVideo({
          image_path: inputImage.path,
          prompt,
          model_id: 'stabilityai/stable-video-diffusion-img2vid-xt',
          num_frames: videoSettings.numFrames,
          fps: videoSettings.fps,
          motion_bucket_id: motionBucket,
          seed: videoSettings.seed === -1 ? undefined : videoSettings.seed,
        });
      }

      clearInterval(progressInterval);
      setGenerationProgress(100);

      if (response.data.success) {
        setLastGeneration(response.data);
        addToHistory(response.data);
        toast.success('Video generated successfully!');
      } else {
        throw new Error(response.data.error || 'Generation failed');
      }
    } catch (error) {
      clearInterval(progressInterval);
      toast.error(error.message || 'Failed to generate video');
      console.error(error);
    } finally {
      setIsGenerating(false);
      setGenerating(false);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setInputImage(data);
      toast.success('Image uploaded');
    } catch (error) {
      toast.error('Failed to upload image');
    }
  };

  const applyPreset = async (presetName) => {
    try {
      const response = await getPresets();
      const preset = response.data.presets[presetName];
      if (preset) {
        setVideoSettings({
          steps: preset.num_inference_steps || 25,
          guidanceScale: preset.guidance_scale || 6.0,
          fps: preset.fps || 8,
        });
        toast.success(`Applied ${preset.name} preset`);
      }
    } catch (error) {
      console.error('Failed to load preset:', error);
    }
  };

  const videoPresets = [
    { name: 'cinematic_video', label: 'Cinematic', desc: '24fps quality' },
    { name: 'kling_reference', label: 'Kling Style', desc: 'Human motion' },
    { name: 'fast_preview', label: 'Fast Preview', desc: 'Quick test' },
  ];

  const schedulers = ['DDIM', 'DPM++ 2M', 'Euler a', 'Euler'];

  const videoResolutions = [
    { label: 'Landscape (16:9)', width: 832, height: 480 },
    { label: 'Portrait (9:16)', width: 480, height: 832 },
    { label: 'Square (1:1)', width: 512, height: 512 },
    { label: 'Cinematic (21:9)', width: 1024, height: 438 },
  ];

  return (
    <div className="space-y-6">
      {/* Generation Mode Toggle */}
      <div className="flex rounded-lg bg-[#1a1a25] p-1">
        <button
          onClick={() => setGenerationMode('text2video')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
            generationMode === 'text2video'
              ? 'bg-[#00d4aa] text-[#0a0a0f]'
              : 'text-[#a0a0b0] hover:text-white'
          }`}
        >
          <Film className="w-4 h-4 inline mr-2" />
          Text to Video
        </button>
        <button
          onClick={() => setGenerationMode('image2video')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
            generationMode === 'image2video'
              ? 'bg-[#00d4aa] text-[#0a0a0f]'
              : 'text-[#a0a0b0] hover:text-white'
          }`}
        >
          <ImageIcon className="w-4 h-4 inline mr-2" />
          Image to Video
        </button>
      </div>

      {/* Image Input for I2V */}
      {generationMode === 'image2video' && (
        <div>
          <label className="text-sm font-medium text-[#a0a0b0] mb-2 block">
            Input Image
          </label>
          <div className="relative">
            {inputImage ? (
              <div className="relative rounded-lg overflow-hidden">
                <img
                  src={`http://localhost:8000${inputImage.url}`}
                  alt="Input"
                  className="w-full h-48 object-cover"
                />
                <button
                  onClick={() => setInputImage(null)}
                  className="absolute top-2 right-2 p-2 rounded-lg bg-[#ff4757] text-white"
                >
                  Remove
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center w-full h-32 rounded-lg border-2 border-dashed border-[#2a2a3a] bg-[#1a1a25] cursor-pointer hover:border-[#00d4aa] transition-colors">
                <ImageIcon className="w-8 h-8 text-[#a0a0b0] mb-2" />
                <span className="text-sm text-[#a0a0b0]">Click to upload image</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>
      )}

      {/* Presets */}
      <div>
        <label className="text-sm font-medium text-[#a0a0b0] mb-2 block">
          Video Presets
        </label>
        <div className="grid grid-cols-3 gap-2">
          {videoPresets.map((preset) => (
            <button
              key={preset.name}
              onClick={() => applyPreset(preset.name)}
              className="p-3 rounded-lg bg-[#1a1a25] border border-[#2a2a3a] hover:border-[#00d4aa] transition-all text-left"
            >
              <Video className="w-4 h-4 text-[#00d4aa] mb-1" />
              <p className="text-sm font-medium">{preset.label}</p>
              <p className="text-xs text-[#a0a0b0]">{preset.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Prompt */}
      <div>
        <label className="text-sm font-medium text-[#a0a0b0] mb-1 block">
          Prompt {generationMode === 'image2video' && '(optional, describes motion)'}
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={generationMode === 'text2video' 
            ? "Describe the video you want to create..." 
            : "Describe the motion (optional)..."}
          className="input-eden min-h-[80px] resize-none"
        />
      </div>

      {/* Basic Settings */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium text-[#a0a0b0] mb-1 block">
            Resolution
          </label>
          <select
            value={`${videoSettings.width}x${videoSettings.height}`}
            onChange={(e) => {
              const [w, h] = e.target.value.split('x').map(Number);
              setVideoSettings({ width: w, height: h });
            }}
            className="input-eden"
          >
            {videoResolutions.map((res) => (
              <option key={`${res.width}x${res.height}`} value={`${res.width}x${res.height}`}>
                {res.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-[#a0a0b0] mb-1 block">
            Duration (Frames @ FPS)
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              value={videoSettings.numFrames}
              onChange={(e) => setVideoSettings({ numFrames: Number(e.target.value) })}
              className="input-eden flex-1"
              min="8"
              max="64"
            />
            <span className="flex items-center text-[#a0a0b0]">@</span>
            <select
              value={videoSettings.fps}
              onChange={(e) => setVideoSettings({ fps: Number(e.target.value) })}
              className="input-eden w-24"
            >
              <option value={8}>8fps</option>
              <option value={12}>12fps</option>
              <option value={16}>16fps</option>
              <option value={24}>24fps</option>
            </select>
          </div>
          <p className="text-xs text-[#a0a0b0] mt-1">
            {(videoSettings.numFrames / videoSettings.fps).toFixed(1)}s duration
          </p>
        </div>
      </div>

      {/* Advanced Settings */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-sm text-[#a0a0b0] hover:text-white transition-colors"
      >
        <Settings className="w-4 h-4" />
        Advanced Settings
        <span className="ml-auto">{showAdvanced ? '−' : '+'}</span>
      </button>

      {showAdvanced && (
        <div className="space-y-4 p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
          {/* Steps */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <label className="text-[#a0a0b0]">Inference Steps</label>
              <span>{videoSettings.steps}</span>
            </div>
            <input
              type="range"
              min="10"
              max="50"
              value={videoSettings.steps}
              onChange={(e) => setVideoSettings({ steps: Number(e.target.value) })}
              className="w-full"
            />
          </div>

          {/* CFG Scale */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <label className="text-[#a0a0b0]">CFG Scale</label>
              <span>{videoSettings.guidanceScale}</span>
            </div>
            <input
              type="range"
              min="1"
              max="15"
              step="0.5"
              value={videoSettings.guidanceScale}
              onChange={(e) => setVideoSettings({ guidanceScale: Number(e.target.value) })}
              className="w-full"
            />
          </div>

          {/* Motion Bucket (I2V only) */}
          {generationMode === 'image2video' && (
            <div>
              <div className="flex justify-between text-sm mb-1">
                <label className="text-[#a0a0b0]">Motion Intensity (0-255)</label>
                <span>{motionBucket}</span>
              </div>
              <input
                type="range"
                min="0"
                max="255"
                value={motionBucket}
                onChange={(e) => setMotionBucket(Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-[#a0a0b0] mt-1">
                Lower: Subtle motion | Higher: Dynamic movement
              </p>
            </div>
          )}

          {/* Seed */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-sm text-[#a0a0b0]">Seed</label>
              <button
                onClick={() => setVideoSettings({ seed: -1 })}
                className="text-xs text-[#00d4aa] hover:underline"
              >
                Randomize
              </button>
            </div>
            <input
              type="number"
              value={videoSettings.seed}
              onChange={(e) => setVideoSettings({ seed: Number(e.target.value) })}
              className="input-eden"
            />
          </div>

          {/* EDEN Negative */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm text-[#a0a0b0]">Use EDEN Negative</label>
              <p className="text-xs text-[#a0a0b0]">
                Prevents temporal artifacts
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={videoSettings.useEdenNegative}
                onChange={(e) => setVideoSettings({ useEdenNegative: e.target.checked })}
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
        disabled={isGenerating || (!prompt.trim() && generationMode === 'text2video') || (generationMode === 'image2video' && !inputImage)}
        className="w-full btn-eden flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            Generating Video...
          </>
        ) : (
          <>
            <Film className="w-5 h-5" />
            Generate Video
          </>
        )}
      </button>

      {/* Video Tips */}
      <div className="p-3 rounded-lg bg-[#00d4aa]/10 border border-[#00d4aa]/30">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-[#00d4aa] mt-0.5" />
          <div className="text-xs text-[#a0a0b0]">
            <p className="text-white font-medium mb-1">For Longer Videos:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>Generate multiple clips and use EDEN's merging feature</li>
              <li>Use lower motion_bucket for smoother transitions</li>
              <li>Enable EDEN negative to prevent flickering/morphing</li>
              <li>Consistent seed helps with sequential generation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EDENVideosTab;
