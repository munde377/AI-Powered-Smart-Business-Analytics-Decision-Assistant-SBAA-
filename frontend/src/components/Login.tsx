import { useState, type FormEvent } from 'react'
import { login } from '../services/api'

interface Props {
  onAuthenticate: (token: string) => void
}

export default function Login({ onAuthenticate }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      const data = await login(email, password)
      onAuthenticate(data.access_token)
    } catch {
      setError('Login failed. Please verify your credentials.')
    }
  }

  return (
    <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
      <h2 className="text-2xl font-semibold text-white">Login</h2>
      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <label className="block text-slate-300">
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" />
        </label>
        <label className="block text-slate-300">
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" />
        </label>
        <button type="submit" className="w-full rounded bg-blue-600 px-4 py-2 font-semibold text-white transition hover:bg-blue-500">
          Sign in
        </button>
      </form>
      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
    </div>
  )
}
