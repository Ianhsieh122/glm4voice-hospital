import { motion } from 'framer-motion'
import { Mic, Volume2, Loader2 } from 'lucide-react'

export default function VoiceAvatar({ isListening, isSpeaking, isConnected }) {
  const getAvatarState = () => {
    if (!isConnected) return 'disconnected'
    if (isSpeaking) return 'speaking'
    if (isListening) return 'listening'
    return 'idle'
  }
  
  const state = getAvatarState()
  
  const stateColors = {
    idle: 'from-blue-400 to-blue-600',
    listening: 'from-green-400 to-green-600',
    speaking: 'from-purple-400 to-purple-600',
    disconnected: 'from-gray-400 to-gray-600',
  }
  
  const stateIcons = {
    idle: Mic,
    listening: Mic,
    speaking: Volume2,
    disconnected: Loader2,
  }
  
  const Icon = stateIcons[state]
  
  return (
    <div className="relative">
      {/* Outer ring - animated */}
      <motion.div
        className={`
          absolute inset-0 rounded-full 
          bg-gradient-to-br ${stateColors[state]}
          opacity-20
        `}
        animate={{
          scale: state === 'listening' ? [1, 1.2, 1] : state === 'speaking' ? [1, 1.1, 1] : 1,
        }}
        transition={{
          duration: state === 'speaking' ? 0.6 : 1.5,
          repeat: (state === 'listening' || state === 'speaking') ? Infinity : 0,
          ease: "easeInOut",
        }}
      />
      
      {/* Middle ring */}
      <motion.div
        className={`
          absolute inset-2 rounded-full 
          bg-gradient-to-br ${stateColors[state]}
          opacity-40
        `}
        animate={{
          scale: state === 'speaking' ? [1, 1.05, 1] : 1,
        }}
        transition={{
          duration: 0.8,
          repeat: state === 'speaking' ? Infinity : 0,
          ease: "easeInOut",
        }}
      />
      
      {/* Avatar circle */}
      <motion.div
        className={`
          relative w-32 h-32 rounded-full 
          bg-gradient-to-br ${stateColors[state]}
          flex items-center justify-center
          shadow-2xl
        `}
        animate={{
          scale: state === 'listening' ? [1, 1.05, 1] : 1,
        }}
        transition={{
          duration: 1.5,
          repeat: state === 'listening' ? Infinity : 0,
          ease: "easeInOut",
        }}
      >
        <motion.div
          animate={{
            rotate: state === 'disconnected' ? 360 : 0,
          }}
          transition={{
            duration: 1,
            repeat: state === 'disconnected' ? Infinity : 0,
            ease: "linear",
          }}
        >
          <Icon className="w-12 h-12 text-white" />
        </motion.div>
      </motion.div>
      
      {/* Pulse rings when speaking */}
      {state === 'speaking' && (
        <>
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-purple-400"
            animate={{
              scale: [1, 1.4],
              opacity: [0.6, 0],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-purple-400"
            animate={{
              scale: [1, 1.4],
              opacity: [0.6, 0],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "easeOut",
              delay: 0.3,
            }}
          />
        </>
      )}
    </div>
  )
}
