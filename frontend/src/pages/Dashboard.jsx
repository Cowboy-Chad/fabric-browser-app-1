import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import ResultCard from '../components/ResultCard'
import { Clapperboard, Users, Globe, ArrowRight } from 'lucide-react'

const quickActions = [
  { label: 'Analyze YouTube', path: '/media', icon: Clapperboard, color: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' },
  { label: 'Scrape Website', path: '/web', icon: Globe, color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' },
  { label: 'Social Profile', path: '/social', icon: Users, color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400' },
]

export default function Dashboard() {
  const [results, setResults] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    api.getResults(5).then(setResults).catch(() => {})
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {quickActions.map(({ label, path, icon: Icon, color }) => (
          <button
            key={path}
            onClick={() => navigate(path)}
            className={`flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-800 hover:shadow-md transition-shadow ${color}`}
          >
            <div className="flex items-center gap-3">
              <Icon className="w-6 h-6" />
              <span className="font-medium">{label}</span>
            </div>
            <ArrowRight className="w-4 h-4" />
          </button>
        ))}
      </div>

      <h2 className="text-lg font-semibold mb-3">Recent Analyses</h2>
      {results.length === 0 ? (
        <p className="text-gray-400 text-sm">No analyses yet. Start one from the sidebar or quick actions above.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {results.map((r) => (
            <ResultCard key={r.id} result={r} onView={(id) => navigate(`/history?selected=${id}`)} />
          ))}
        </div>
      )}
    </div>
  )
}