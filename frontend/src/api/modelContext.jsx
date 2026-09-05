import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

const ModelContext = createContext()

const STORAGE_KEY = 'osint-selected-model'
const DEFAULT_MODEL = 'deepseek/deepseek-v4-flash'

export function ModelProvider({ children }) {
  const [models, setModels] = useState([])
  const [selected, setSelected] = useState(() => localStorage.getItem(STORAGE_KEY) || DEFAULT_MODEL)

  useEffect(() => {
    api.getModels().then((data) => {
      setModels(data.models || [])
      const saved = localStorage.getItem(STORAGE_KEY)
      if (!saved) {
        setSelected(data.default || DEFAULT_MODEL)
      }
    }).catch(() => {})
  }, [])

  const changeModel = useCallback((model) => {
    setSelected(model)
    localStorage.setItem(STORAGE_KEY, model)
  }, [])

  return (
    <ModelContext.Provider value={{ models, selected, changeModel }}>
      {children}
    </ModelContext.Provider>
  )
}

export function useModel() {
  return useContext(ModelContext)
}