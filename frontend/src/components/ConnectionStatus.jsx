import { Wifi, WifiOff } from 'lucide-react'
import { motion } from 'framer-motion'

export default function ConnectionStatus({ isConnected }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={`
        flex items-center space-x-2 px-3 py-1 rounded-full
        ${isConnected 
          ? 'bg-green-500/20 text-green-100' 
          : 'bg-red-500/20 text-red-100'
        }
      `}
    >
      {isConnected ? (
        <Wifi className="w-4 h-4" />
      ) : (
        <WifiOff className="w-4 h-4" />
      )}
      <span className="text-xs font-medium">
        {isConnected ? '已連線' : '未連線'}
      </span>
    </motion.div>
  )
}
