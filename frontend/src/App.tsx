import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import NavBar from './components/NavBar'
import Dashboard from './components/Dashboard'
import DataUpload from './components/DataUpload'
import ModelTraining from './components/ModelTraining'
import Chat from './components/Chat'
import Alerts from './components/Alerts'
import Login from './components/Login'
import Register from './components/Register'
import { getKpis } from './services/api'

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [kpis, setKpis] = useState({ dataset_count: 0, model_count: 0, active_alerts: 0 })

  useEffect(() => {
    if (token) {
      getKpis(token).then(setKpis).catch(() => setKpis({ dataset_count: 0, model_count: 0, active_alerts: 0 }))
    }
  }, [token])

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  const handleLogin = (newToken: string) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  if (!token) {
    return (
      <Router>
        <div className="min-h-screen bg-slate-950 text-slate-50">
          <div className="container mx-auto p-6">
            <Routes>
              <Route path="/login" element={<Login onAuthenticate={handleLogin} />} />
              <Route path="/register" element={<Register />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </div>
        </div>
      </Router>
    )
  }

  return (
    <Router>
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <NavBar onLogout={handleLogout} />
        <main className="container mx-auto p-6 space-y-6">
          <Routes>
            <Route path="/" element={<Dashboard token={token} kpis={kpis} />} />
            <Route path="/upload" element={<DataUpload token={token} />} />
            <Route path="/models" element={<ModelTraining token={token} />} />
            <Route path="/chat" element={<Chat token={token} />} />
            <Route path="/alerts" element={<Alerts token={token} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
