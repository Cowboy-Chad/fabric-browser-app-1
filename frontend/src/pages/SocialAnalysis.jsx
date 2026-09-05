import { useState } from 'react'
import { api } from '../api/client'
import { useModel } from '../api/modelContext'
import FormattedOutput from '../components/FormattedOutput'
import SavePdfButton from '../components/SavePdfButton'
import OpenPdfButton from '../components/OpenPdfButton'
import { CostBadge } from '../components/CostBadge'

const platforms = [
  { id: 'twitter', label: 'Twitter/X' },
  { id: 'reddit', label: 'Reddit' },
  { id: 'tiktok', label: 'TikTok' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'linkedin', label: 'LinkedIn' },
]

const patternMap = {
  twitter: 'summarize',
  reddit: 'analyze_comments',
  tiktok: 'summarize',
  instagram: 'analyze_personality',
  linkedin: 'analyze_personality',
}

export default function SocialAnalysis() {
  const { selected: selectedModel } = useModel()
  const [platform, setPlatform] = useState('twitter')
  const [target, setTarget] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const pattern = patternMap[platform] || 'summarize'
      const data = await api.analyzeSocial(platform, target, pattern, selectedModel)
      const interval = setInterval(async () => {
        try {
          const r = await api.getResult(data.result_id)
          if (r.status === 'completed' || r.status === 'failed') {
            clearInterval(interval)
            setResult(r)
            setLoading(false)
          }
        } catch { clearInterval(interval); setLoading(false) }
      }, 2000)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Social Media Analysis</h1>

      <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit">
        {platforms.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setPlatform(id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              platform === id ? 'bg-white dark:bg-gray-700 shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="max-w-xl space-y-3">
        <label className="block text-sm font-medium">
          {platform === 'twitter' ? 'Username or Tweet URL' :
           platform === 'reddit' ? 'Post URL or Subreddit' :
           platform === 'tiktok' ? 'Profile URL or Video URL' :
           platform === 'instagram' ? 'Profile URL' :
           'Profile URL'}
        </label>
        <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="Enter URL or handle..." className="input" required />
        <button type="submit" disabled={loading} className="btn">{loading ? 'Analyzing...' : 'Analyze'}</button>
      </form>

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {result && (
        <div className="mt-6 max-w-3xl">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Result</h2>
            <div className="flex items-center gap-2">
              <CostBadge result={result} />
              <OpenPdfButton text={result.output_data || result.error_message} />
              <SavePdfButton text={result.output_data || result.error_message} title={result.metadata_json ? JSON.parse(result.metadata_json).video_title : ''} filename={`social-${result.target?.slice(0, 40)}`} />
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