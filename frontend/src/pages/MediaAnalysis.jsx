import { useState } from 'react'
import { api } from '../api/client'
import { useModel } from '../api/modelContext'
import { Clapperboard, Music, Upload } from 'lucide-react'
import FormattedOutput from '../components/FormattedOutput'
import SavePdfButton from '../components/SavePdfButton'
import OpenPdfButton from '../components/OpenPdfButton'
import { CostBadge } from '../components/CostBadge'

const patterns = ['youtube_summary', 'summarize', 'extract_wisdom', 'analyze_comments', 'create_tags', 'extract_insights']

export default function MediaAnalysis() {
  const { selected: selectedModel } = useModel()
  const [activeTab, setActiveTab] = useState('youtube')
  const [loading, setLoading] = useState(false)
  const [resultId, setResultId] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [includeComments, setIncludeComments] = useState(false)
  const [youtubePattern, setYoutubePattern] = useState('youtube_summary')

  const [spotifyUrl, setSpotifyUrl] = useState('')
  const [spotifyPattern, setSpotifyPattern] = useState('summarize')

  const [file, setFile] = useState(null)
  const [filePattern, setFilePattern] = useState('summarize')

  const handleYouTube = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null); setResultId(null)
    try {
      const data = await api.analyzeYouTube({ url: youtubeUrl, include_comments: includeComments, pattern: youtubePattern, model: selectedModel })
      setResultId(data.result_id)
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  const handleSpotify = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null); setResultId(null)
    try {
      const data = await api.analyzeSpotify({ url: spotifyUrl, pattern: spotifyPattern, model: selectedModel })
      setResultId(data.result_id)
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  const handleFileUpload = async (e) => {
    e.preventDefault()
    if (!file) return
    setLoading(true); setError(''); setResult(null); setResultId(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('model', selectedModel)
      const data = await api.transcribeFile(fd)
      setResultId(data.result_id)
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  const pollResult = async (id) => {
    const interval = setInterval(async () => {
      try {
        const r = await api.getResult(id)
        if (r.status === 'completed' || r.status === 'failed') {
          clearInterval(interval)
          setResult(r)
          setLoading(false)
        }
      } catch { clearInterval(interval); setLoading(false) }
    }, 2000)
  }

  const tabs = [
    { key: 'youtube', label: 'YouTube', icon: Clapperboard },
    { key: 'spotify', label: 'Spotify', icon: Music },
    { key: 'file', label: 'File Upload', icon: Upload },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Media Analysis</h1>

      <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === key ? 'bg-white dark:bg-gray-700 shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {activeTab === 'youtube' && (
        <form onSubmit={handleYouTube} className="max-w-xl space-y-3">
          <label className="block text-sm font-medium">YouTube URL</label>
          <input value={youtubeUrl} onChange={(e) => setYoutubeUrl(e.target.value)} placeholder="https://youtube.com/watch?v=..." className="input" required />
          <label className="block text-sm font-medium">Pattern</label>
          <select value={youtubePattern} onChange={(e) => setYoutubePattern(e.target.value)} className="input">
            {patterns.map((p) => <option key={p}>{p}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={includeComments} onChange={(e) => setIncludeComments(e.target.checked)} />
            Include comments
          </label>
          <button type="submit" disabled={loading} className="btn">{loading ? 'Analyzing...' : 'Analyze YouTube'}</button>
        </form>
      )}

      {activeTab === 'spotify' && (
        <form onSubmit={handleSpotify} className="max-w-xl space-y-3">
          <label className="block text-sm font-medium">Spotify URL</label>
          <input value={spotifyUrl} onChange={(e) => setSpotifyUrl(e.target.value)} placeholder="https://open.spotify.com/episode/..." className="input" required />
          <label className="block text-sm font-medium">Pattern</label>
          <select value={spotifyPattern} onChange={(e) => setSpotifyPattern(e.target.value)} className="input">
            {patterns.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button type="submit" disabled={loading} className="btn">{loading ? 'Analyzing...' : 'Analyze Spotify'}</button>
        </form>
      )}

      {activeTab === 'file' && (
        <form onSubmit={handleFileUpload} className="max-w-xl space-y-3">
          <label className="block text-sm font-medium">Audio/Video File</label>
          <input type="file" accept="audio/*,video/*" onChange={(e) => setFile(e.target.files[0])} className="input" required />
          <label className="block text-sm font-medium">Pattern</label>
          <select value={filePattern} onChange={(e) => setFilePattern(e.target.value)} className="input">
            {patterns.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button type="submit" disabled={loading || !file} className="btn">{loading ? 'Transcribing...' : 'Transcribe & Analyze'}</button>
        </form>
      )}

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {result && (
        <div className="mt-6 max-w-3xl">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Result</h2>
            <div className="flex items-center gap-2">
              <CostBadge result={result} />
              <OpenPdfButton text={result.output_data || result.error_message} />
              <SavePdfButton text={result.output_data || result.error_message} title={result.metadata_json ? JSON.parse(result.metadata_json).video_title : ''} filename={`media-${result.type}-${result.target?.slice(0, 40)}`} />
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