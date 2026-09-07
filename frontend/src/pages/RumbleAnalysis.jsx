import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import { useModel } from '../api/modelContext'
import { CheckCircle2, Loader2, Search, Download, AudioWaveform, Sparkles, TimerOff } from 'lucide-react'
import FormattedOutput from '../components/FormattedOutput'
import SavePdfButton from '../components/SavePdfButton'
import OpenPdfButton from '../components/OpenPdfButton'
import { CostBadge } from '../components/CostBadge'

const patterns = ['summarize', 'extract_wisdom', 'create_tags', 'extract_insights', 'extract_ideas']

function stepIcon(step) {
  if (/checking/i.test(step) || /existing/i.test(step) || /history/i.test(step)) return <Search className="w-4 h-4" />
  if (/download/i.test(step)) return <Download className="w-4 h-4" />
  if (/transcrib/i.test(step)) return <AudioWaveform className="w-4 h-4" />
  if (/analysis/i.test(step)) return <Sparkles className="w-4 h-4" />
  if (/complete/i.test(step)) return <CheckCircle2 className="w-4 h-4" />
  if (/fail/i.test(step)) return <TimerOff className="w-4 h-4" />
  return <CheckCircle2 className="w-4 h-4" />
}

function ProgressSteps({ steps, done }) {
  return (
    <div className="mt-6 max-w-3xl border border-gray-200 dark:border-gray-800 rounded-lg p-4">
      <p className="text-sm font-semibold mb-3 flex items-center gap-2">
        <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />
        Processing Rumble video
      </p>
      <ol className="flex flex-col gap-2">
        {steps.map((step, idx) => {
          const isCurrent = done ? false : idx === steps.length - 1
          const Icon = stepIcon(step)
          return (
            <li key={idx} className="flex items-center gap-2 text-sm">
              {isCurrent ? (
                <Loader2 className="w-4 h-4 animate-spin text-emerald-500 shrink-0" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              )}
              <span className={isCurrent ? 'font-medium' : 'text-gray-600 dark:text-gray-400'}>{step}</span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

export default function RumbleAnalysis() {
  const { selected: selectedModel } = useModel()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [steps, setSteps] = useState([])
  const pollRef = useRef(null)

  const [rumbleUrl, setRumbleUrl] = useState('')
  const [pattern, setPattern] = useState('summarize')

  const resetState = () => {
    setResult(null)
    setError('')
    setSteps([])
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null); setSteps([])
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
    try {
      const data = await api.analyzeRumble({ url: rumbleUrl, pattern, model: selectedModel })
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  const pollResult = (id) => {
    pollRef.current = setInterval(async () => {
      try {
        const r = await api.getResult(id)
        if (r.progress) {
          setSteps((prev) => {
            const last = prev[prev.length - 1]
            return last === r.progress ? prev : [...prev, r.progress]
          })
        }
        if (r.status === 'completed' || r.status === 'failed') {
          clearInterval(pollRef.current)
          pollRef.current = null
          setResult(r)
          setLoading(false)
        }
      } catch {
        clearInterval(pollRef.current)
        pollRef.current = null
        setLoading(false)
      }
    }, 1500)
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Rumble Analysis</h1>

      <form onSubmit={handleSubmit} className="max-w-xl space-y-3">
        <label className="block text-sm font-medium">Rumble Video URL</label>
        <input
          value={rumbleUrl}
          onChange={(e) => setRumbleUrl(e.target.value)}
          placeholder="https://rumble.com/vXXXXX-..."
          className="input"
          required
        />
        <label className="block text-sm font-medium">Pattern</label>
        <select value={pattern} onChange={(e) => setPattern(e.target.value)} className="input">
          {patterns.map((p) => <option key={p}>{p}</option>)}
        </select>
        <button type="submit" disabled={loading} className="btn">
          {loading ? 'Analyzing...' : 'Analyze Rumble'}
        </button>
      </form>

      {loading && !result && steps.length === 0 && (
        <p className="mt-6 flex items-center gap-2 text-sm text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" /> Starting analysis...
        </p>
      )}

      {loading && steps.length > 0 && <ProgressSteps steps={steps} done={false} />}

      {error && !loading && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {result && (
        <div className="mt-6 max-w-3xl">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Result</h2>
            <div className="flex items-center gap-2">
              <CostBadge result={result} />
              <OpenPdfButton text={result.output_data || result.error_message} />
              <SavePdfButton
                text={result.output_data || result.error_message}
                title={result.metadata_json ? JSON.parse(result.metadata_json).video_title : ''}
                filename={`rumble-${result.type}-${result.target?.slice(0, 40)}`}
              />
            </div>
          </div>
          <div className="border border-gray-200 dark:border-gray-800 rounded-lg p-4 max-h-96 overflow-y-auto">
            <FormattedOutput text={result.output_data || result.error_message} />
          </div>
        </div>
      )}
    </div>
  )
}