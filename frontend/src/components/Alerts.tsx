import { useState, useEffect } from 'react'
import { AlertTriangle, Bell, CheckCircle, Clock, TrendingDown, TrendingUp } from 'lucide-react'
import { getAlerts, acknowledgeAlert, resolveAlert } from '../services/api'

interface Props {
  token: string
}

interface AlertItem {
  id: number
  alert_type: string
  severity: string
  title: string
  message: string
  status: string
  created_at: string
  metric_value?: number
  threshold_value?: number
}

export default function Alerts({ token }: Props) {
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAlerts()
  }, [token])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const alertsData = await getAlerts(token)
      setAlerts(alertsData)
    } catch (error) {
      console.error('Failed to load alerts:', error)
      setAlerts([]) // Set empty array on error
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-400 bg-red-500/20 border-red-500/30'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30'
      case 'low': return 'text-blue-400 bg-blue-500/20 border-blue-500/30'
      default: return 'text-slate-400 bg-slate-500/20 border-slate-500/30'
    }
  }

  const getSeverityIcon = (type: string) => {
    switch (type) {
      case 'sales_drop': return <TrendingDown className="h-5 w-5" />
      case 'high_demand': return <TrendingUp className="h-5 w-5" />
      case 'anomaly_detected': return <AlertTriangle className="h-5 w-5" />
      case 'forecast_accuracy': return <Bell className="h-5 w-5" />
      default: return <Bell className="h-5 w-5" />
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  const activeAlerts = alerts.filter((alertItem) => alertItem.status === 'active')
  const resolvedAlerts = alerts.filter((alertItem) => alertItem.status === 'resolved')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400"></div>
      </div>
    )
  }

  return (
    <section className="space-y-6">
      {/* Alert Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Active Alerts</p>
          </div>
          <h2 className="mt-4 text-3xl font-semibold text-white">{activeAlerts.length}</h2>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Resolved</p>
          </div>
          <h2 className="mt-4 text-3xl font-semibold text-white">{resolvedAlerts.length}</h2>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-blue-400" />
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Last 24h</p>
          </div>
          <h2 className="mt-4 text-3xl font-semibold text-white">
            {alerts.filter(a => new Date(a.created_at) > new Date(Date.now() - 86400000)).length}
          </h2>
        </div>
      </div>

      {/* Active Alerts */}
      <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
        <h2 className="text-2xl font-semibold text-white mb-6 flex items-center space-x-2">
          <AlertTriangle className="h-6 w-6 text-red-400" />
          <span>Active Alerts</span>
        </h2>

        {activeAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-400 mx-auto mb-4" />
            <p className="text-slate-400">No active alerts. All systems normal!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {activeAlerts.map((alert) => (
              <div key={alert.id} className="border border-slate-700 rounded-lg p-4 bg-slate-800/50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-lg border ${getSeverityColor(alert.severity)}`}>
                      {getSeverityIcon(alert.alert_type)}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-white mb-1">{alert.title}</h3>
                      <p className="text-slate-300 mb-2">{alert.message}</p>
                      <div className="flex items-center space-x-4 text-sm text-slate-400">
                        <span className="capitalize">{alert.alert_type.replace('_', ' ')}</span>
                        <span>•</span>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span>•</span>
                        <span>{formatTimeAgo(alert.created_at)}</span>
                      </div>
                      {alert.metric_value && alert.threshold_value && (
                        <div className="mt-2 text-sm">
                          <span className="text-slate-400">Value: </span>
                          <span className="text-white">${alert.metric_value.toLocaleString()}</span>
                          <span className="text-slate-400 mx-2">•</span>
                          <span className="text-slate-400">Threshold: </span>
                          <span className="text-red-400">${alert.threshold_value.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={async () => {
                        try {
                          await acknowledgeAlert(token, alert.id)
                          await loadAlerts()
                        } catch (error) {
                          window.alert('Failed to acknowledge alert')
                        }
                      }}
                      className="px-3 py-1 bg-emerald-500 text-slate-950 rounded text-sm hover:bg-emerald-400"
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          await resolveAlert(token, alert.id)
                          await loadAlerts()
                        } catch (error) {
                          window.alert('Failed to resolve alert')
                        }
                      }}
                      className="px-3 py-1 bg-slate-400 text-slate-950 rounded text-sm hover:bg-slate-300"
                    >
                      Resolve
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Alert History */}
      <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
        <h2 className="text-2xl font-semibold text-white mb-6 flex items-center space-x-2">
          <Clock className="h-6 w-6 text-slate-400" />
          <span>Alert History</span>
        </h2>

        <div className="space-y-3">
          {resolvedAlerts.map((alert) => (
            <div key={alert.id} className="border border-slate-700 rounded-lg p-4 bg-slate-800/30">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="p-2 rounded-lg border border-green-500/30 bg-green-500/20">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                  </div>
                  <div className="flex-1">
                      <h3 className="font-medium text-slate-300 mb-1">{alert.title}</h3>
                      <p className="text-slate-400 mb-2">{alert.message}</p>
                      <div className="flex items-center space-x-4 text-sm text-slate-500">
                        <span className="capitalize">{alert.alert_type.replace('_', ' ')}</span>
                      <span>•</span>
                      <span className="text-green-400">Resolved</span>
                      <span>•</span>
                      <span>{formatTimeAgo(alert.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Alert Rules Configuration */}
      <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
        <h2 className="text-2xl font-semibold text-white mb-6">Alert Rules</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="font-medium text-white mb-2">Sales Drop Alert</h3>
            <p className="text-sm text-slate-400 mb-3">Trigger when daily sales drop below threshold</p>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Threshold: $50,000</span>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                <span className="text-sm text-green-400">Active</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="font-medium text-white mb-2">Forecast Accuracy Alert</h3>
            <p className="text-sm text-slate-400 mb-3">Trigger when model accuracy drops below threshold</p>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Threshold: 80%</span>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                <span className="text-sm text-green-400">Active</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="font-medium text-white mb-2">Anomaly Detection</h3>
            <p className="text-sm text-slate-400 mb-3">Detect unusual patterns in data</p>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Sensitivity: Medium</span>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                <span className="text-sm text-yellow-400">Active</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="font-medium text-white mb-2">High Demand Alert</h3>
            <p className="text-sm text-slate-400 mb-3">Trigger when product demand spikes</p>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Threshold: +25%</span>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                <span className="text-sm text-green-400">Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}