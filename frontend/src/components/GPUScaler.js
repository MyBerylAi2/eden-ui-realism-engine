/**
 * EDEN UI REALISM ENGINE - HF GPU Scaler Component
 * ================================================
 * GPU scaling buttons with pricing overlay and auto-sleep.
 */
import React, { useState, useEffect } from 'react';
import { 
  Zap, Battery, DollarSign, Clock, ChevronUp, ChevronDown,
  Server, Cpu, AlertCircle, CheckCircle, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

const GPUScaler = ({ spaceId = "AIBRUH/video-studio" }) => {
  const [showOverlay, setShowOverlay] = useState(false);
  const [pricing, setPricing] = useState([]);
  const [currentTier, setCurrentTier] = useState(null);
  const [activeUpgrades, setActiveUpgrades] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sleepMinutes, setSleepMinutes] = useState(10);
  const [showSleepSettings, setShowSleepSettings] = useState(false);

  useEffect(() => {
    fetchPricing();
    fetchActiveUpgrades();
    if (spaceId) {
      fetchCurrentStatus();
    }
    
    // Poll for updates every 30 seconds
    const interval = setInterval(() => {
      fetchActiveUpgrades();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [spaceId]);

  const fetchPricing = async () => {
    try {
      const response = await api.get('/api/gpu/pricing');
      setPricing(response.data.pricing);
    } catch (error) {
      console.error('Failed to fetch pricing:', error);
    }
  };

  const fetchCurrentStatus = async () => {
    try {
      const response = await api.get(`/api/gpu/status/${spaceId}`);
      setCurrentTier(response.data.tier);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const fetchActiveUpgrades = async () => {
    try {
      const response = await api.get('/api/gpu/active-upgrades');
      setActiveUpgrades(response.data.upgrades);
    } catch (error) {
      console.error('Failed to fetch upgrades:', error);
    }
  };

  const handleUpgrade = async (gpuTier) => {
    setIsLoading(true);
    try {
      const response = await api.post('/api/gpu/upgrade', {
        space_id: spaceId,
        gpu_tier: gpuTier,
        sleep_after_minutes: sleepMinutes
      });
      
      if (response.data.success) {
        toast.success(response.data.message);
        setCurrentTier(gpuTier);
        fetchActiveUpgrades();
        setShowOverlay(false);
        
        // Show sleep notification
        const info = response.data.upgrade_info;
        if (info.sleep_scheduled_at) {
          toast.info(`Auto-sleep scheduled at ${new Date(info.sleep_scheduled_at).toLocaleTimeString()}`);
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upgrade failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDowngrade = async () => {
    setIsLoading(true);
    try {
      const response = await api.post('/api/gpu/downgrade', null, {
        params: { space_id: spaceId }
      });
      
      if (response.data.success) {
        toast.success(response.data.message);
        setCurrentTier('zero');
        fetchActiveUpgrades();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Downgrade failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExtendSleep = async (additionalMinutes) => {
    try {
      const response = await api.post('/api/gpu/extend', {
        space_id: spaceId,
        additional_minutes: additionalMinutes
      });
      
      if (response.data.success) {
        toast.success(`Extended by ${additionalMinutes} minutes`);
        fetchActiveUpgrades();
      }
    } catch (error) {
      toast.error('Failed to extend sleep timer');
    }
  };

  const getTierIcon = (tier) => {
    switch (tier) {
      case 'zero': return <Battery className="w-4 h-4" />;
      case 't4': return <Cpu className="w-4 h-4" />;
      case 'l4': return <Server className="w-4 h-4" />;
      case 'a10g': return <Zap className="w-4 h-4" />;
      case 'a100': return <Zap className="w-4 h-4 text-yellow-400" />;
      case 'h100': return <Zap className="w-4 h-4 text-purple-400" />;
      default: return <Cpu className="w-4 h-4" />;
    }
  };

  const isUpgraded = currentTier && currentTier !== 'zero';
  const currentUpgrade = activeUpgrades.find(u => u.space_id === spaceId);

  return (
    <div className="relative">
      {/* GPU Control Buttons */}
      <div className="flex items-center gap-2">
        {/* Scale GPU Button */}
        <button
          onClick={() => setShowOverlay(true)}
          disabled={isLoading}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            isUpgraded 
              ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
              : 'bg-gradient-to-r from-[#00d4aa] to-[#00b894] text-[#0a0a0f] hover:shadow-lg hover:shadow-[#00d4aa]/30'
          }`}
        >
          {getTierIcon(currentTier || 'zero')}
          <span>
            {isUpgraded 
              ? `${pricing.find(p => p.id === currentTier)?.name || 'GPU Active'}` 
              : 'SCALE GPU'}
          </span>
          {isUpgraded && <ChevronUp className="w-4 h-4" />}
        </button>

        {/* Zero GPU Button */}
        <button
          onClick={handleDowngrade}
          disabled={isLoading || !isUpgraded}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            isUpgraded
              ? 'bg-[#2a2a3a] text-[#a0a0b0] hover:bg-[#3a3a4a] border border-[#2a2a3a]'
              : 'bg-[#1a1a25] text-[#a0a0b0] cursor-not-allowed opacity-50'
          }`}
        >
          <Battery className="w-4 h-4 inline mr-1" />
          ZERO GPU
        </button>

        {/* Sleep Settings Toggle */}
        {isUpgraded && (
          <button
            onClick={() => setShowSleepSettings(!showSleepSettings)}
            className="p-2 rounded-lg bg-[#1a1a25] text-[#a0a0b0] hover:text-white border border-[#2a2a3a]"
          >
            <Clock className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Sleep Settings Dropdown */}
      {showSleepSettings && isUpgraded && (
        <div className="absolute top-full right-0 mt-2 p-4 bg-[#1a1a25] border border-[#2a2a3a] rounded-lg shadow-xl z-30 w-72">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium">Auto-Sleep Settings</span>
            <button onClick={() => setShowSleepSettings(false)}>
              <X className="w-4 h-4 text-[#a0a0b0]" />
            </button>
          </div>
          
          <div className="space-y-3">
            <div>
              <label className="text-xs text-[#a0a0b0] mb-1 block">
                Sleep after (minutes): {sleepMinutes}
              </label>
              <input
                type="range"
                min="1"
                max="60"
                value={sleepMinutes}
                onChange={(e) => setSleepMinutes(Number(e.target.value))}
                className="w-full"
              />
            </div>
            
            {currentUpgrade?.sleep_scheduled_at && (
              <div className="p-2 bg-[#0a0a0f] rounded text-xs">
                <Clock className="w-3 h-3 inline mr-1 text-[#ffa502]" />
                Auto-sleep at: {new Date(currentUpgrade.sleep_scheduled_at).toLocaleTimeString()}
              </div>
            )}
            
            <div className="flex gap-2">
              <button
                onClick={() => handleExtendSleep(10)}
                className="flex-1 py-1.5 text-xs bg-[#2a2a3a] hover:bg-[#3a3a4a] rounded transition-colors"
              >
                +10 min
              </button>
              <button
                onClick={() => handleExtendSleep(30)}
                className="flex-1 py-1.5 text-xs bg-[#2a2a3a] hover:bg-[#3a3a4a] rounded transition-colors"
              >
                +30 min
              </button>
              <button
                onClick={() => handleExtendSleep(60)}
                className="flex-1 py-1.5 text-xs bg-[#2a2a3a] hover:bg-[#3a3a4a] rounded transition-colors"
              >
                +1 hr
              </button>
            </div>
          </div>
        </div>
      )}

      {/* GPU Pricing Overlay */}
      {showOverlay && (
        <div className="fixed inset-0 z-50 bg-[#0a0a0f]/90 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#12121a] border border-[#2a2a3a] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="p-6 border-b border-[#2a2a3a] flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Server className="w-6 h-6 text-[#00d4aa]" />
                  HF GPU Scaling
                </h2>
                <p className="text-[#a0a0b0] mt-1">
                  Upgrade to dedicated GPU for instant inference
                </p>
              </div>
              <button
                onClick={() => setShowOverlay(false)}
                className="p-2 rounded-lg hover:bg-[#2a2a3a] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Status */}
            <div className="p-6 bg-[#00d4aa]/5 border-b border-[#2a2a3a]">
              <div className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${isUpgraded ? 'bg-green-500 animate-pulse' : 'bg-[#a0a0b0]'}`} />
                <div>
                  <p className="font-medium">Current: {pricing.find(p => p.id === currentTier)?.name || 'Zero GPU'}</p>
                  <p className="text-sm text-[#a0a0b0]">
                    {isUpgraded 
                      ? `Billing at $${pricing.find(p => p.id === currentTier)?.price_per_hour}/hour` 
                      : 'Free tier - shared CPU resources'}
                  </p>
                </div>
              </div>
            </div>

            {/* GPU Options */}
            <div className="p-6">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-medium text-lg">Select GPU Tier</h3>
                <div className="flex items-center gap-2 text-sm text-[#a0a0b0]">
                  <Clock className="w-4 h-4" />
                  <span>Auto-sleep after: {sleepMinutes} min</span>
                  <input
                    type="range"
                    min="1"
                    max="60"
                    value={sleepMinutes}
                    onChange={(e) => setSleepMinutes(Number(e.target.value))}
                    className="w-24"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {pricing.map((gpu) => (
                  <div
                    key={gpu.id}
                    className={`relative p-4 rounded-xl border-2 transition-all cursor-pointer ${
                      currentTier === gpu.id
                        ? 'border-[#00d4aa] bg-[#00d4aa]/10'
                        : 'border-[#2a2a3a] hover:border-[#00d4aa]/50 bg-[#1a1a25]'
                    } ${gpu.id === 'zero' ? 'opacity-75' : ''}`}
                    onClick={() => gpu.id !== 'zero' && handleUpgrade(gpu.id)}
                  >
                    {/* Recommended Badge */}
                    {gpu.recommended && (
                      <div className="absolute -top-2 -right-2 px-2 py-0.5 bg-[#00d4aa] text-[#0a0a0f] text-xs font-bold rounded-full">
                        BEST VALUE
                      </div>
                    )}

                    {/* Current Badge */}
                    {currentTier === gpu.id && (
                      <div className="absolute top-2 right-2">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      </div>
                    )}

                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        gpu.id === 'zero' ? 'bg-[#2a2a3a]' : 'bg-[#00d4aa]/20'
                      }`}>
                        {getTierIcon(gpu.id)}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-bold">{gpu.name}</h4>
                        <p className="text-xs text-[#a0a0b0] mt-0.5">{gpu.gpu_type}</p>
                      </div>
                    </div>

                    <div className="mt-3 space-y-1">
                      <div className="flex items-center gap-2 text-sm">
                        <Cpu className="w-4 h-4 text-[#a0a0b0]" />
                        <span>{gpu.vram_gb > 0 ? `${gpu.vram_gb}GB VRAM` : 'Shared'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <DollarSign className="w-4 h-4 text-[#a0a0b0]" />
                        <span className={gpu.price_per_hour === 0 ? 'text-green-400' : 'text-[#00d4aa]'}>
                          {gpu.price_per_hour === 0 ? 'FREE' : `$${gpu.price_per_hour}/hour`}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-[#a0a0b0]" />
                        <span>${gpu.price_per_minute}/min</span>
                      </div>
                    </div>

                    <p className="mt-3 text-xs text-[#a0a0b0]">{gpu.description}</p>

                    {/* Cost Estimates */}
                    {gpu.price_per_hour > 0 && (
                      <div className="mt-3 pt-3 border-t border-[#2a2a3a]">
                        <p className="text-xs text-[#a0a0b0] mb-1">Est. costs:</p>
                        <div className="flex gap-3 text-xs">
                          <span>10min: <strong>${(gpu.price_per_hour / 6).toFixed(2)}</strong></span>
                          <span>1hr: <strong>${gpu.price_per_hour.toFixed(2)}</strong></span>
                        </div>
                      </div>
                    )}

                    {gpu.id === 'zero' && (
                      <div className="mt-3 pt-3 border-t border-[#2a2a3a] text-center">
                        <span className="text-xs text-[#a0a0b0]">Currently selected</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Info Box */}
              <div className="mt-6 p-4 bg-[#00d4aa]/10 border border-[#00d4aa]/30 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-[#00d4aa] flex-shrink-0 mt-0.5" />
                <div className="text-sm text-[#a0a0b0]">
                  <p className="text-white font-medium mb-1">Auto-Sleep Feature</p>
                  <p>
                    By default, GPUs automatically downgrade to Zero after {sleepMinutes} minutes 
                    of inactivity to prevent runaway billing. Extend this timer anytime from the 
                    sleep settings. You only pay for actual GPU time used.
                  </p>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-[#2a2a3a] flex items-center justify-between">
              <div className="text-sm text-[#a0a0b0]">
                Space: <code className="bg-[#1a1a25] px-2 py-0.5 rounded">{spaceId}</code>
              </div>
              <button
                onClick={() => setShowOverlay(false)}
                className="px-6 py-2 rounded-lg bg-[#2a2a3a] hover:bg-[#3a3a4a] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GPUScaler;
