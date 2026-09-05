import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ModelProvider } from './api/modelContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import MediaAnalysis from './pages/MediaAnalysis'
import SocialAnalysis from './pages/SocialAnalysis'
import WebAnalysis from './pages/WebAnalysis'
import History from './pages/History'

function App() {
  const [dark, setDark] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e) => setDark(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  return (
    <ModelProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/media" element={<MediaAnalysis />} />
          <Route path="/social" element={<SocialAnalysis />} />
          <Route path="/web" element={<WebAnalysis />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ModelProvider>
  )
}

export default App