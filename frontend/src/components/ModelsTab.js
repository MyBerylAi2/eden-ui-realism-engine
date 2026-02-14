/**
 * EDEN UI REALISM ENGINE - Models Tab
 * ===================================
 * HuggingFace model management and import.
 */
import React, { useState, useEffect } from 'react';
import { 
  Search, Download, CheckCircle, Star, Trash2, RefreshCw,
  ExternalLink, HardDrive, Filter, Plus, Cpu 
} from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../hooks/useStore';
import { 
  searchModels, 
  downloadModel, 
  listDownloadedModels,
  getRecommendedModels 
} from '../services/api';

const ModelsTab = () => {
  const { currentModel, setCurrentModel, downloadedModels, setDownloadedModels } = useStore();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [downloadingId, setDownloadingId] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    loadDownloadedModels();
  }, []);

  const loadDownloadedModels = async () => {
    try {
      const response = await listDownloadedModels();
      const recommended = await getRecommendedModels();
      
      // Merge downloaded with recommended
      const allModels = [...response.data.models];
      recommended.data.models.forEach(rec => {
        if (!allModels.find(m => m.id === rec.id)) {
          allModels.push({ ...rec, isRecommended: true, is_downloaded: false });
        }
      });
      
      setDownloadedModels(allModels);
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const response = await searchModels(searchQuery, activeFilter === 'all' ? 'text-to-image' : activeFilter);
      setSearchResults(response.data.models);
      setShowSearch(true);
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const handleDownload = async (modelId) => {
    setDownloadingId(modelId);
    try {
      await downloadModel(modelId);
      toast.success(`Downloaded ${modelId}`);
      loadDownloadedModels();
    } catch (error) {
      toast.error('Download failed');
    } finally {
      setDownloadingId(null);
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) return `${gb.toFixed(1)} GB`;
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const filters = [
    { id: 'all', label: 'All' },
    { id: 'text-to-image', label: 'Text2Img' },
    { id: 'image-to-video', label: 'Img2Vid' },
    { id: 'text-to-video', label: 'Text2Vid' },
    { id: 'vae', label: 'VAE' },
    { id: 'lora', label: 'LoRA' },
  ];

  const displayedModels = showSearch ? searchResults : downloadedModels;

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#a0a0b0]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search HuggingFace models..."
            className="input-eden pl-10"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="px-4 py-2 rounded-lg bg-[#00d4aa] text-[#0a0a0f] font-medium hover:bg-[#00b894] disabled:opacity-50"
        >
          {isSearching ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Search'}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {filters.map((filter) => (
          <button
            key={filter.id}
            onClick={() => setActiveFilter(filter.id)}
            className={`px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
              activeFilter === filter.id
                ? 'bg-[#00d4aa] text-[#0a0a0f]'
                : 'bg-[#1a1a25] text-[#a0a0b0] hover:text-white'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Results Toggle */}
      {searchResults.length > 0 && (
        <div className="flex gap-2">
          <button
            onClick={() => setShowSearch(false)}
            className={`px-4 py-2 rounded-lg text-sm ${!showSearch ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'text-[#a0a0b0]'}`}
          >
            My Models ({downloadedModels.length})
          </button>
          <button
            onClick={() => setShowSearch(true)}
            className={`px-4 py-2 rounded-lg text-sm ${showSearch ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'text-[#a0a0b0]'}`}
          >
            Search Results ({searchResults.length})
          </button>
        </div>
      )}

      {/* Models List */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {displayedModels.length === 0 && (
          <div className="text-center py-8 text-[#a0a0b0]">
            <Cpu className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No models found</p>
            <p className="text-sm">Search HuggingFace to import models</p>
          </div>
        )}

        {displayedModels.map((model) => (
          <div
            key={model.id}
            className={`p-3 rounded-lg border transition-all ${
              currentModel === model.id
                ? 'bg-[#00d4aa]/10 border-[#00d4aa]'
                : 'bg-[#1a1a25] border-[#2a2a3a] hover:border-[#00d4aa]/50'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-sm truncate">{model.id}</h4>
                  {model.is_downloaded && (
                    <CheckCircle className="w-4 h-4 text-[#2ed573] flex-shrink-0" />
                  )}
                  {model.isRecommended && !model.is_downloaded && (
                    <Star className="w-4 h-4 text-[#ffa502] flex-shrink-0" />
                  )}
                </div>
                
                {model.description && (
                  <p className="text-xs text-[#a0a0b0] mt-1 line-clamp-2">
                    {model.description}
                  </p>
                )}
                
                <div className="flex items-center gap-3 mt-2 text-xs text-[#a0a0b0]">
                  {model.downloads && (
                    <span className="flex items-center gap-1">
                      <Download className="w-3 h-3" />
                      {(model.downloads / 1000).toFixed(1)}k
                    </span>
                  )}
                  {model.size && (
                    <span className="flex items-center gap-1">
                      <HardDrive className="w-3 h-3" />
                      {formatSize(model.size)}
                    </span>
                  )}
                  {model.pipeline_tag && (
                    <span className="px-2 py-0.5 rounded bg-[#2a2a3a]">
                      {model.pipeline_tag}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-1 ml-2">
                {model.is_downloaded ? (
                  <>
                    <button
                      onClick={() => setCurrentModel(model.id)}
                      className={`p-2 rounded-lg transition-colors ${
                        currentModel === model.id
                          ? 'bg-[#00d4aa] text-[#0a0a0f]'
                          : 'hover:bg-[#2a2a3a]'
                      }`}
                      title={currentModel === model.id ? 'Selected' : 'Select Model'}
                    >
                      <CheckCircle className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => window.open(`https://huggingface.co/${model.id}`, '_blank')}
                      className="p-2 rounded-lg hover:bg-[#2a2a3a]"
                      title="View on HuggingFace"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleDownload(model.id)}
                    disabled={downloadingId === model.id}
                    className="p-2 rounded-lg bg-[#00d4aa]/10 text-[#00d4aa] hover:bg-[#00d4aa]/20 disabled:opacity-50"
                    title="Download Model"
                  >
                    {downloadingId === model.id ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Import Info */}
      <div className="p-3 rounded-lg bg-[#1a1a25] border border-[#2a2a3a]">
        <p className="text-xs text-[#a0a0b0]">
          <strong className="text-white">Import any HuggingFace model:</strong> Search for model IDs 
          like "stabilityai/stable-diffusion-xl-base-1.0" or "Wan-AI/Wan2.1-T2V-1.3B". 
          Models are downloaded and cached locally.
        </p>
      </div>
    </div>
  );
};

export default ModelsTab;
