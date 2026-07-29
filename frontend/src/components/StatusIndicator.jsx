import { motion } from 'framer-motion'

export default function StatusIndicator({ isListening, isSpeaking, isConnected }) {
  const getStatus = () => {
    if (!isConnected) return { text: '連線中...', color: 'text-gray-500', bgColor: 'bg-gray-100' }
    if (isSpeaking) return { text: '正在回答...', color: 'text-purple-600', bgColor: 'bg-purple-50' }
    if (isListening) return { text: '正在聆聽...', color: 'text-green-600', bgColor: 'bg-green-50' }
    return { text: '待機中', color: 'text-blue-600', bgColor: 'bg-blue-50' }
  }
  
  const status = getStatus()
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        ${status.bgColor} ${status.color}
        px-4 py-2 rounded-full text-center
        font-medium text-sm
        inline-flex items-center justify-center
        mx-auto
      `}
    >
      {/* Animated dot */}
      {(isListening || isSpeaking) && (
        <motion.span
          className={`
            w-2 h-2 rounded-full mr-2
            ${isSpeaking ? 'bg-purple-600' : 'bg-green-600'}
          `}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [1, 0.5, 1],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      )}
      {status.text}
    </motion.div>
  )
}
