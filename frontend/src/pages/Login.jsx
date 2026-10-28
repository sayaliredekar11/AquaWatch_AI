import { useState } from 'react'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  FlaskConical,
  Lock,
  Mail,
  AlertCircle,
  ArrowRight,
  Loader2,
  ShieldAlert,
  Info,
  Terminal,
  ArrowLeft,
} from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login, user, isLabAuthority } = useAuth()
  const navigate = useNavigate()

  // Redirect to Dashboard if already authenticated as Lab Authority
  if (user && isLabAuthority) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const result = await login(email, password)
      if (result.success) {
        navigate('/dashboard', { replace: true })
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
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-ocean/10 text-ocean mb-1">
            <FlaskConical className="h-6 w-6" />
          </div>
          <div className="inline-block rounded-full bg-slate-900 px-3 py-0.5 text-[11px] font-bold uppercase tracking-wider text-white">
            Authorized Personnel Only
          </div>
          <h1 className="text-2xl font-extrabold text-ink sm:text-3xl">
            Laboratory Authority Login
          </h1>
          <p className="text-sm text-slate-600">
            Sign in to access water sampling, WQI assessment, and laboratory monitoring.
          </p>
        </div>

        {/* Login Card */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm space-y-6">
          {error && (
            <div className="rounded-lg bg-rose-50 border border-rose-200 p-3.5 text-xs font-semibold text-rose-800 flex items-start gap-2.5">
              <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-rose-600" />
              <div className="space-y-1">
                <p className="font-bold">Access Denied</p>
                <p className="font-normal text-rose-700 leading-relaxed">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                Lab Authority Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input pl-9 text-slate-800 text-sm"
                  placeholder="lab@aquawatch.ai"
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pl-9 text-slate-800 text-sm"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full btn-primary font-semibold flex items-center justify-center gap-2 py-2.5 shadow-sm mt-3 disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <span>Sign In as Lab Authority</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Account Policy & Provisioning Notice */}
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-3.5 space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-1.5 text-slate-800 font-semibold">
              <Info className="h-4 w-4 text-ocean shrink-0" />
              <span>Administrative Account Provisioning</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-600">
              Normal users do not need an account to view water quality maps, intelligence summaries, or historical data.
            </p>
            <p className="text-[11px] leading-relaxed text-slate-600">
              Laboratory Authority credentials are created directly on the server by the system administrator:
            </p>
            <div className="rounded bg-slate-900 text-slate-200 p-2 font-mono text-[10.5px] space-y-1 overflow-x-auto">
              <div className="flex items-center gap-1 text-cyan-400 font-sans text-[10px] uppercase font-bold">
                <Terminal className="h-3 w-3" />
                <span>Admin Provisioning Command</span>
              </div>
              <div className="select-all">
                python assign_lab_authority.py --create --name "Dr. Patil" --email "patil@lab.aquawatch.ai" --password "SecurePass123!"
              </div>
            </div>
          </div>

          {/* Return Links */}
          <div className="text-center pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <Link
              to="/signup"
              className="inline-flex items-center gap-1 text-ocean hover:text-cyan-800 transition-colors font-semibold"
            >
              <span>Have an invitation token? Sign Up</span>
            </Link>
            <Link
              to="/map"
              className="inline-flex items-center gap-1 hover:text-ocean transition-colors font-medium"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Explore Public Map</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
