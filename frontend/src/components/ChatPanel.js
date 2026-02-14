/**
 * EDEN UI REALISM ENGINE - Chat Panel Component
 * =============================================
 * Natural language chat with drag & drop support.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Send, Image as ImageIcon, Film, Trash2, Bot, User, Paperclip, X } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../hooks/useStore';
import { sendChatMessage, uploadFile } from '../services/api';

const ChatPanel = () => {
  const { 
    chatMessages, 
    addChatMessage, 
    clearChat, 
    sessionId,
    setLastGeneration,
    setGenerating 
  } = useStore();

  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Handle file drop
  const onDrop = useCallback(async (acceptedFiles) => {
    const newAttachments = [];
    
    for (const file of acceptedFiles) {
      try {
        const response = await uploadFile(file);
        newAttachments.push({
          id: response.data.file_id,
          name: file.name,
          url: response.data.url,
          type: file.type.startsWith('image/') ? 'image' : 'video',
          path: response.data.path
        });
        toast.success(`Uploaded ${file.name}`);
      } catch (error) {
        toast.error(`Failed to upload ${file.name}`);
      }
    }
    
    setAttachments((prev) => [...prev, ...newAttachments]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.gif'],
      'video/*': ['.mp4', '.webm', '.mov'],
    },
    noClick: true,
    noKeyboard: true,
  });

  // Send message
  const handleSendMessage = async () => {
    if (!inputMessage.trim() && attachments.length === 0) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage || (attachments.length > 0 ? 'Uploaded media:' : ''),
      attachments: attachments,
      timestamp: new Date().toISOString(),
    };

    addChatMessage(userMessage);
    setInputMessage('');
    setAttachments([]);
    setIsTyping(true);

    try {
      const response = await sendChatMessage(
        inputMessage,
        sessionId,
        attachments
      );

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        suggestedPrompt: response.data.suggested_prompt,
        suggestedSettings: response.data.suggested_settings,
        timestamp: new Date().toISOString(),
      };

      addChatMessage(assistantMessage);

      // If there's a suggested prompt, set it for generation
      if (response.data.suggested_prompt) {
        setLastGeneration({
          suggestedPrompt: response.data.suggested_prompt,
          suggestedSettings: response.data.suggested_settings,
        });
      }
    } catch (error) {
      toast.error('Failed to get response from EDEN');
      console.error(error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const removeAttachment = (id) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const quickCommands = [
    { label: '/enhance', desc: 'Enhance a prompt' },
    { label: '/negative', desc: 'Get negative keywords' },
    { label: '/preset', desc: 'Load a preset' },
  ];

  return (
    <div className="h-full flex flex-col bg-[#12121a]" {...getRootProps()}>
      <input {...getInputProps()} />

      {/* Drag Overlay */}
      {isDragActive && (
        <div className="absolute inset-0 z-50 bg-[#00d4aa]/20 border-2 border-dashed border-[#00d4aa] flex items-center justify-center backdrop-blur-sm">
          <div className="text-center">
            <ImageIcon className="w-16 h-16 text-[#00d4aa] mx-auto mb-4" />
            <p className="text-xl font-semibold text-[#00d4aa]">Drop files here</p>
            <p className="text-sm text-[#a0a0b0]">Images or videos for generation</p>
          </div>
        </div>
      )}

      {/* Chat Header */}
      <div className="p-4 border-b border-[#2a2a3a] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-[#00d4aa]" />
          <span className="font-semibold">EDEN Assistant</span>
        </div>
        <button
          onClick={clearChat}
          className="p-2 hover:bg-[#2a2a3a] rounded-lg transition-colors"
          title="Clear chat"
        >
          <Trash2 className="w-4 h-4 text-[#a0a0b0]" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatMessages.length === 0 && (
          <div className="text-center text-[#a0a0b0] mt-8">
            <Bot className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">Welcome to EDEN</p>
            <p className="text-sm max-w-xs mx-auto">
              Describe what you want to create, or drag & drop images/videos here.
            </p>
            <div className="mt-6 space-y-2">
              <p className="text-xs uppercase tracking-wider text-[#a0a0b0]">Quick Commands</p>
              {quickCommands.map((cmd) => (
                <button
                  key={cmd.label}
                  onClick={() => setInputMessage(cmd.label + ' ')}
                  className="block w-full text-left px-3 py-2 rounded-lg bg-[#1a1a25] hover:bg-[#2a2a3a] text-sm transition-colors"
                >
                  <span className="text-[#00d4aa] font-mono">{cmd.label}</span>
                  <span className="text-[#a0a0b0] ml-2">- {cmd.desc}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {chatMessages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-[#00d4aa] text-[#0a0a0f] rounded-br-md'
                  : 'bg-[#1a1a25] border border-[#2a2a3a] rounded-bl-md'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                {message.role === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4 text-[#00d4aa]" />
                )}
                <span className="text-xs opacity-70">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <div className="whitespace-pre-wrap text-sm">{message.content}</div>

              {/* Attachments */}
              {message.attachments && message.attachments.length > 0 && (
                <div className="mt-2 space-y-2">
                  {message.attachments.map((attachment) => (
                    <div key={attachment.id} className="rounded-lg overflow-hidden">
                      {attachment.type === 'image' ? (
                        <img
                          src={`http://localhost:8000${attachment.url}`}
                          alt={attachment.name}
                          className="max-w-full h-auto max-h-48 object-cover"
                        />
                      ) : (
                        <video
                          src={`http://localhost:8000${attachment.url}`}
                          className="max-w-full max-h-48"
                          controls
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Suggested Actions */}
              {message.suggestedPrompt && (
                <div className="mt-3 p-2 bg-[#0a0a0f]/50 rounded-lg">
                  <p className="text-xs text-[#a0a0b0] mb-1">Suggested Prompt:</p>
                  <p className="text-sm font-medium text-[#00d4aa]">{message.suggestedPrompt}</p>
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-[#1a1a25] border border-[#2a2a3a] rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-[#00d4aa]" />
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-[#00d4aa] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-[#00d4aa] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-[#00d4aa] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-[#2a2a3a]">
        {/* Attachments Preview */}
        {attachments.length > 0 && (
          <div className="flex gap-2 mb-3 overflow-x-auto pb-2">
            {attachments.map((attachment) => (
              <div key={attachment.id} className="relative flex-shrink-0">
                {attachment.type === 'image' ? (
                  <div className="w-16 h-16 rounded-lg bg-[#1a1a25] flex items-center justify-center">
                    <ImageIcon className="w-6 h-6 text-[#00d4aa]" />
                  </div>
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-[#1a1a25] flex items-center justify-center">
                    <Film className="w-6 h-6 text-[#00d4aa]" />
                  </div>
                )}
                <button
                  onClick={() => removeAttachment(attachment.id)}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-[#ff4757] rounded-full flex items-center justify-center"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <label className="p-3 rounded-lg bg-[#1a1a25] hover:bg-[#2a2a3a] cursor-pointer transition-colors">
            <Paperclip className="w-5 h-5 text-[#a0a0b0]" />
            <input
              type="file"
              className="hidden"
              accept="image/*,video/*"
              onChange={(e) => {
                if (e.target.files) {
                  onDrop(Array.from(e.target.files));
                }
              }}
            />
          </label>

          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe what you want to create..."
            className="flex-1 input-eden"
          />

          <button
            onClick={handleSendMessage}
            disabled={(!inputMessage.trim() && attachments.length === 0) || isTyping}
            className="p-3 rounded-lg bg-[#00d4aa] text-[#0a0a0f] hover:bg-[#00b894] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
