/**
 * EDEN UI REALISM ENGINE - Preview Panel Component
 * ================================================
 * Displays generated images/videos and allows interaction.
 */
import React, { useState } from 'react';
import { 
  Download, Expand, Share2, Trash2, Image as ImageIcon, 
  Film, Clock, Settings, CheckCircle, XCircle, Loader 
} from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../hooks/useStore';

const PreviewPanel = () => {
  const { 
    lastGeneration, 
    isGenerating, 
    generationProgress,
    generationHistory 
  } = useStore();

  const [selectedItem, setSelectedItem] = useState(null);
  const [viewMode, setViewMode] = useState('current'); // 'current' | 'gallery'

  const handleDownload = (url, filename) => {
    const link = document.createElement('a');
    link.href = `http://localhost:8000${url}`;
    link.download = filename || 'eden-output';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Download started');
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  };

  const renderCurrentGeneration = () => {
    if (isGenerating) {
      return (
        <div className="h-full flex flex-col items-center justify-center">
          <div className="relative">
            <div className="w-32 h-32 rounded-full border-4 border-[#2a2a3a]" />
            <div 
              className="absolute inset-0 rounded-full border-4 border-t-[#00d4aa] border-r-transparent border-b-transparent border-l-transparent animate-spin"
              style={{ transform: `rotate(${generationProgress * 3.6}deg)` }}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader className="w-10 h-10 text-[#00d4aa] animate-spin" />
            </div>
          </div>
          <p className="mt-6 text-lg font-medium">Generating...</p>
          <p className="text-[#a0a0b0]">{Math.round(generationProgress)}% complete</p>
          <div className="mt-4 w-64 h-2 bg-[#2a2a3a] rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-[#00d4aa] to-[#00b894] transition-all duration-300"
              style={{ width: `${generationProgress}%` }}
            />
          </div>
        </div>
      );
    }

    if (!lastGeneration || !lastGeneration.output_path) {
      return (
        <div className="h-full flex flex-col items-center justify-center text-[#a0a0b0]">
          <div className="w-32 h-32 rounded-2xl bg-[#1a1a25] border-2 border-dashed border-[#2a2a3a] flex items-center justify-center mb-6">
            <ImageIcon className="w-12 h-12 opacity-50" />
          </div>
          <p className="text-xl font-medium text-white mb-2">Ready to Create</p>
          <p className="text-center max-w-md">
            Use the controls below to generate images or videos.
            <br />
            Chat with EDEN on the left for AI assistance.
          </p>
        </div>
      );
    }

    const isVideo = lastGeneration.output_path.endsWith('.mp4');
    const outputUrl = `http://localhost:8000${lastGeneration.output_path.replace('/home/letsgo/eden-ui-realism-engine', '')}`;

    return (
      <div className="h-full flex flex-col">
        {/* Preview */}
        <div className="flex-1 flex items-center justify-center p-4 bg-[#0a0a0f] relative group">
          {isVideo ? (
            <video
              src={outputUrl}
              controls
              className="max-w-full max-h-full rounded-lg shadow-2xl"
              autoPlay
              loop
            />
          ) : (
            <img
              src={outputUrl}
              alt="Generated"
              className="max-w-full max-h-full rounded-lg shadow-2xl object-contain"
            />
          )}

          {/* Overlay Actions */}
          <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => handleDownload(outputUrl, `eden-output-${Date.now()}`)}
              className="p-2 rounded-lg bg-[#1a1a25]/80 backdrop-blur border border-[#2a2a3a] hover:border-[#00d4aa] transition-colors"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={() => setSelectedItem(lastGeneration)}
              className="p-2 rounded-lg bg-[#1a1a25]/80 backdrop-blur border border-[#2a2a3a] hover:border-[#00d4aa] transition-colors"
            >
              <Expand className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Info Bar */}
        <div className="p-4 bg-[#12121a] border-t border-[#2a2a3a]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1 text-[#00d4aa]">
                <CheckCircle className="w-4 h-4" />
                Generated
              </span>
              <span className="text-[#a0a0b0]">
                {lastGeneration.width && `${lastGeneration.width}x${lastGeneration.height}`}
              </span>
              <span className="text-[#a0a0b0] flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatDuration(lastGeneration.generation_time)}
              </span>
              {lastGeneration.seed !== undefined && (
                <span className="text-[#a0a0b0]">Seed: {lastGeneration.seed}</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#a0a0b0]">
                CFG: {lastGeneration.guidance_scale} | Steps: {lastGeneration.steps}
              </span>
            </div>
          </div>
          {lastGeneration.prompt && (
            <p className="mt-2 text-sm text-[#a0a0b0] truncate">
              <span className="text-white">Prompt:</span> {lastGeneration.prompt}
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderGallery = () => {
    if (generationHistory.length === 0) {
      return (
        <div className="h-full flex items-center justify-center text-[#a0a0b0]">
          <p>No generation history yet</p>
        </div>
      );
    }

    return (
      <div className="h-full overflow-y-auto p-4">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {generationHistory.map((item, index) => {
            const isVideo = item.output_path?.endsWith('.mp4');
            const outputUrl = item.output_path 
              ? `http://localhost:8000${item.output_path.replace('/home/letsgo/eden-ui-realism-engine', '')}`
              : null;

            return (
              <div 
                key={index}
                className="group relative aspect-square rounded-xl overflow-hidden bg-[#1a1a25] border border-[#2a2a3a] hover:border-[#00d4aa] cursor-pointer transition-all"
                onClick={() => setSelectedItem(item)}
              >
                {outputUrl ? (
                  isVideo ? (
                    <video
                      src={outputUrl}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <img
                      src={outputUrl}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  )
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    {isVideo ? <Film className="w-8 h-8 text-[#a0a0b0]" /> : <ImageIcon className="w-8 h-8 text-[#a0a0b0]" />}
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0f] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="absolute bottom-0 left-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <p className="text-xs text-white truncate">{item.prompt}</p>
                  <p className="text-xs text-[#a0a0b0]">{formatDuration(item.generation_time)}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* View Toggle */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#12121a] border-b border-[#2a2a3a]">
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('current')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'current' 
                ? 'bg-[#00d4aa]/20 text-[#00d4aa]' 
                : 'text-[#a0a0b0] hover:text-white'
            }`}
          >
            Current
          </button>
          <button
            onClick={() => setViewMode('gallery')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'gallery' 
                ? 'bg-[#00d4aa]/20 text-[#00d4aa]' 
                : 'text-[#a0a0b0] hover:text-white'
            }`}
          >
            Gallery ({generationHistory.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'current' ? renderCurrentGeneration() : renderGallery()}
      </div>

      {/* Fullscreen Modal */}
      {selectedItem && (
        <div 
          className="fixed inset-0 z-50 bg-[#0a0a0f]/95 flex items-center justify-center p-8"
          onClick={() => setSelectedItem(null)}
        >
          <button
            onClick={() => setSelectedItem(null)}
            className="absolute top-4 right-4 p-2 rounded-lg bg-[#1a1a25] hover:bg-[#2a2a3a]"
          >
            <XCircle className="w-6 h-6" />
          </button>
          {selectedItem.output_path && (
            selectedItem.output_path.endsWith('.mp4') ? (
              <video
                src={`http://localhost:8000${selectedItem.output_path.replace('/home/letsgo/eden-ui-realism-engine', '')}`}
                controls
                className="max-w-full max-h-full rounded-lg"
                autoPlay
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <img
                src={`http://localhost:8000${selectedItem.output_path.replace('/home/letsgo/eden-ui-realism-engine', '')}`}
                alt=""
                className="max-w-full max-h-full rounded-lg object-contain"
                onClick={(e) => e.stopPropagation()}
              />
            )
          )}
        </div>
      )}
    </div>
  );
};

export default PreviewPanel;
