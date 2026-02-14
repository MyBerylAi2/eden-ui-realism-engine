/**
 * EDEN UI REALISM ENGINE - Header Component
 */
import React from 'react';
import { Cpu, Zap, Wifi, WifiOff } from 'lucide-react';
import useStore from '../hooks/useStore';
import GPUScaler from './GPUScaler';

const Header = () => {
  const { systemStatus } = useStore();

  const isGPUAvailable = systemStatus?.gpu?.available;

  return (
    <header className="h-16 border-b border-[#2a2a3a] bg-[#12121a]/80 backdrop-blur-md flex items-center justify-between px-6">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00d4aa] to-[#00b894] flex items-center justify-center">
          <Cpu className="w-6 h-6 text-[#0a0a0f]" />
        </div>
        <div>
          <h1 className="font-display font-bold text-xl text-white">
            EDEN UI
          </h1>
          <p className="text-xs text-[#00d4aa] font-medium tracking-wider">
            REALISM ENGINE
          </p>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="flex items-center gap-6">
        {/* HF GPU Scaler */}
        <GPUScaler spaceId="AIBRUH/video-studio" />

        {/* GPU Status */}
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isGPUAvailable ? 'bg-[#2ed573] animate-pulse' : 'bg-[#ff4757]'}`} />
          <span className="text-sm text-[#a0a0b0]">
            {isGPUAvailable ? 'Local GPU' : 'CPU Mode'}
          </span>
        </div>

        {/* API Status */}
        <div className="flex items-center gap-2">
          {systemStatus ? (
            <Wifi className="w-4 h-4 text-[#2ed573]" />
          ) : (
            <WifiOff className="w-4 h-4 text-[#ff4757]" />
          )}
          <span className="text-sm text-[#a0a0b0]">
            {systemStatus ? 'Connected' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Header;
