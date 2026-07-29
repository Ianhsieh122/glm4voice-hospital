import { useState, useEffect } from 'react'
import { Mic, MicOff, Languages, Settings, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useVoiceStore } from './store/voiceStore'
import VoiceAvatar from './components/VoiceAvatar'
import TranscriptDisplay from './components/TranscriptDisplay'
import LanguageSelector from './components/LanguageSelector'
import StatusIndicator from './components/StatusIndicator'
import ConnectionStatus from './components/ConnectionStatus'

function App() {
  const {
    isConnected,
    isListening,
    isSpeaking,
    language,
    transcript,
    response,
    connect,
    disconnect,
    startListening,
    stopListening,
    interrupt,
  } = useVoiceStore()

  const [showSettings, setShowSettings] = useState(false)

  useEffect(() => {
    // Auto-connect on mount
    connect()
    
    return () => {
      disconnect()
    }
  }, [])

  const handleToggleMic = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  const handleInterrupt = () => {
    if (isSpeaking) {
      interrupt()
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Main Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/95 backdrop-blur-lg rounded-3xl shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="w-8 h-8 text-white" />
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Opus Hospital
                </h1>
                <p className="text-sm text-blue-100">
                  AI 智能櫃台
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <ConnectionStatus isConnected={isConnected} />
              
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
              >
                <Settings className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        <AnimatePresence>
          {showSettings && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-b border-gray-200 bg-gray-50 px-6 py-4"
            >
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    <Languages className="w-4 h-4 inline mr-1" />
                    語言 / Language
                  </label>
                  <LanguageSelector />
                </div>
                
                <div className="text-xs text-gray-500">
                  <p>🎯 支援語言: 繁體中文 • 台語 • English</p>
                  <p>⚡ 延遲: {'<'}500ms | 🤖 模型: TAIDE 2.0 + Qwen3</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="px-6 py-8">
          {/* Avatar */}
          <div className="flex justify-center mb-8">
            <VoiceAvatar
              isListening={isListening}
              isSpeaking={isSpeaking}
              isConnected={isConnected}
            />
          </div>

          {/* Status */}
          <div className="mb-6">
            <StatusIndicator
              isListening={isListening}
              isSpeaking={isSpeaking}
              isConnected={isConnected}
            />
          </div>

          {/* Transcript Display */}
          <div className="mb-8">
            <TranscriptDisplay
              transcript={transcript}
              response={response}
            />
          </div>

          {/* Controls */}
          <div className="flex justify-center space-x-4">
            {/* Mic Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleToggleMic}
              disabled={!isConnected}
              className={`
                relative w-16 h-16 rounded-full flex items-center justify-center
                transition-all duration-300 shadow-lg
                ${isListening 
                  ? 'bg-red-500 hover:bg-red-600' 
                  : 'bg-blue-600 hover:bg-blue-700'
                }
                ${!isConnected && 'opacity-50 cursor-not-allowed'}
              `}
            >
              {isListening ? (
                <MicOff className="w-7 h-7 text-white" />
              ) : (
                <Mic className="w-7 h-7 text-white" />
              )}
              
              {/* Pulse animation when listening */}
              {isListening && (
                <motion.div
                  className="absolute inset-0 rounded-full bg-red-400"
                  animate={{
                    scale: [1, 1.3, 1],
                    opacity: [0.5, 0, 0.5],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />
              )}
            </motion.button>

            {/* Interrupt Button */}
            {isSpeaking && (
              <motion.button
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleInterrupt}
                className="
                  px-6 py-3 rounded-full 
                  bg-orange-500 hover:bg-orange-600
                  text-white font-medium
                  shadow-lg transition-colors
                "
              >
                🛑 打斷
              </motion.button>
            )}
          </div>

          {/* Quick Actions */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500 text-center mb-3">
              常見問題 Quick Actions
            </p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { text: '我想掛號', lang: 'zh-tw' },
                { text: '查詢門診時間', lang: 'zh-tw' },
                { text: '我欲掛心臟科', lang: 'nan' },
                { text: 'Make appointment', lang: 'en' },
              ].map((action, i) => (
                <button
                  key={i}
                  onClick={() => {
                    // TODO: Send quick action
                  }}
                  className="
                    px-4 py-2 rounded-lg text-sm
                    bg-gray-100 hover:bg-gray-200
                    text-gray-700 transition-colors
                  "
                >
                  {action.text}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-3 text-center text-xs text-gray-500 border-t">
          <p>Powered by TAIDE 2.0 • Qwen3-ASR • Qwen3-TTS</p>
          <p>AMD MI300X Optimized • &lt;500ms Latency</p>
        </div>
      </motion.div>

      {/* Help Text */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-6 text-center text-white/80 text-sm"
      >
        <p>點擊麥克風開始對話 • 可隨時打斷 AI 回應</p>
        <p className="text-xs mt-1 text-white/60">
          Click microphone to start • Interrupt anytime
        </p>
      </motion.div>
    </div>
  )
}

export default App
