/**
 * EDEN UI REALISM ENGINE - Main Application
 * =========================================
 * Main App component with the core layout.
 */
import React, { useEffect, useState } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import ChatPanel from './components/ChatPanel';
import PreviewPanel from './components/PreviewPanel';
import EDENImagesTab from './components/EDENImagesTab';
import EDENVideosTab from './components/EDENVideosTab';
import PlaygroundTab from './components/PlaygroundTab';
import ModelsTab from './components/ModelsTab';
import SettingsTab from './components/SettingsTab';
import useStore from './hooks/useStore';
import { getSystemStatus, getRecommendedModels } from './services/api';
import './styles/index.css';

function App() {
  const { 
    activeTab, 
    setActiveTab, 
    setSystemStatus, 
    setDownloadedModels,
    setSessionId,
    sessionId 
  } = useStore();

  const [isSidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    // Initialize session
    if (!sessionId) {
      setSessionId(`session-${Date.now()}`);
    }

    // Fetch system status
    const fetchStatus = async () => {
      try {
        const response = await getSystemStatus();
        setSystemStatus(response.data);
      } catch (error) {
        console.error('Failed to fetch system status:', error);
      }
    };

    // Fetch recommended models
    const fetchModels = async () => {
      try {
        const response = await getRecommendedModels();
        setDownloadedModels(response.data.models);
      } catch (error) {
        console.error('Failed to fetch models:', error);
      }
    };

    fetchStatus();
    fetchModels();

    // Poll system status
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [setSystemStatus, setDownloadedModels, sessionId, setSessionId]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'images':
        return <EDENImagesTab />;
      case 'videos':
        return <EDENVideosTab />;
      case 'playground':
        return <PlaygroundTab />;
      case 'models':
        return <ModelsTab />;
      case 'settings':
        return <SettingsTab />;
      default:
        return <EDENImagesTab />;
    }
  };

  return (
    <div className="min-h-screen eden-gradient">
      <Toaster 
        position="top-right" 
        toastOptions={{
          style: {
            background: '#1a1a25',
            color: '#fff',
            border: '1px solid #2a2a3a',
          },
        }}
      />
      
      <Header />
      
      {/* Main Layout: Chat (Left) | Preview/Controls (Right) */}
      <div className="flex h-[calc(100vh-64px)]">
        {/* Left Panel - Chat with Drag & Drop */}
        <div className={`${isSidebarOpen ? 'w-96' : 'w-0'} transition-all duration-300 overflow-hidden border-r border-[#2a2a3a]`}>
          <ChatPanel />
        </div>

        {/* Toggle Sidebar Button */}
        <button
          onClick={() => setSidebarOpen(!isSidebarOpen)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-[#1a1a25] border border-[#2a2a3a] p-2 rounded-r-lg hover:border-[#00d4aa] transition-colors"
        >
          {isSidebarOpen ? '◀' : '▶'}
        </button>

        {/* Right Panel - Preview and Controls */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Preview Area */}
          <div className="flex-1 overflow-hidden">
            <PreviewPanel />
          </div>

          {/* Tab Navigation - Large Buttons */}
          <div className="border-t border-[#2a2a3a] bg-[#12121a]">
            <div className="flex">
              <button
                onClick={() => setActiveTab('images')}
                className={`flex-1 py-5 font-display font-bold text-lg transition-all ${
                  activeTab === 'images' 
                    ? 'bg-gradient-to-r from-[#00d4aa]/20 to-transparent text-[#00d4aa] border-t-2 border-[#00d4aa]' 
                    : 'text-[#a0a0b0] hover:text-white'
                }`}
              >
                📷 EDEN IMAGES
              </button>
              <button
                onClick={() => setActiveTab('videos')}
                className={`flex-1 py-5 font-display font-bold text-lg transition-all ${
                  activeTab === 'videos' 
                    ? 'bg-gradient-to-r from-[#00d4aa]/20 to-transparent text-[#00d4aa] border-t-2 border-[#00d4aa]' 
                    : 'text-[#a0a0b0] hover:text-white'
                }`}
              >
                🎬 EDEN VIDEOS
              </button>
              <button
                onClick={() => setActiveTab('playground')}
                className={`flex-1 py-5 font-display font-bold text-lg transition-all ${
                  activeTab === 'playground' 
                    ? 'bg-gradient-to-r from-[#00d4aa]/20 to-transparent text-[#00d4aa] border-t-2 border-[#00d4aa]' 
                    : 'text-[#a0a0b0] hover:text-white'
                }`}
              >
                🎮 PLAYGROUND
              </button>
              <button
                onClick={() => setActiveTab('models')}
                className={`flex-1 py-5 font-display font-bold text-lg transition-all ${
                  activeTab === 'models' 
                    ? 'bg-gradient-to-r from-[#00d4aa]/20 to-transparent text-[#00d4aa] border-t-2 border-[#00d4aa]' 
                    : 'text-[#a0a0b0] hover:text-white'
                }`}
              >
                🤖 MODELS
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`flex-1 py-5 font-display font-bold text-lg transition-all ${
                  activeTab === 'settings' 
                    ? 'bg-gradient-to-r from-[#00d4aa]/20 to-transparent text-[#00d4aa] border-t-2 border-[#00d4aa]' 
                    : 'text-[#a0a0b0] hover:text-white'
                }`}
              >
                ⚙️ SETTINGS
              </button>
            </div>

            {/* Tab Content */}
            <div className="p-6 overflow-y-auto max-h-[40vh]">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
