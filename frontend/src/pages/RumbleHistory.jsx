import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { FileAudio, RefreshCw, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'

export default function RumbleHistory() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [copied, setCopied] = useState(false)

  const loadHistory = () => {
    setLoading(true)
    api.getRumbleHistory(200).then((data) => {
      setItems(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => { loadHistory() }, [])

  useEffect(() => {
    const onFocus = () => loadHistory()
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [])

  const toggleItem = (id) => {
    setExpanded(expanded === id ? null : id)
    setCopied(false)
  }

  const copyTranscript = (text) => {
    navigator.clipboard.writeText(text || '').then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const fmtDate = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleString(undefined, { timeZoneName: 'short' })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Rumble Transcript History</h1>
        <button onClick={loadHistory} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
          <FileAudio className="w-10 h-10" />
          <p>No Rumble transcripts saved yet.</p>
          <p className="text-sm">Analyze a Rumble video and the transcript will be stored here for reuse.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-2 max-w-3xl">
          {items.map((item) => (
            <div key={item.id} className="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleItem(item.id)}
                className="w-full flex items-center justify-between gap-4 p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-900/40 transition-colors"
              >
                <div className="min-w-0">
                  <p className="font-medium truncate">{item.title || item.video_id}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {item.channel && <span>{item.channel} · </span>}
                    <span className="font-mono">v{item.video_id}</span>
                    {item.duration && <span> · {item.duration}</span>}
                    {item.created_at && <span> · {fmtDate(item.created_at)}</span>}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">
                    {item.method === 'subtitles' ? 'Subtitles' : 'MAI-Transcribe 2'}
                  </span>
                  {expanded === item.id ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </div>
              </button>

              {expanded === item.id && (
                <div className="border-t border-gray-200 dark:border-gray-800 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                      <p><span className="font-medium">Video ID:</span> <span className="font-mono">{item.video_id}</span></p>
                      <p><span className="font-medium">Channel:</span> {item.channel || '—'}</p>
                      <p><span className="font-medium">Views:</span> {item.view_count ? Number(item.view_count).toLocaleString() : '—'}</p>
                      <p><span className="font-medium">Duration:</span> {item.duration || '—'}</p>
                      <p><span className="font-medium">Transcription:</span> {item.method === 'subtitles' ? 'Subtitles' : 'Microsoft MAI-Transcribe 2 ($0.10/hr)'}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyTranscript(item.transcript)}
                        className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                      <a
                        href={item.url || `https://rumble.com/v${item.video_id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-700"
                      >
                        Open Video
                      </a>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded p-3 max-h-96 overflow-y-auto whitespace-pre-wrap text-sm font-mono">
                    {item.transcript || '(empty transcript)'}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}