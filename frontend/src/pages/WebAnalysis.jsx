import { useState } from 'react'
import { api } from '../api/client'
import { useModel } from '../api/modelContext'
import { Globe, Monitor, Mail, FileText } from 'lucide-react'
import FormattedOutput from '../components/FormattedOutput'
import SavePdfButton from '../components/SavePdfButton'
import OpenPdfButton from '../components/OpenPdfButton'
import { CostBadge } from '../components/CostBadge'

const tabs = [
  { key: 'scrape', label: 'Website Scrape', icon: Globe },
  { key: 'domain', label: 'Domain Analysis', icon: Monitor },
  { key: 'email', label: 'Email Headers', icon: Mail },
  { key: 'logs', label: 'Log Analysis', icon: FileText },
]

const patterns = ['summarize', 'extract_domains', 'analyze_threat_report', 'extract_insights', 'create_summary', 'analyze_logs']

export default function WebAnalysis() {
  const { selected: selectedModel } = useModel()
  const [activeTab, setActiveTab] = useState('scrape')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const [scrapeUrl, setScrapeUrl] = useState('')
  const [scrapePattern, setScrapePattern] = useState('summarize')

  const [domain, setDomain] = useState('')
  const [domainPattern, setDomainPattern] = useState('extract_domains')

  const [emailHeaders, setEmailHeaders] = useState('')
  const [emailPattern, setEmailPattern] = useState('analyze_email_headers')

  const [logs, setLogs] = useState('')
  const [logPattern, setLogPattern] = useState('analyze_logs')

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

  const handleScrape = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await api.scrapeWeb({ url: scrapeUrl, pattern: scrapePattern, model: selectedModel })
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  const handleDomain = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await api.analyzeDomain({ domain, pattern: domainPattern, model: selectedModel })
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  const handleEmail = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await api.analyzeEmailHeaders({ headers: emailHeaders, pattern: emailPattern, model: selectedModel })
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  const handleLogs = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await api.analyzeLogs({ logs, pattern: logPattern, model: selectedModel })
      pollResult(data.result_id)
    } catch (err) { setError(err.message); setLoading(false) }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Web & Domain Analysis</h1>

      <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit flex-wrap">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === key ? 'bg-white dark:bg-gray-700 shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
            }`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {activeTab === 'scrape' && (
        <form onSubmit={handleScrape} className="max-w-xl space-y-3">
          <label className="block text-sm font-medium">Website URL</label>
          <input value={scrapeUrl} onChange={(e) => setScrapeUrl(e.target.value)} placeholder="https://example.com" className="input" required />
          <label className="block text-sm font-medium">Pattern</label>
          <select value={scrapePattern} onChange={(e) => setScrapePattern(e.target.value)} className="input">
            {patterns.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button type="submit" disabled={loading} className="btn">{loading ? 'Scraping...' : 'Scrape & Analyze'}</button>
        </form>
      )}

      {activeTab === 'domain' && (
        <form onSubmit={handleDomain} className="max-w-xl space-y-3">
          <label className="block text-sm font-medium">Domain Name</label>
          <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="example.com" className="input" required />
          <label className="block text-sm font-medium">Pattern</label>
          <select value={domainPattern} onChange={(e) => setDomainPattern(e.target.value)} className="input">
            {patterns.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button type="submit" disabled={loading} className="btn">{loading ? 'Analyzing...' : 'Analyze Domain'}</button>
        </form>
      )}

      {activeTab === 'email' && (
        <form onSubmit={handleEmail} className="max-w-xl space-y-3">
          <label className="block text-sm font-medium">Raw Email Headers</label>
          <textarea value={emailHeaders} onChange={(e) => setEmailHeaders(e.target.value)} rows={8} className="input font-mono text-xs" placeholder="Paste raw email headers here..." required />
          <label className="block text-sm font-medium">Pattern</label>
          <select value={emailPattern} onChange={(e) => setEmailPattern(e.target.value)} className="input">
            {patterns.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button type="submit" disabled={loading} className="btn">{loading ? 'Analyzing...' : 'Analyze Headers'}</button>
        </form>
      )}

      {activeTab === 'logs' && (
        <form onSubmit={handleLogs} className="max-w-xl space-y-3">
          <label className="block text-sm font-medium">Log Data</label>
          <textarea value={logs} onChange={(e) => setLogs(e.target.value)} rows={8} className="input font-mono text-xs" placeholder="Paste server logs, firewall logs, or any log data..." required />
          <label className="block text-sm font-medium">Pattern</label>
          <select value={logPattern} onChange={(e) => setLogPattern(e.target.value)} className="input">
            {patterns.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button type="submit" disabled={loading} className="btn">{loading ? 'Analyzing...' : 'Analyze Logs'}</button>
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
              <SavePdfButton text={result.output_data || result.error_message} title={result.metadata_json ? JSON.parse(result.metadata_json).video_title : ''} filename={`web-${result.type}-${result.target?.slice(0, 40)}`} />
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