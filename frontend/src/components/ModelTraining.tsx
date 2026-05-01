import { useState, useEffect } from 'react'
import { Brain, Play, BarChart3, TrendingUp, Zap } from 'lucide-react'
import { trainMLModel, getModels, predictML, trainLSTM, predictLSTM, getLSTMs, getDatasets } from '../services/api'

interface Props {
  token: string
}

interface Dataset {
  id: number
  filename: string
  row_count: number
  column_count: number
}

interface Model {
  id: number
  name: string
  model_type: string
  accuracy: number
  rmse?: number
  created_at: string
}

export default function ModelTraining({ token }: Props) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [lstms, setLstms] = useState<Model[]>([])
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null)
  const [targetColumn, setTargetColumn] = useState('')
  const [modelType, setModelType] = useState<'regression' | 'classification'>('regression')
  const [algorithm, setAlgorithm] = useState<'randomforest' | 'linear' | 'logistic'>('randomforest')
  const [training, setTraining] = useState(false)
  const [predictionInput, setPredictionInput] = useState('')
  const [predictionResult, setPredictionResult] = useState<any>(null)
  const [lstmHistory, setLstmHistory] = useState('')
  const [lstmResult, setLstmResult] = useState<any>(null)
  const [trainingTasks, setTrainingTasks] = useState<{[key: string]: string}>({})

  useEffect(() => {
    loadData()
  }, [token])

  const loadData = async () => {
    try {
      const datasetsData = await getDatasets(token)
      setDatasets(datasetsData)

      const modelsData = await getModels(token)
      setModels(modelsData)

      const lstmsData = await getLSTMs(token)
      setLstms(lstmsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    }
  }

  const handleTrainML = async () => {
    if (!selectedDataset || !targetColumn) return

    setTraining(true)
    try {
      const result = await trainMLModel(token, {
        dataset_id: selectedDataset,
        target_column: targetColumn,
        model_type: modelType,
        algorithm: algorithm,
        model_name: `${modelType}_${algorithm}_${Date.now()}`
      })

      // Store task ID for tracking
      setTrainingTasks(prev => ({ ...prev, [result.task_id]: 'ML Training' }))

      alert(`ML training started! Task ID: ${result.task_id}`)
      await loadData() // Refresh models list
    } catch (error) {
      alert('Training failed: ' + error)
    } finally {
      setTraining(false)
    }
  }

  const handleTrainLSTM = async () => {
    if (!selectedDataset || !targetColumn) return

    setTraining(true)
    try {
      const result = await trainLSTM(token, {
        dataset_id: selectedDataset,
        target_column: targetColumn,
        lookback_steps: 12,
        forecast_steps: 7
      })

      // Store task ID for tracking
      setTrainingTasks(prev => ({ ...prev, [result.task_id]: 'LSTM Training' }))

      alert(`LSTM training started! Task ID: ${result.task_id}`)
      await loadData() // Refresh LSTMs list
    } catch (error) {
      alert('LSTM Training failed: ' + error)
    } finally {
      setTraining(false)
    }
  }

  const handlePredict = async (modelId: number) => {
    if (!predictionInput) return

    try {
      const inputData = JSON.parse(predictionInput)
      const result = await predictML(token, modelId, inputData)
      setPredictionResult(result)
    } catch (error) {
      alert('Prediction failed: ' + error)
    }
  }

  const handleLSTMPredict = async (modelId: number) => {
    if (!lstmHistory) return

    try {
      const history = JSON.parse(lstmHistory)
      const result = await predictLSTM(token, modelId, history, 7)
      setLstmResult(result)
    } catch (error) {
      alert('LSTM Prediction failed: ' + error)
    }
  }

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
        <h2 className="text-2xl font-semibold text-white mb-6 flex items-center space-x-2">
          <Brain className="h-6 w-6 text-emerald-400" />
          <span>Model Training & Prediction</span>
        </h2>

        {/* Dataset Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">Select Dataset</label>
          <select
            value={selectedDataset || ''}
            onChange={(e) => setSelectedDataset(Number(e.target.value))}
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
          >
            <option value="">Choose a dataset...</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.filename} ({dataset.row_count} rows, {dataset.column_count} cols)
              </option>
            ))}
          </select>
        </div>

        {/* Target Column */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">Target Column</label>
          <input
            type="text"
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            placeholder="e.g., sales, churn, price"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
          />
        </div>

        {/* ML Model Training */}
        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-blue-400" />
              <span>Machine Learning Models</span>
            </h3>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Model Type</label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value as 'regression' | 'classification')}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
              >
                <option value="regression">Regression</option>
                <option value="classification">Classification</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Algorithm</label>
              <select
                value={algorithm}
                onChange={(e) => setAlgorithm(e.target.value as 'randomforest' | 'linear' | 'logistic')}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
              >
                <option value="randomforest">Random Forest</option>
                <option value="linear">Linear Regression</option>
                <option value="logistic">Logistic Regression</option>
              </select>
            </div>

            <button
              onClick={handleTrainML}
              disabled={training || !selectedDataset || !targetColumn}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-500 text-slate-950 rounded-md hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="h-4 w-4" />
              <span>{training ? 'Training...' : 'Train ML Model'}</span>
            </button>
          </div>

          {/* LSTM Training */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-orange-400" />
              <span>LSTM Forecasting</span>
            </h3>

            <p className="text-sm text-slate-400">
              Train LSTM model for time-series forecasting with 12-step lookback and 7-step prediction.
            </p>

            <button
              onClick={handleTrainLSTM}
              disabled={training || !selectedDataset || !targetColumn}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-orange-500 text-slate-950 rounded-md hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="h-4 w-4" />
              <span>{training ? 'Training...' : 'Train LSTM Model'}</span>
            </button>
          </div>
        </div>

        {/* Models List */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* ML Models */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Trained ML Models</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {models.map((model) => (
                <div key={model.id} className="bg-slate-800 p-4 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-white">{model.name}</h4>
                    <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded">
                      {model.model_type}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">
                    Accuracy: {(model.accuracy * 100).toFixed(1)}%
                    {model.rmse && ` | RMSE: ${model.rmse.toFixed(2)}`}
                  </p>
                  <button
                    onClick={() => handlePredict(model.id)}
                    className="text-sm bg-emerald-500 text-slate-950 px-3 py-1 rounded hover:bg-emerald-400"
                  >
                    Test Prediction
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* LSTM Models */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Trained LSTM Models</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {lstms.map((model) => (
                <div key={model.id} className="bg-slate-800 p-4 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-white">{model.name}</h4>
                    <span className="text-xs bg-orange-500 text-white px-2 py-1 rounded">
                      LSTM
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">
                    Accuracy: {(model.accuracy * 100).toFixed(1)}%
                    {model.rmse && ` | RMSE: ${model.rmse.toFixed(2)}`}
                  </p>
                  <button
                    onClick={() => handleLSTMPredict(model.id)}
                    className="text-sm bg-orange-500 text-slate-950 px-3 py-1 rounded hover:bg-orange-400"
                  >
                    Test Forecast
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Prediction Input */}
        <div className="mt-8 space-y-4">
          <h3 className="text-lg font-semibold text-white">Test Predictions</h3>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                ML Prediction Input (JSON)
              </label>
              <textarea
                value={predictionInput}
                onChange={(e) => setPredictionInput(e.target.value)}
                placeholder='{"feature1": 100, "feature2": "value"}'
                className="w-full h-24 px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                LSTM History (JSON array)
              </label>
              <textarea
                value={lstmHistory}
                onChange={(e) => setLstmHistory(e.target.value)}
                placeholder='[100, 120, 110, 130, 125, 140, 135, 150, 145, 160, 155, 170]'
                className="w-full h-24 px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-400"
              />
            </div>
          </div>

          {/* Results */}
          {predictionResult && (
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-medium text-white mb-2">ML Prediction Result</h4>
              <pre className="text-sm text-emerald-400 bg-slate-900 p-2 rounded">
                {JSON.stringify(predictionResult, null, 2)}
              </pre>
            </div>
          )}

          {lstmResult && (
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-medium text-white mb-2">LSTM Forecast Result</h4>
              <pre className="text-sm text-orange-400 bg-slate-900 p-2 rounded">
                {JSON.stringify(lstmResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}