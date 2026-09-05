import { useState, useEffect, useRef } from 'react'
import { ChevronDown, Sparkles } from 'lucide-react'

const DEFAULT = 'deepseek/deepseek-v4-flash'

export default function ModelSelector({ models, selected, onChange }) {
  const [open, setOpen] = useState(false)
  const [hover, setHover] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-left"
      >
        <Sparkles className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
        <span className="truncate flex-1">{selected || DEFAULT}</span>
        <ChevronDown className={`w-3 h-3 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {hover && !open && (
        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-800 text-gray-100 text-xs px-3 py-1.5 rounded-lg whitespace-nowrap shadow-lg z-50 pointer-events-none">
          {selected || DEFAULT}
        </div>
      )}
      {open && (
        <div className="absolute bottom-full mb-1 left-0 right-0 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto z-50">
          {models.map((m) => (
            <button
              key={m}
              onClick={() => { onChange(m); setOpen(false) }}
              className={`w-full text-left px-3 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${
                m === selected ? 'text-emerald-600 dark:text-emerald-400 font-medium' : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}