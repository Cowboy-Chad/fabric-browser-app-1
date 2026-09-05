import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import ResultCard from '../components/ResultCard'
import FormattedOutput from '../components/FormattedOutput'
import SavePdfButton from '../components/SavePdfButton'
import OpenPdfButton from '../components/OpenPdfButton'
import { CostBadge, parseMeta, formatCost } from '../components/CostBadge'
import { X, RefreshCw } from 'lucide-react'

export default function History() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadResults = () => {
    setLoading(true)
    api.getResults(50).then((data) => {
      setResults(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => {
    loadResults()
  }, [])

  useEffect(() => {
    const onFocus = () => loadResults()
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [])

  useEffect(() => {
    const onVisible = () => { if (document.visibilityState === 'visible') loadResults() }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [])

  useEffect(() => {
    const id = searchParams.get('selected')
    if (id) {
      api.getResult(id).then(setSelected).catch(() => {})
    }
  }, [searchParams])

  const viewResult = (id) => {
    api.getResult(id).then(setSelected)
    setSearchParams({ selected: id })
  }

  const closeDetail = () => {
    setSelected(null)
    setSearchParams({})
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Analysis History</h1>
        <button onClick={loadResults} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {loading ? (
            <p className="text-gray-400">Loading...</p>
          ) : results.length === 0 ? (
            <p className="text-gray-400">No results yet.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {results.map((r) => (
                <ResultCard key={r.id} result={r} onView={viewResult} selectedId={selected?.id} />
              ))}
            </div>
          )}
        </div>

        {selected && (
          <div className="border border-gray-200 dark:border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold">Result Detail</h2>
              <div className="flex items-center gap-2">
                <OpenPdfButton text={selected.output_data || selected.error_message} />
                <SavePdfButton text={selected.output_data || selected.error_message} title={selected.metadata_json ? JSON.parse(selected.metadata_json).video_title : ''} filename={`${selected.type}-${selected.target?.slice(0, 40)}`} />
                <button onClick={closeDetail} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
              </div>
            </div>
            <div className="space-y-2 text-sm mb-3">
              <div className="flex items-center gap-2">
                <span className="font-medium">Status:</span> {selected.status}
                <CostBadge result={selected} />
              </div>
              <p><span className="font-medium">Type:</span> {selected.type}</p>
              <p><span className="font-medium">Target:</span> {selected.target}</p>
              {selected.pattern && <p><span className="font-medium">Pattern:</span> {selected.pattern}</p>}
              {(() => { const m = parseMeta(selected); if (m.cost_estimate === undefined) return null; return (
                <>
                  {m.input_tokens != null && <p><span className="font-medium">Tokens:</span> {m.input_tokens} in / {m.output_tokens} out</p>}
                  {m.cost_estimate > 0 && <p><span className="font-medium">Cost:</span> {formatCost(m.cost_estimate)}</p>}
                </>
              )})()}
              {selected.raw_fabric_command && (
                <p><span className="font-medium">Command:</span> <code className="text-xs break-all">{selected.raw_fabric_command}</code></p>
              )}
              {selected.created_at && (
                <p><span className="font-medium">Created:</span> {new Date(selected.created_at).toLocaleString(undefined, { timeZoneName: 'short' })}</p>
              )}
            </div>
            <div className="border-t border-gray-200 dark:border-gray-800 pt-3">
<p className="text-xs font-medium mb-1">Output:</p>
            <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded max-h-96 overflow-y-auto">
              <FormattedOutput text={selected.output_data || selected.error_message || '(empty)'} />
            </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}