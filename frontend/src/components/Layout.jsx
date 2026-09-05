import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Clapperboard, Users, Globe, History, Binary
} from 'lucide-react'
import { useModel } from '../api/modelContext'
import ModelSelector from './ModelSelector'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/media', label: 'Media', icon: Clapperboard },
  { to: '/social', label: 'Social', icon: Users },
  { to: '/web', label: 'Web & Domain', icon: Globe },
  { to: '/history', label: 'History', icon: History },
]

export default function Layout() {
  const { models, selected, changeModel } = useModel()

  return (
    <div className="flex h-screen">
      <aside className="w-56 border-r border-gray-200 dark:border-gray-800 p-4 flex flex-col">
        <div className="flex items-center gap-2 mb-8">
          <Binary className="w-6 h-6 text-emerald-500" />
          <span className="font-bold text-lg">OSINT App 1</span>
        </div>
        <nav className="flex flex-col gap-1 flex-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-2">
          <ModelSelector models={models} selected={selected} onChange={changeModel} />
        </div>
        <div className="mt-1 text-xs text-gray-400 text-center">
          Powered by Fabric
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}