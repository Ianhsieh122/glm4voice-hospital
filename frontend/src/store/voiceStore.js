import { create } from 'zustand'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/conversation'

export const useVoiceStore = create((set, get) => ({
  // Connection state
  ws: null,
  isConnected: false,
  
  // Voice state
  isListening: false,
  isSpeaking: false,
  
  // Language
  language: 'zh-tw', // zh-tw, nan, en
  
  // Conversation
  transcript: '',
  response: '',
  conversationHistory: [],
  
  // Audio
  audioContext: null,
  audioQueue: [],
  mediaRecorder: null,
  audioStream: null,
  
  // Actions
  connect: async () => {
    const ws = new WebSocket(WS_URL)
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected')
      set({ isConnected: true, ws })
      
      // Initialize audio context
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      set({ audioContext })
    }
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        get().handleMessage(message)
      } catch (error) {
        console.error('Failed to parse message:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
    }
    
    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected')
      set({ isConnected: false, ws: null })
      
      // Cleanup
      get().cleanup()
    }
    
    set({ ws })
  },
  
  disconnect: () => {
    const { ws } = get()
    if (ws) {
      ws.close()
    }
    get().cleanup()
  },
  
  cleanup: () => {
    const { mediaRecorder, audioStream, audioContext } = get()
    
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    
    if (audioStream) {
      audioStream.getTracks().forEach(track => track.stop())
    }
    
    if (audioContext && audioContext.state !== 'closed') {
      audioContext.close()
    }
    
    set({
      mediaRecorder: null,
      audioStream: null,
      audioContext: null,
      isListening: false,
      isSpeaking: false,
      audioQueue: [],
    })
  },
  
  handleMessage: (message) => {
    const { type } = message
    
    switch (type) {
      case 'status':
        console.log('📊 Status:', message.message)
        if (message.message === 'listening') {
          set({ isListening: true })
        } else if (message.message === 'interrupted') {
          set({ isSpeaking: false, audioQueue: [] })
        }
        break
      
      case 'transcript':
        console.log('📝 Transcript:', message.text)
        set({ transcript: message.text })
        get().addToHistory('user', message.text)
        break
      
      case 'response_text':
        console.log('💬 Response:', message.text)
        set({ response: message.text, isSpeaking: true })
        get().addToHistory('assistant', message.text)
        break
      
      case 'response_audio':
        // Play audio chunk
        get().playAudioChunk(message.data)
        break
      
      case 'response_complete':
        console.log('✅ Response complete')
        set({ isSpeaking: false })
        break
      
      case 'error':
        console.error('❌ Error:', message.message)
        alert(`錯誤: ${message.message}`)
        break
      
      default:
        console.log('Unknown message type:', type)
    }
  },
  
  startListening: async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
      })
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          get().sendAudioChunk(event.data)
        }
      }
      
      mediaRecorder.start(100) // Send chunks every 100ms
      
      set({
        mediaRecorder,
        audioStream: stream,
        isListening: true,
      })
      
      console.log('🎤 Started listening')
    } catch (error) {
      console.error('Failed to start listening:', error)
      alert('無法存取麥克風，請檢查權限設定')
    }
  },
  
  stopListening: () => {
    const { mediaRecorder } = get()
    
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    
    set({ isListening: false })
    console.log('🛑 Stopped listening')
  },
  
  sendAudioChunk: async (audioBlob) => {
    const { ws, language, isConnected } = get()
    
    if (!ws || !isConnected) {
      return
    }
    
    try {
      // Convert blob to base64
      const reader = new FileReader()
      reader.readAsDataURL(audioBlob)
      reader.onloadend = () => {
        const base64Audio = reader.result.split(',')[1]
        
        // Send to server
        ws.send(JSON.stringify({
          type: 'audio_chunk',
          data: base64Audio,
          language,
          timestamp: Date.now(),
        }))
      }
    } catch (error) {
      console.error('Failed to send audio chunk:', error)
    }
  },
  
  playAudioChunk: async (base64Audio) => {
    const { audioContext, audioQueue } = get()
    
    if (!audioContext) {
      return
    }
    
    try {
      // Decode base64 to array buffer
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // Decode audio data
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer)
      
      // Play audio
      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContext.destination)
      source.start()
      
      // Add to queue for tracking
      set({ audioQueue: [...audioQueue, source] })
      
      // Remove from queue when finished
      source.onended = () => {
        const queue = get().audioQueue.filter(s => s !== source)
        set({ audioQueue: queue })
      }
    } catch (error) {
      console.error('Failed to play audio chunk:', error)
    }
  },
  
  interrupt: () => {
    const { ws, isConnected, audioQueue } = get()
    
    if (!ws || !isConnected) {
      return
    }
    
    // Stop all playing audio
    audioQueue.forEach(source => {
      try {
        source.stop()
      } catch (e) {
        // Ignore if already stopped
      }
    })
    
    // Send interrupt signal
    ws.send(JSON.stringify({
      type: 'interrupt',
      timestamp: Date.now(),
    }))
    
    set({
      isSpeaking: false,
      audioQueue: [],
    })
    
    console.log('🛑 Interrupted')
  },
  
  setLanguage: (language) => {
    const { ws, isConnected } = get()
    
    set({ language })
    
    // Send config update
    if (ws && isConnected) {
      ws.send(JSON.stringify({
        type: 'config',
        language,
        timestamp: Date.now(),
      }))
    }
    
    console.log('🌐 Language changed:', language)
  },
  
  addToHistory: (role, content) => {
    const { conversationHistory } = get()
    
    set({
      conversationHistory: [
        ...conversationHistory,
        {
          role,
          content,
          timestamp: Date.now(),
        }
      ]
    })
  },
  
  clearHistory: () => {
    set({
      conversationHistory: [],
      transcript: '',
      response: '',
    })
  },
}))
