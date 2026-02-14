/**
 * EDEN UI REALISM ENGINE - State Management
 * ==========================================
 * Zustand store for global state management.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set, get) => ({
      // Session
      sessionId: null,
      setSessionId: (id) => set({ sessionId: id }),

      // UI State
      activeTab: 'images', // 'images' | 'videos' | 'playground' | 'models' | 'settings'
      setActiveTab: (tab) => set({ activeTab: tab }),

      // Models
      currentModel: 'stabilityai/stable-diffusion-xl-base-1.0',
      downloadedModels: [],
      setCurrentModel: (model) => set({ currentModel: model }),
      setDownloadedModels: (models) => set({ downloadedModels: models }),

      // Generation State
      isGenerating: false,
      generationProgress: 0,
      lastGeneration: null,
      setGenerating: (status) => set({ isGenerating: status }),
      setGenerationProgress: (progress) => set({ generationProgress: progress }),
      setLastGeneration: (result) => set({ lastGeneration: result }),

      // Chat State
      chatMessages: [],
      addChatMessage: (message) => set((state) => ({
        chatMessages: [...state.chatMessages, message]
      })),
      clearChat: () => set({ chatMessages: [] }),

      // Image Settings
      imageSettings: {
        width: 1024,
        height: 1024,
        steps: 30,
        guidanceScale: 7.5,
        scheduler: 'DPM++ 2M Karras',
        useEdenNegative: true,
        seed: -1,
      },
      setImageSettings: (settings) => set((state) => ({
        imageSettings: { ...state.imageSettings, ...settings }
      })),

      // Video Settings
      videoSettings: {
        width: 832,
        height: 480,
        numFrames: 16,
        fps: 8,
        steps: 25,
        guidanceScale: 6.0,
        scheduler: 'DDIM',
        useEdenNegative: true,
        seed: -1,
      },
      setVideoSettings: (settings) => set((state) => ({
        videoSettings: { ...state.videoSettings, ...settings }
      })),

      // Generation History
      generationHistory: [],
      addToHistory: (item) => set((state) => ({
        generationHistory: [item, ...state.generationHistory].slice(0, 50)
      })),

      // System
      systemStatus: null,
      setSystemStatus: (status) => set({ systemStatus: status }),

      // Playground
      comfyUIConnected: false,
      setComfyUIConnected: (connected) => set({ comfyUIConnected: connected }),

      // Negative Keywords
      customNegativeAdditions: '',
      setCustomNegativeAdditions: (text) => set({ customNegativeAdditions: text }),
    }),
    {
      name: 'eden-ui-storage',
      partialize: (state) => ({
        sessionId: state.sessionId,
        imageSettings: state.imageSettings,
        videoSettings: state.videoSettings,
        customNegativeAdditions: state.customNegativeAdditions,
        currentModel: state.currentModel,
      }),
    }
  )
);

export default useStore;
