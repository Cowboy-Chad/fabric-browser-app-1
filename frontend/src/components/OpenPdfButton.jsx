import { useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { generatePdfBlob } from './pdfUtils'

export default function OpenPdfButton({ text, title = '' }) {
  const [loading, setLoading] = useState(false)

  const handleOpen = () => {
    setLoading(true)
    const blob = generatePdfBlob(text)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 60000)
    setLoading(false)
  }

  return (
    <button
      onClick={handleOpen}
      disabled={loading}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-800/40 transition-colors disabled:opacity-50"
    >
      <ExternalLink className="w-3.5 h-3.5" />
      {loading ? 'Opening...' : 'Open PDF'}
    </button>
  )
}