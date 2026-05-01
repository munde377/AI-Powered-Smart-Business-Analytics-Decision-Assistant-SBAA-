import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts'
import { TrendingUp, Database, Brain, AlertTriangle, Activity } from 'lucide-react'
import { getModels, getLSTMs, getDatasets, getCorrelation } from '../services/api'

interface Props {
  token: string
  kpis: {
    dataset_count: number
    model_count: number
    active_alerts: number
  }
}

interface ChartData {
  name: string
  value: number
  date?: string
}

export default function Dashboard({ token, kpis }: Props) {
  const [analyticsData, setAnalyticsData] = useState<any>(null)
  const [models, setModels] = useState<any[]>([])
  const [forecastData, setForecastData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [token])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      const [mlModels, lstmModels, datasets] = await Promise.all([
        getModels(token),
        getLSTMs(token),
        getDatasets(token)
      ])

      const allModels = [
        ...mlModels.map((m: any) => ({ ...m, type: 'regression' })),
        ...lstmModels.map((m: any) => ({ ...m, type: 'lstm' }))
      ]

      setModels(allModels)

      const totalRows = datasets.reduce((sum: number, d: any) => sum + (d.row_count || 0), 0)
      const totalColumns = datasets.reduce((sum: number, d: any) => sum + (d.column_count || 0), 0)
      const averageRows = datasets.length ? Math.round(totalRows / datasets.length) : 0

      let correlations: any[] = []
      if (datasets.length > 0) {
        const correlationResponse = await getCorrelation(token, +datasets[0].id)
        const matrix = correlationResponse.correlation || {}
        const pairs: any[] = []

        Object.entries(matrix).forEach(([col, row]: any) => {
          Object.entries(row).forEach(([other, value]: any) => {
            if (col !== other) {
              pairs.push({ feature: `${col} vs ${other}`, correlation: Number(value) })
            }
          })
        })

        correlations = pairs
          .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
          .slice(0, 3)
          .map((item) => ({ feature: item.feature, correlation: item.correlation }))
      }

      setAnalyticsData({
        summary: {
          total_rows: totalRows,
          total_columns: totalColumns,
          average_rows_per_dataset: averageRows
        },
        correlations
      })

      setForecastData(
        allModels
          .slice(-7)
          .map((model: any, index: number) => ({
            name: model.name || `Model ${index + 1}`,
            value: Math.round((model.accuracy ?? 0) * 100)
          }))
      )
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      setAnalyticsData({
        summary: {
          total_rows: 0,
          total_columns: 0,
          average_rows_per_dataset: 0
        },
        correlations: []
      })
      setModels([])
      setForecastData([])
    } finally {
      setLoading(false)
    }
  }

  const pieData = [
    { name: 'Regression', value: models.filter(m => m.type === 'regression').length, color: '#10b981' },
    { name: 'Classification', value: models.filter(m => m.type === 'classification').length, color: '#3b82f6' },
    { name: 'LSTM', value: models.filter(m => m.type === 'lstm').length, color: '#f59e0b' }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400"></div>
      </div>
    )
  }

  return (
    <section className="space-y-6">
      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center space-x-2">
            <Database className="h-5 w-5 text-emerald-400" />
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Datasets</p>
          </div>
          <h2 className="mt-4 text-3xl font-semibold text-white">{kpis.dataset_count}</h2>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-blue-400" />
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Models</p>
          </div>
          <h2 className="mt-4 text-3xl font-semibold text-white">{kpis.model_count}</h2>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Active Alerts</p>
          </div>
          <h2 className="mt-4 text-3xl font-semibold text-white">{kpis.active_alerts}</h2>
        </div>
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-purple-400" />
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Average Rows</p>
          </div>
          <h2 className="mt-4 text-3xl font-semibold text-white">{analyticsData?.summary?.average_rows_per_dataset || 0}</h2>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Model Accuracy Trend */}
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-emerald-400" />
            <span>Latest Model Accuracy</span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Model Performance Chart */}
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <h3 className="text-xl font-semibold text-white mb-4">Model Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={models}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="accuracy" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Model Types Distribution */}
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <h3 className="text-xl font-semibold text-white mb-4">Model Types</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Feature Correlations */}
        <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
          <h3 className="text-xl font-semibold text-white mb-4">Top Correlations</h3>
          <div className="space-y-4">
            {analyticsData?.correlations?.map((corr: any, index: number) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-slate-300">{corr.feature}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-emerald-400 h-2 rounded-full"
                      style={{ width: `${corr.correlation * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-slate-400 w-12">
                    {(corr.correlation * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Models Table */}
      <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
        <h3 className="text-xl font-semibold text-white mb-4">Recent Models</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="pb-3 text-slate-400">Model Name</th>
                <th className="pb-3 text-slate-400">Type</th>
                <th className="pb-3 text-slate-400">Accuracy</th>
                <th className="pb-3 text-slate-400">RMSE</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model, index) => (
                <tr key={index} className="border-b border-slate-800">
                  <td className="py-3 text-white">{model.name}</td>
                  <td className="py-3 text-slate-300 capitalize">{model.type}</td>
                  <td className="py-3 text-emerald-400">{(model.accuracy * 100).toFixed(1)}%</td>
                  <td className="py-3 text-slate-300">{model.rmse?.toFixed(2) || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
