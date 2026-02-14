/**
 * EDEN UI REALISM ENGINE - Header Component
 */
import React from 'react';
import { Cpu, Zap, Wifi, WifiOff } from 'lucide-react';
import useStore from '../hooks/useStore';

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
        {/* GPU Status */}
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isGPUAvailable ? 'bg-[#2ed573] animate-pulse' : 'bg-[#ff4757]'}`} />
          <span className="text-sm text-[#a0a0b0]">
            {isGPUAvailable ? systemStatus?.gpu?.name || 'GPU Ready' : 'CPU Mode'}
          </span>
          {isGPUAvailable && systemStatus?.gpu && (
            <span className="text-xs text-[#a0a0b0]">
              {Math.round(systemStatus.gpu.memory_allocated / 1024 / 1024 / 1024 * 100) / 100}GB / {Math.round(systemStatus.gpu.memory_total / 1024 / 1024 / 1024)}GB
            </span>
          )}
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

        {/* Quick Action */}
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00d4aa]/10 border border-[#00d4aa]/30 text-[#00d4aa] hover:bg-[#00d4aa]/20 transition-all">
          <Zap className="w-4 h-4" />
          <span className="text-sm font-medium">Turbo Mode</span>
        </button>
      </div>
    </header>
  );
};

export default Header;
