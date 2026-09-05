import { CostBadge } from './CostBadge'

export default function ResultCard({ result, onView, selectedId }) {
  const statusColors = {
    completed: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
    running: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  }

  let typeLabel = result.type
  if (result.type === 'youtube_transcript' && result.metadata_json) {
    try {
      const meta = JSON.parse(result.metadata_json)
      if (meta.video_title) typeLabel = meta.video_title
    } catch {}
  }

  return (
    <div
      className={`border rounded-lg p-4 transition-colors cursor-pointer ${result.id === selectedId ? 'border-blue-500 dark:border-blue-400' : 'border-gray-200 dark:border-gray-800 hover:border-emerald-300 dark:hover:border-emerald-700'}`}
      onClick={() => onView?.(result.id)}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono text-gray-400 truncate max-w-[70%]" title={typeLabel}>{typeLabel}</span>
        <div className="flex items-center gap-1.5 shrink-0">
          <CostBadge result={result} />
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusColors[result.status] || ''}`}>
            {result.status}
          </span>
        </div>
      </div>
      <p className="text-sm font-medium truncate">{result.target}</p>
      {result.pattern && (
        <p className="text-xs text-gray-400 mt-1">Pattern: {result.pattern}</p>
      )}
      {result.created_at && (
        <p className="text-xs text-gray-400 mt-1">
          {new Date(result.created_at).toLocaleString()}
        </p>
      )}
    </div>
  )
}