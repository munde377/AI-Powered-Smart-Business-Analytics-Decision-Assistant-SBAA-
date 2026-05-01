import { useState, useEffect, useRef } from 'react'
import { MessageSquare, Send, Bot, User, Database } from 'lucide-react'
import { chatWithData, getChatHistory, getDatasets } from '../services/api'

interface Props {
  token: string
}

interface ChatMessage {
  id?: number
  query: string
  response: string
  sql?: string
  timestamp: string
}

export default function Chat({ token }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [datasetId, setDatasetId] = useState('')
  const [loading, setLoading] = useState(false)
  const [datasets, setDatasets] = useState<any[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadDatasets()
    loadChatHistory()
  }, [token])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadDatasets = async () => {
    try {
      const data = await getDatasets(token)
      setDatasets(data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
      setDatasets([])
    }
  }

  const loadChatHistory = async () => {
    try {
      const history = await getChatHistory(token)
      const formattedHistory = history.map((item: any) => ({
        id: item.id,
        query: item.query,
        response: item.response,
        sql: item.sql_query,
        timestamp: item.created_at
      }))
      setMessages(formattedHistory)
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!input.trim() || !datasetId) return

    const userMessage: ChatMessage = {
      query: input,
      response: '',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setLoading(true)
    setInput('')

    try {
      const result = await chatWithData(token, input, parseInt(datasetId))

      const aiMessage: ChatMessage = {
        query: input,
        response: result.answer,
        sql: result.sql,
        timestamp: new Date().toISOString()
      }

      setMessages(prev => prev.slice(0, -1).concat(aiMessage))
    } catch (error) {
      const errorMessage: ChatMessage = {
        query: input,
        response: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => prev.slice(0, -1).concat(errorMessage))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
        <h2 className="text-2xl font-semibold text-white mb-6 flex items-center space-x-2">
          <MessageSquare className="h-6 w-6 text-emerald-400" />
          <span>AI Data Assistant</span>
        </h2>

        {/* Dataset Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center space-x-2">
            <Database className="h-4 w-4" />
            <span>Select Dataset to Chat With</span>
          </label>
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
          >
            <option value="">Choose a dataset...</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.filename} ({dataset.row_count} rows)
              </option>
            ))}
          </select>
        </div>

        {/* Chat Messages */}
        <div className="bg-slate-800 rounded-lg p-4 mb-4 h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="text-center text-slate-400 py-8">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Start a conversation with your data!</p>
              <p className="text-sm mt-2">Ask questions like "What are the top selling products?" or "Show me sales trends"</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div key={index} className="space-y-3">
                  {/* User Message */}
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center">
                      <User className="h-4 w-4 text-slate-950" />
                    </div>
                    <div className="flex-1 bg-slate-700 rounded-lg p-3">
                      <p className="text-white">{message.query}</p>
                    </div>
                  </div>

                  {/* AI Response */}
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1 bg-slate-700 rounded-lg p-3">
                      <div className="text-slate-300 whitespace-pre-wrap">{message.response}</div>
                      {message.sql && (
                        <div className="mt-3 p-2 bg-slate-800 rounded text-xs font-mono text-emerald-400">
                          <div className="text-slate-400 mb-1">Generated SQL:</div>
                          {message.sql}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                  <div className="flex-1 bg-slate-700 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-400"></div>
                      <span className="text-slate-300">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your data..."
            disabled={!datasetId || loading}
            className="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !datasetId || loading}
            className="px-6 py-3 bg-emerald-500 text-slate-950 rounded-lg hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Send className="h-4 w-4" />
            <span>Send</span>
          </button>
        </div>

        {!datasetId && (
          <p className="text-sm text-slate-400 mt-2">
            Please select a dataset to start chatting with your data.
          </p>
        )}
      </div>
    </section>
  )
}