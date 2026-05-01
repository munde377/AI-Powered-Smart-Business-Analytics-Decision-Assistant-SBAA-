import { Link, useLocation } from 'react-router-dom'
import { BarChart3, Upload, Brain, MessageSquare, Bell, LogOut } from 'lucide-react'

interface Props {
  onLogout: () => void
}

export default function NavBar({ onLogout }: Props) {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/upload', label: 'Upload Data', icon: Upload },
    { path: '/models', label: 'Models', icon: Brain },
    { path: '/chat', label: 'Chat AI', icon: MessageSquare },
    { path: '/alerts', label: 'Alerts', icon: Bell },
  ]

  return (
    <header className="bg-slate-900 border-b border-slate-700">
      <div className="container mx-auto flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-8">
          <Link to="/" className="text-xl font-semibold text-emerald-400">
            Smart Analytics
          </Link>
          <nav className="hidden md:flex space-x-6">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition ${
                  location.pathname === path
                    ? 'bg-emerald-500 text-slate-950'
                    : 'text-slate-300 hover:text-emerald-400 hover:bg-slate-800'
                }`}
              >
                <Icon size={18} />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center space-x-2 rounded bg-slate-700 px-4 py-2 text-slate-300 transition hover:bg-slate-600"
        >
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  )
}
