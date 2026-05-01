import { useState, type FormEvent } from 'react'
import { register } from '../services/api'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      await register(email, password)
      setMessage('Registration successful. You can now login.')
    } catch {
      setMessage('Registration failed. Please use another email.')
    }
  }

  return (
    <div className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
      <h2 className="text-2xl font-semibold text-white">Register</h2>
      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <label className="block text-slate-300">
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" />
        </label>
        <label className="block text-slate-300">
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" />
        </label>
        <button type="submit" className="w-full rounded bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400">
          Create account
        </button>
      </form>
      {message && <p className="mt-3 text-sm text-slate-300">{message}</p>}
    </div>
  )
}
