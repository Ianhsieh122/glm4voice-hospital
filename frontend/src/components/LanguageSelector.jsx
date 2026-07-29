import { useVoiceStore } from '../store/voiceStore'

const languages = [
  { value: 'zh-tw', label: '繁體中文 (國語)', flag: '🇹🇼' },
  { value: 'nan', label: '台語 (Taigi)', flag: '🗣️' },
  { value: 'en', label: 'English', flag: '🇺🇸' },
]

export default function LanguageSelector() {
  const { language, setLanguage } = useVoiceStore()
  
  return (
    <div className="flex space-x-2">
      {languages.map((lang) => (
        <button
          key={lang.value}
          onClick={() => setLanguage(lang.value)}
          className={`
            flex-1 px-4 py-2 rounded-lg text-sm font-medium
            transition-all duration-200
            ${language === lang.value
              ? 'bg-blue-600 text-white shadow-md'
              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
            }
          `}
        >
          <span className="mr-1">{lang.flag}</span>
          {lang.label}
        </button>
      ))}
    </div>
  )
}
