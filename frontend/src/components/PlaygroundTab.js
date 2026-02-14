/**
 * EDEN UI REALISM ENGINE - Playground Tab
 * =======================================
 * ComfyUI integration and enhancement search.
 */
import React, { useState, useEffect } from 'react';
import { 
  Workflow, Search, Zap, Layers, Cpu, Globe, 
  Plus, Play, Save, Trash2, RefreshCw, Settings 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { getComfyUIStatus, getEnhancements } from '../services/api';

const PlaygroundTab = () => {
  const [comfyUIStatus, setComfyUIStatus] = useState({ connected: false });
  const [enhancements, setEnhancements] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [workflows, setWorkflows] = useState([
    {
      id: 'default',
      name: 'EDEN Basic Workflow',
      description: 'Standard image generation with enhancements',
      nodes: ['Load Checkpoint', 'KSampler', 'VAE Decode', 'Save Image']
    },
    {
      id: 'upscale',
      name: 'EDEN Upscale Pipeline',
      description: 'Generate and upscale in one go',
      nodes: ['Load Checkpoint', 'KSampler', 'Upscale Model', 'Save Image']
    },
    {
      id: 'img2vid',
      name: 'Image to Video',
      description: 'Animate static images',
      nodes: ['Load Image', 'SVD Model', 'Video Combine', 'Save Video']
    }
  ]);

  useEffect(() => {
    checkComfyUIStatus();
    loadEnhancements();
  }, []);

  const checkComfyUIStatus = async () => {
    try {
      const response = await getComfyUIStatus();
      setComfyUIStatus(response.data);
    } catch (error) {
      setComfyUIStatus({ connected: false });
    }
  };

  const loadEnhancements = async () => {
    try {
      const response = await getEnhancements();
      setEnhancements(Object.entries(response.data.enhancements).map(([key, value]) => ({
        id: key,
        ...value
      })));
    } catch (error) {
      console.error('Failed to load enhancements:', error);
    }
  };

  const handleLaunchComfyUI = () => {
    window.open('http://localhost:8188', '_blank');
  };

  const filteredEnhancements = enhancements.filter(e => 
    e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* ComfyUI Status */}
      <div className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${comfyUIStatus.connected ? 'bg-[#2ed573] animate-pulse' : 'bg-[#ff4757]'}`} />
            <div>
              <h3 className="font-medium">ComfyUI Integration</h3>
              <p className="text-sm text-[#a0a0b0]">
                {comfyUIStatus.connected 
                  ? 'Connected and ready' 
                  : 'Not connected - Launch ComfyUI externally'}
              </p>
            </div>
          </div>
          <button
            onClick={handleLaunchComfyUI}
            className="btn-eden-secondary flex items-center gap-2"
          >
            <Globe className="w-4 h-4" />
            Open ComfyUI
          </button>
        </div>
      </div>

      {/* Enhancement Search */}
      <div>
        <label className="text-sm font-medium text-[#a0a0b0] mb-2 block">
          Search Enhancements
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#a0a0b0]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for enhancement modules..."
            className="input-eden pl-10"
          />
        </div>
      </div>

      {/* Enhancement Grid */}
      <div className="grid grid-cols-2 gap-3">
        {filteredEnhancements.map((enhancement) => (
          <div
            key={enhancement.id}
            className="p-3 rounded-lg bg-[#1a1a25] border border-[#2a2a3a] hover:border-[#00d4aa] transition-all cursor-pointer group"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-[#00d4aa]/10 group-hover:bg-[#00d4aa]/20 transition-colors">
                <Zap className="w-5 h-5 text-[#00d4aa]" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-sm">{enhancement.name}</h4>
                <p className="text-xs text-[#a0a0b0] mt-0.5">{enhancement.description}</p>
                {enhancement.models && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {enhancement.models.map((model) => (
                      <span
                        key={model}
                        className="px-2 py-0.5 text-xs rounded-full bg-[#2a2a3a] text-[#a0a0b0]"
                      >
                        {model}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <Plus className="w-4 h-4 text-[#a0a0b0] group-hover:text-[#00d4aa]" />
            </div>
          </div>
        ))}
      </div>

      {/* Workflows */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-[#a0a0b0]">
            EDEN Workflows
          </label>
          <button className="text-xs text-[#00d4aa] hover:underline">
            + New Workflow
          </button>
        </div>

        <div className="space-y-2">
          {workflows.map((workflow) => (
            <div
              key={workflow.id}
              onClick={() => setActiveWorkflow(workflow.id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                activeWorkflow === workflow.id
                  ? 'bg-[#00d4aa]/10 border-[#00d4aa]'
                  : 'bg-[#1a1a25] border-[#2a2a3a] hover:border-[#00d4aa]/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Workflow className="w-5 h-5 text-[#00d4aa]" />
                  <div>
                    <h4 className="font-medium text-sm">{workflow.name}</h4>
                    <p className="text-xs text-[#a0a0b0]">{workflow.description}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button className="p-1.5 rounded hover:bg-[#2a2a3a]" title="Run">
                    <Play className="w-4 h-4 text-[#00d4aa]" />
                  </button>
                  <button className="p-1.5 rounded hover:bg-[#2a2a3a]" title="Edit">
                    <Settings className="w-4 h-4 text-[#a0a0b0]" />
                  </button>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {workflow.nodes.map((node) => (
                  <span
                    key={node}
                    className="px-2 py-0.5 text-xs rounded bg-[#2a2a3a] text-[#a0a0b0]"
                  >
                    {node}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3">
        <button className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a] hover:border-[#00d4aa] transition-all text-center">
          <Layers className="w-6 h-6 text-[#00d4aa] mx-auto mb-2" />
          <p className="text-sm font-medium">Model Merge</p>
          <p className="text-xs text-[#a0a0b0]">Combine checkpoints</p>
        </button>
        <button className="p-4 rounded-lg bg-[#1a1a25] border border-[#2a2a3a] hover:border-[#00d4aa] transition-all text-center">
          <Cpu className="w-6 h-6 text-[#00d4aa] mx-auto mb-2" />
          <p className="text-sm font-medium">Distill Model</p>
          <p className="text-xs text-[#a0a0b0]">Create lightweight version</p>
        </button>
      </div>
    </div>
  );
};

export default PlaygroundTab;
