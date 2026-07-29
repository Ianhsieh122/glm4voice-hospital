import { motion, AnimatePresence } from 'framer-motion'
import { User, Bot } from 'lucide-react'

export default function TranscriptDisplay({ transcript, response }) {
  return (
    <div className="space-y-4 max-h-64 overflow-y-auto">
      {/* User transcript */}
      <AnimatePresence>
        {transcript && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="flex items-start space-x-3"
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <User className="w-4 h-4 text-blue-600" />
            </div>
            <div className="flex-1 bg-blue-50 rounded-2xl rounded-tl-none px-4 py-3">
              <p className="text-sm text-gray-800">{transcript}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* AI response */}
      <AnimatePresence>
        {response && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="flex items-start space-x-3 flex-row-reverse"
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-purple-600" />
            </div>
            <div className="flex-1 bg-purple-50 rounded-2xl rounded-tr-none px-4 py-3">
              <p className="text-sm text-gray-800">{response}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Placeholder when empty */}
      {!transcript && !response && (
        <div className="text-center py-8 text-gray-400">
          <p className="text-sm">開始對話，我會幫您服務</p>
          <p className="text-xs mt-1">Start speaking, I'm here to help</p>
        </div>
      )}
    </div>
  )
}
