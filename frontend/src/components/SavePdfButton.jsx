import { useState } from 'react'
import { FileDown } from 'lucide-react'
import { generatePdfBlob } from './pdfUtils'

export default function SavePdfButton({ text, filename = 'osint-result', title = '' }) {
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      const blob = generatePdfBlob(text)
      const safeName = (title || filename).replace(/[^a-zA-Z0-9_\- ]/g, '_').slice(0, 100) + '.pdf'

      if ('showSaveFilePicker' in window) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: safeName,
            types: [{ description: 'PDF Document', accept: { 'application/pdf': ['.pdf'] } }],
          })
          const writable = await handle.createWritable()
          await writable.write(blob)
          await writable.close()
          setSaving(false)
          return
        } catch (err) {
          if (err.name === 'AbortError') { setSaving(false); return }
        }
      }

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = safeName
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('PDF save failed:', err)
    }
    setSaving(false)
  }

  return (
    <button
      onClick={handleSave}
      disabled={saving}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-800/40 transition-colors disabled:opacity-50"
    >
      <FileDown className="w-3.5 h-3.5" />
      {saving ? 'Saving...' : 'Save PDF'}
    </button>
  )
}