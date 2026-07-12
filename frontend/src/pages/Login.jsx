import { useState } from 'react'
import { login } from '../api'

export default function Login({ onLogin, onRegister }) {
  const [form, setForm] = useState({ email:'', password:'' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setLoading(true); setError('')
    try {
      const res = await login(form)
      onLogin(res.data)
    } catch {
      setError('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl
                      p-8 w-full max-w-sm">
        <h1 className="text-xl font-semibold text-white mb-1">
          HealthMonitor
        </h1>
        <p className="text-sm text-gray-400 mb-6">Sign in to your account</p>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-400
                          text-sm rounded-lg px-4 py-2 mb-4">{error}</div>
        )}

        <div className="space-y-3">
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg
                       px-4 py-2.5 text-sm text-white placeholder-gray-500
                       focus:outline-none focus:border-blue-500"
            placeholder="Email"
            type="email"
            value={form.email}
            onChange={e => setForm({...form, email: e.target.value})}
          />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg
                       px-4 py-2.5 text-sm text-white placeholder-gray-500
                       focus:outline-none focus:border-blue-500"
            placeholder="Password"
            type="password"
            value={form.password}
            onChange={e => setForm({...form, password: e.target.value})}
          />
          <button
            onClick={submit}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white
                       rounded-lg py-2.5 text-sm font-medium transition
                       disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </div>

        <p className="text-center text-sm text-gray-500 mt-4">
          New patient?{' '}
          <button onClick={onRegister}
                  className="text-blue-400 hover:underline">
            Register here
          </button>
        </p>
      </div>
    </div>
  )
}