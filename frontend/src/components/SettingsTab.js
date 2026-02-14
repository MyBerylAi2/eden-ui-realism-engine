/**
 * EDEN UI REALISM ENGINE - Settings Tab
 * =====================================
 * Application settings and configuration.
 */
import React, { useState } from 'react';
import { 
  Settings, Folder, Trash2, RefreshCw, Save, Shield,
  Cpu, Zap, Moon, Sun, Keyboard, ExternalLink 
} from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../hooks/useStore';
import { getNegativeKeywords, getNegativeCategories, unloadModel } from '../services/api';

const SettingsTab = () => {
  const { 
    imageSettings, 
    setImageSettings,
    videoSettings,
    setVideoSettings,
    customNegativeAdditions,
    setCustomNegativeAdditions,
    systemStatus
  } = useStore();

  const [activeSection, setActiveSection] = useState('general');
  const [negativePreview, setNegativePreview] = useState('');
  const [showNegativeModal, setShowNegativeModal] = useState(false);

  const handleUnloadModels = async () => {
    try {
      await unloadModel();
      toast.success('Models unloaded from VRAM');
    } catch (error) {
      toast.error('Failed to unload models');
    }
  };

  const previewNegativeKeywords = async (category = 'all') => {
    try {
      const response = await getNegativeKeywords(category);
      setNegativePreview(response.data.keywords);
      setShowNegativeModal(true);
    } catch (error) {
      toast.error('Failed to load negative keywords');
    }
  };

  const sections = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'negative', label: 'Negative Keywords', icon: Shield },
    { id: 'system', label: 'System', icon: Cpu },
  ];

  const renderGeneralSettings = () => (
    <div className="space-y-6">
      {/* Default Image Settings */}
      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-[#00d4aa]" />
          Default Image Settings
        </h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-[#a0a0b0] mb-1 block">Default Width</label>
            <select
              value={imageSettings.width}
              onChange={(e) => setImageSettings({ width: Number(e.target.value) })}
              className="input-eden"
            >
              <option value={512}>512px</option>
              <option value={768}>768px</option>
              <option value={1024}>1024px</option>
              <option value={1216}>1216px</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-[#a0a0b0] mb-1 block">Default Height</label>
            <select
              value={imageSettings.height}
              onChange={(e) => setImageSettings({ height: Number(e.target.value) })}
              className="input-eden"
            >
              <option value={512}>512px</option>
              <option value={768}>768px</option>
              <option value={1024}>1024px</option>
              <option value={1216}>1216px</option>
            </select>
          </div>
        </div>

        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <label className="text-[#a0a0b0]">Default Steps</label>
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
        </div>

        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <label className="text-[#a0a0b0]">Default CFG Scale</label>
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
        </div>
      </div>

      {/* Paths */}
      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Folder className="w-4 h-4 text-[#00d4aa]" />
          Paths
        </h3>
        <div className="space-y-3">
          <div>
            <label className="text-sm text-[#a0a0b0] mb-1 block">Models Directory</label>
            <input
              type="text"
              value="~/.cache/huggingface"
              readOnly
              className="input-eden bg-[#0a0a0f]"
            />
          </div>
          <div>
            <label className="text-sm text-[#a0a0b0] mb-1 block">Outputs Directory</label>
            <input
              type="text"
              value="./outputs"
              readOnly
              className="input-eden bg-[#0a0a0f]"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderNegativeSettings = () => (
    <div className="space-y-6">
      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <h3 className="font-medium mb-2 flex items-center gap-2">
          <Shield className="w-4 h-4 text-[#00d4aa]" />
          EDEN Negative Keywords
        </h3>
        <p className="text-sm text-[#a0a0b0] mb-4">
          EDEN uses a comprehensive set of negative keywords to prevent AI artifacts 
          and achieve maximum human realness. Click below to preview the categories.
        </p>

        <div className="grid grid-cols-2 gap-2">
          {[
            { id: 'all', label: 'All Categories' },
            { id: 'base', label: 'Base Artifacts' },
            { id: 'skin_quality', label: 'Skin Quality' },
            { id: 'facial_features', label: 'Facial Features' },
            { id: 'body_anatomy', label: 'Body Anatomy' },
            { id: 'video_artifacts', label: 'Video Artifacts' },
            { id: 'lighting_rendering', label: 'Lighting/Rendering' },
            { id: 'style_filters', label: 'Style Filters' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => previewNegativeKeywords(cat.id)}
              className="p-2 rounded-lg bg-[#2a2a3a] hover:bg-[#00d4aa]/20 text-left text-sm transition-colors"
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <h3 className="font-medium mb-2">Custom Negative Additions</h3>
        <p className="text-sm text-[#a0a0b0] mb-3">
          Add your own negative keywords that will be appended to EDEN's defaults.
        </p>
        <textarea
          value={customNegativeAdditions}
          onChange={(e) => setCustomNegativeAdditions(e.target.value)}
          placeholder="e.g., watermark, signature, cropped, out of frame"
          className="input-eden min-h-[100px] resize-none"
        />
      </div>

      <div className="p-4 rounded-lg bg-[#00d4aa]/10 border border-[#00d4aa]/30">
        <h4 className="font-medium text-[#00d4aa] mb-2">Why EDEN's Negative Keywords?</h4>
        <p className="text-sm text-[#a0a0b0]">
          EDEN's negative keyword system targets specific AI artifacts that make generated 
          humans look fake: perfect symmetry, plastic skin, dead eyes, unnatural poses, 
          and temporal inconsistencies in video. The system is continuously refined based 
          on research into models like Kling and other photorealistic generators.
        </p>
      </div>
    </div>
  );

  const renderSystemSettings = () => (
    <div className="space-y-6">
      {/* GPU Status */}
      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-[#00d4aa]" />
          GPU Status
        </h3>
        
        {systemStatus?.gpu?.available ? (
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-[#a0a0b0]">GPU</span>
              <span>{systemStatus.gpu.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#a0a0b0]">Memory</span>
              <span>
                {(systemStatus.gpu.memory_allocated / 1024 / 1024 / 1024).toFixed(2)} GB / {' '}
                {(systemStatus.gpu.memory_total / 1024 / 1024 / 1024).toFixed(2)} GB
              </span>
            </div>
            <div className="w-full h-2 bg-[#2a2a3a] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#00d4aa] transition-all"
                style={{
                  width: `${(systemStatus.gpu.memory_allocated / systemStatus.gpu.memory_total) * 100}%`
                }}
              />
            </div>
            <button
              onClick={handleUnloadModels}
              className="w-full py-2 rounded-lg bg-[#2a2a3a] hover:bg-[#3a3a4a] text-sm transition-colors"
            >
              Unload All Models from VRAM
            </button>
          </div>
        ) : (
          <div className="text-center py-4 text-[#a0a0b0]">
            <p>No GPU detected</p>
            <p className="text-sm">Running in CPU mode (slower)</p>
          </div>
        )}
      </div>

      {/* Cache Management */}
      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <h3 className="font-medium mb-4">Cache Management</h3>
        <div className="space-y-2">
          <button className="w-full py-2 px-4 rounded-lg bg-[#2a2a3a] hover:bg-[#3a3a4a] text-left flex items-center gap-2 transition-colors">
            <Trash2 className="w-4 h-4" />
            Clear Generation Cache
          </button>
          <button className="w-full py-2 px-4 rounded-lg bg-[#2a2a3a] hover:bg-[#3a3a4a] text-left flex items-center gap-2 transition-colors">
            <RefreshCw className="w-4 h-4" />
            Reset All Settings
          </button>
        </div>
      </div>

      {/* About */}
      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <h3 className="font-medium mb-2">About EDEN UI REALISM ENGINE</h3>
        <p className="text-sm text-[#a0a0b0]">
          Version 1.0.0
        </p>
        <p className="text-sm text-[#a0a0b0] mt-2">
          A diffusion model fine-tuner built for maximum human realness. 
          Import any HuggingFace model and generate photorealistic images and videos.
        </p>
        <div className="flex gap-3 mt-4">
          <a 
            href="https://github.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-[#00d4aa] text-sm hover:underline flex items-center gap-1"
          >
            GitHub <ExternalLink className="w-3 h-3" />
          </a>
          <a 
            href="https://huggingface.co" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-[#00d4aa] text-sm hover:underline flex items-center gap-1"
          >
            HuggingFace <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex gap-4">
      {/* Sidebar */}
      <div className="w-40 space-y-1">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`w-full px-3 py-2 rounded-lg text-left text-sm flex items-center gap-2 transition-colors ${
              activeSection === section.id
                ? 'bg-[#00d4aa]/20 text-[#00d4aa]'
                : 'text-[#a0a0b0] hover:bg-[#1a1a25]'
            }`}
          >
            <section.icon className="w-4 h-4" />
            {section.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1">
        {activeSection === 'general' && renderGeneralSettings()}
        {activeSection === 'negative' && renderNegativeSettings()}
        {activeSection === 'system' && renderSystemSettings()}
      </div>

      {/* Negative Keywords Modal */}
      {showNegativeModal && (
        <div 
          className="fixed inset-0 z-50 bg-[#0a0a0f]/90 flex items-center justify-center p-4"
          onClick={() => setShowNegativeModal(false)}
        >
          <div 
            className="bg-[#1a1a25] rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto border border-[#2a2a3a]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-lg">EDEN Negative Keywords</h3>
              <button 
                onClick={() => setShowNegativeModal(false)}
                className="p-2 hover:bg-[#2a2a3a] rounded-lg"
              >
                Close
              </button>
            </div>
            <div className="p-4 bg-[#0a0a0f] rounded-lg font-mono text-sm text-[#a0a0b0] whitespace-pre-wrap">
              {negativePreview}
            </div>
            <button
              onClick={() => navigator.clipboard.writeText(negativePreview)}
              className="mt-4 w-full py-2 rounded-lg bg-[#00d4aa] text-[#0a0a0f] font-medium"
            >
              Copy to Clipboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsTab;
