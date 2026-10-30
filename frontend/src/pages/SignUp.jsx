import { useState } from 'react'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  FlaskConical,
  Lock,
  Mail,
  User,
  ArrowRight,
  Loader2,
  ShieldAlert,
  CheckCircle2,
  Info,
  Terminal,
  ArrowLeft,
  Clock,
} from 'lucide-react'

export default function SignUp() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submittedPending, setSubmittedPending] = useState(false)

  const { signup, user, isLabAuthority } = useAuth()
  const navigate = useNavigate()

  // Redirect if already authenticated as Lab Authority
  if (user && isLabAuthority) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim() || !email.trim() || !password || !confirmPassword) {
      setError('All fields are required.')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Password and Confirm Password do not match.')
      return
    }

    setSubmitting(true)

    try {
      const result = await signup({
        name: name.trim(),
        email: email.trim(),
        password,
      })

      if (result.success) {
        if (result.pendingApproval) {
          setSubmittedPending(true)
        } else {
          navigate('/dashboard', { replace: true })
        }
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during registration.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-65px)] bg-mist flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-lg space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-ocean/10 text-ocean mb-1">
            <FlaskConical className="h-6 w-6" />
          </div>
          <div className="inline-block rounded-full bg-slate-900 px-3 py-0.5 text-[11px] font-bold uppercase tracking-wider text-white">
            Authorized Personnel Only
          </div>
          <h1 className="text-2xl font-extrabold text-ink sm:text-3xl">
            Laboratory Authority Signup
          </h1>
          <p className="text-sm text-slate-600">
            Account registration for certified water testing personnel.
          </p>
        </div>

        {/* Signup Card */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm space-y-6">
          {submittedPending ? (
            <div className="space-y-6 text-center py-2">
              <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 mb-1">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-slate-900">
                  Registration Submitted
                </h2>
                <p className="text-sm text-slate-600 max-w-md mx-auto leading-relaxed">
                  Your Laboratory Authority account for <strong className="text-slate-800">{email}</strong> has been registered successfully.
                </p>
              </div>

              <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-left text-xs text-amber-900 space-y-2">
                <div className="flex items-center gap-2 font-semibold">
                  <Clock className="h-4 w-4 text-amber-700 shrink-0" />
                  <span>Pending Administrator Approval</span>
                </div>
                <p className="text-[12px] leading-relaxed text-amber-800">
                  Access to the laboratory testing portal is restricted to verified personnel. Your account will be activated once an administrator approves your registration.
                </p>
                <div className="mt-2 pt-2 border-t border-amber-200/60 font-mono text-[11px] text-amber-950">
                  Admin approval command: <span className="font-bold">python assign_lab_authority.py --approve {email}</span>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <Link
                  to="/login"
                  className="flex-1 btn-primary py-2.5 text-xs font-semibold flex items-center justify-center gap-1.5 shadow-sm"
                >
                  <span>Go to Login</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <Link
                  to="/map"
                  className="flex-1 rounded-lg border border-slate-200 px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center gap-1.5"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Explore Public Map</span>
                </Link>
              </div>
            </div>
          ) : (
            <>
              {error && (
                <div className="rounded-lg bg-rose-50 border border-rose-200 p-3.5 text-xs font-semibold text-rose-800 flex items-start gap-2.5">
                  <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-rose-600" />
                  <div className="space-y-1">
                    <p className="font-bold">Registration Rejected</p>
                    <p className="font-normal text-rose-700 leading-relaxed">{error}</p>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Full Name */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                    Full Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="input pl-9 text-slate-800 text-sm"
                      placeholder="Dr. Sunita Patil"
                      autoComplete="name"
                    />
                  </div>
                </div>

                {/* Email Address */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                    Official Email Address <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="input pl-9 text-slate-800 text-sm"
                      placeholder="analyst@lab.aquawatch.ai"
                      autoComplete="email"
                    />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                    Password <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="input pl-9 text-slate-800 text-sm"
                      placeholder="At least 6 characters"
                      autoComplete="new-password"
                    />
                  </div>
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                    Confirm Password <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="input pl-9 text-slate-800 text-sm"
                      placeholder="Repeat your password"
                      autoComplete="new-password"
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
                      <span>Creating Account...</span>
                    </>
                  ) : (
                    <>
                      <span>Create Lab Authority Account</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Portal Authorization Notice */}
              <div className="rounded-lg bg-slate-50 border border-slate-200 p-3.5 space-y-2 text-xs text-slate-600">
                <div className="flex items-center gap-1.5 text-slate-800 font-semibold">
                  <Info className="h-4 w-4 text-ocean shrink-0" />
                  <span>Laboratory Authority Access Policy</span>
                </div>
                <p className="text-[11px] leading-relaxed text-slate-600">
                  Laboratory Authority accounts are granted permissions to submit water quality sampling data and calculate WQI indices. To safeguard water quality data integrity, newly registered accounts require administrator approval before logging in.
                </p>
                <div className="rounded bg-slate-900 text-slate-200 p-2 font-mono text-[10.5px] space-y-1 overflow-x-auto">
                  <div className="flex items-center gap-1 text-cyan-400 font-sans text-[10px] uppercase font-bold">
                    <Terminal className="h-3 w-3" />
                    <span>Administrator Approval Command</span>
                  </div>
                  <div className="select-all">
                    python assign_lab_authority.py --approve "analyst@lab.aquawatch.ai"
                  </div>
                </div>
              </div>

              {/* Links */}
              <div className="text-center pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1 text-ocean hover:text-cyan-800 transition-colors font-medium"
                >
                  <span>Already registered? Sign In</span>
                </Link>
                <Link
                  to="/map"
                  className="inline-flex items-center gap-1 hover:text-ocean transition-colors font-medium"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Explore Public Map</span>
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
