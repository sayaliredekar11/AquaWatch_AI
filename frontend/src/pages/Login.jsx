import { useState } from 'react'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Droplets, Lock, Mail, AlertCircle, ArrowRight, Loader2 } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login, user, isLabAuthority } = useAuth()
  const navigate = useNavigate()

  // Redirect if already logged in
  if (user) {
    const defaultTarget = isLabAuthority ? '/dashboard' : '/'
    return <Navigate to={defaultTarget} replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const result = await login(email, password)
      if (result.success) {
        const isLab =
          result.role === 'LAB_AUTHORITY' || result.role === 'lab_authority'
        const target = isLab ? '/dashboard' : '/'
        navigate(target, { replace: true })
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-65px)] bg-mist flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-ocean/10 text-ocean mb-1">
            <Droplets className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-extrabold text-ink sm:text-3xl">Sign in to AquaWatch AI</h1>
          <p className="text-sm text-slate-600">Access water-quality assessments & laboratory monitoring</p>
        </div>

        <div className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm space-y-6">
          {error && (
            <div className="rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs font-semibold text-rose-700 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 mb-1.5 block">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input pl-9 text-slate-800"
                  placeholder="user@example.com"
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 mb-1.5 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pl-9 text-slate-800"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full btn-primary font-semibold flex items-center justify-center gap-2 py-2.5 shadow-sm mt-2 disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Sign Up Link */}
          <div className="text-center pt-1 border-t border-slate-100">
            <p className="text-xs text-slate-600">
              Don't have an account?{' '}
              <Link to="/signup" className="font-semibold text-ocean hover:text-cyan-800 transition-colors">
                Sign Up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
