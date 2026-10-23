import { useState, useEffect } from 'react'
import { useNavigate, Navigate, Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { validateInvitationApi } from '../services/api'
import {
  FlaskConical,
  Lock,
  Mail,
  User,
  KeyRound,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Loader2,
  ShieldAlert,
  Info,
  Terminal,
  ArrowLeft,
} from 'lucide-react'

export default function SignUp() {
  const [searchParams] = useSearchParams()
  const initialToken = searchParams.get('token') || ''

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [invitationToken, setInvitationToken] = useState(initialToken)

  const [tokenStatus, setTokenStatus] = useState(null) // { valid, email, message }
  const [checkingToken, setCheckingToken] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { signup, user, isLabAuthority } = useAuth()
  const navigate = useNavigate()

  // Redirect if already authenticated as Lab Authority
  if (user && isLabAuthority) {
    return <Navigate to="/dashboard" replace />
  }

  // Pre-validate token if present in query parameter
  useEffect(() => {
    if (initialToken) {
      checkTokenValidity(initialToken)
    }
  }, [initialToken])

  const checkTokenValidity = async (tok) => {
    if (!tok || !tok.trim()) {
      setTokenStatus(null)
      return
    }
    setCheckingToken(true)
    try {
      const res = await validateInvitationApi(tok.trim())
      setTokenStatus(res)
      if (res.valid && res.email) {
        setEmail(res.email)
      }
    } catch (_) {
      setTokenStatus({ valid: false, message: 'Could not verify invitation token.' })
    } finally {
      setCheckingToken(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim() || !email.trim() || !password || !confirmPassword || !invitationToken.trim()) {
      setError('All fields including the invitation token are required.')
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
        invitation_token: invitationToken.trim(),
      })

      if (result.success) {
        navigate('/dashboard', { replace: true })
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
            Invitation-protected account registration for certified water testing personnel.
          </p>
        </div>

        {/* Signup Card */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm space-y-6">
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
            {/* Invitation Token Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  Administrative Invitation Token <span className="text-rose-500">*</span>
                </label>
                {checkingToken && (
                  <span className="text-[11px] text-slate-500 flex items-center gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" /> Verifying...
                  </span>
                )}
              </div>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  value={invitationToken}
                  onChange={(e) => {
                    setInvitationToken(e.target.value)
                    if (e.target.value.length > 20) {
                      checkTokenValidity(e.target.value)
                    } else {
                      setTokenStatus(null)
                    }
                  }}
                  onBlur={() => checkTokenValidity(invitationToken)}
                  className="input pl-9 text-slate-800 font-mono text-xs"
                  placeholder="Paste your single-use invitation token"
                  autoComplete="off"
                />
              </div>

              {/* Token validation feedback */}
              {tokenStatus && (
                <div
                  className={`mt-1.5 rounded p-2 text-xs flex items-center gap-2 ${
                    tokenStatus.valid
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : 'bg-rose-50 text-rose-800 border border-rose-200'
                  }`}
                >
                  {tokenStatus.valid ? (
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                  ) : (
                    <AlertCircle className="h-3.5 w-3.5 shrink-0 text-rose-600" />
                  )}
                  <span className="text-[11px]">
                    {tokenStatus.message}
                    {tokenStatus.email && ` Restricted to: ${tokenStatus.email}`}
                  </span>
                </div>
              )}
            </div>

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
                  disabled={tokenStatus?.valid && !!tokenStatus?.email}
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
                  <span>Validating & Registering...</span>
                </>
              ) : (
                <>
                  <span>Create Lab Authority Account</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Invitation Policy Notice */}
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-3.5 space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-1.5 text-slate-800 font-semibold">
              <Info className="h-4 w-4 text-ocean shrink-0" />
              <span>Invitation-Based Provisioning Policy</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-600">
              Self-registration without authorization is strictly prohibited. Accounts created here are automatically granted the <strong>LAB_AUTHORITY</strong> role upon successful invitation validation.
            </p>
            <p className="text-[11px] leading-relaxed text-slate-600">
              Invitations can be issued by administrators via the CLI or by existing Lab Authorities:
            </p>
            <div className="rounded bg-slate-900 text-slate-200 p-2 font-mono text-[10.5px] space-y-1 overflow-x-auto">
              <div className="flex items-center gap-1 text-cyan-400 font-sans text-[10px] uppercase font-bold">
                <Terminal className="h-3 w-3" />
                <span>Admin Command to Issue Token</span>
              </div>
              <div className="select-all">
                python assign_lab_authority.py --invite --email "analyst@lab.aquawatch.ai"
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
        </div>
      </div>
    </div>
  )
}
