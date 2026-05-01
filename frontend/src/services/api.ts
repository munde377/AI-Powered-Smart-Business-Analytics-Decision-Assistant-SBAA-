import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Auth APIs
export const login = async (email: string, password: string) => {
  const response = await axios.post(`${BASE_URL}/auth/login`, new URLSearchParams({ username: email, password }))
  return response.data
}

export const register = async (email: string, password: string) => {
  const response = await axios.post(`${BASE_URL}/auth/register`, { email, password })
  return response.data
}

// Dashboard APIs
export const getKpis = async (token: string) => {
  const response = await axios.get(`${BASE_URL}/dashboard/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

// Data APIs
export const uploadDataset = async (file: File, token: string) => {
  const form = new FormData()
  form.append('file', file)
  const response = await axios.post(`${BASE_URL}/data/upload`, form, {
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const getDatasets = async (token: string) => {
  const response = await axios.get(`${BASE_URL}/data/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data.items
}

export const getDataset = async (id: number, token: string) => {
  const response = await axios.get(`${BASE_URL}/data/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const getDatasetPreview = async (id: number, token: string) => {
  const response = await axios.get(`${BASE_URL}/data/${id}/preview`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

// Analytics APIs
export const getSummary = async (token: string, datasetId: number) => {
  const response = await axios.get(`${BASE_URL}/analytics/summary/${datasetId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const getCorrelation = async (token: string, datasetId: number) => {
  const response = await axios.get(`${BASE_URL}/analytics/correlation/${datasetId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const getDistribution = async (token: string, datasetId: number) => {
  const response = await axios.get(`${BASE_URL}/analytics/distribution/${datasetId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

// ML APIs
export const trainMLModel = async (token: string, data: {
  dataset_id: number
  target_column: string
  model_type: string
  algorithm: string
  model_name: string
  feature_columns?: string[]
}) => {
  const response = await axios.post(`${BASE_URL}/ml/train`, data, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const predictML = async (token: string, modelId: number, record: any) => {
  const response = await axios.post(`${BASE_URL}/ml/predict`, {
    model_id: modelId,
    record
  }, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const getModels = async (token: string) => {
  const response = await axios.get(`${BASE_URL}/ml/models`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const getModelStatus = async (token: string, modelId: number) => {
  const response = await axios.get(`${BASE_URL}/ml/model-status/${modelId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

// DL APIs
export const trainLSTM = async (token: string, data: {
  dataset_id: number
  target_column: string
  lookback_steps: number
  forecast_steps: number
}) => {
  const response = await axios.post(`${BASE_URL}/dl/train-lstm`, data, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const predictLSTM = async (token: string, modelId: number, history: number[], forecastSteps: number) => {
  const response = await axios.post(`${BASE_URL}/dl/predict-lstm`, {
    model_id: modelId,
    history,
    forecast_steps: forecastSteps
  }, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const getLSTMs = async (token: string) => {
  const response = await axios.get(`${BASE_URL}/dl/lstm-models`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

// GenAI APIs
export const chatWithData = async (token: string, query: string, datasetId: number) => {
  const response = await axios.post(`${BASE_URL}/genai/chat`, {
    query,
    dataset_id: datasetId
  }, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const translateToSQL = async (token: string, query: string, datasetId: number) => {
  const response = await axios.post(`${BASE_URL}/genai/translate-sql`, {
    query,
    dataset_id: datasetId
  }, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const getChatHistory = async (token: string) => {
  const response = await axios.get(`${BASE_URL}/genai/chat-history`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

// Alerts APIs
export const getAlerts = async (token: string) => {
  const response = await axios.get(`${BASE_URL}/alerts/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const acknowledgeAlert = async (token: string, alertId: number) => {
  const response = await axios.post(`${BASE_URL}/alerts/${alertId}/acknowledge`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}

export const resolveAlert = async (token: string, alertId: number) => {
  const response = await axios.post(`${BASE_URL}/alerts/${alertId}/resolve`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return response.data
}
