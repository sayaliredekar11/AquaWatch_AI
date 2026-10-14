import { NavLink, Link, useNavigate } from 'react-router-dom'
import { Droplets, User, LogOut, LogIn, UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout, isLabAuthority } = useAuth()
  const navigate = useNavigate()

  // Public links available to everyone (logged out and Normal User)
  const publicLinks = [
    ['/', 'Home'],
    ['/map', 'Water Quality Map'],
    ['/intelligence', 'Water Intelligence'],
    ['/about', 'About'],
  ]

  // Role-specific links: Lab Authority gets Dashboard and Test Water
  const links = isLabAuthority
    ? [
        ['/', 'Home'],
        ['/dashboard', 'Dashboard'],
        ['/map', 'Water Quality Map'],
        ['/test', 'Test Water'],
        ['/intelligence', 'Water Intelligence'],
        ['/about', 'About'],
      ]
    : publicLinks

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="border-b border-slate-200/80 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex flex-wrap items-center gap-6 lg:gap-10">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold text-ink">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ocean/10 text-ocean">
              <Droplets className="h-5 w-5" />
            </div>
            <span>
              AquaWatch <span className="text-ocean">AI</span>
            </span>
          </Link>
          <nav className="flex flex-wrap items-center gap-1.5 text-sm font-medium">
            {links.map(([to, label]) => (
              <NavLink
                key={`${to}-${label}`}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `rounded-lg px-3.5 py-1.5 transition-colors ${
                    isActive
                      ? 'bg-cyan-100/70 text-ocean font-semibold'
                      : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3 text-sm font-medium text-slate-700">
          {user ? (
            <>
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-white">
                  <User className="h-4 w-4" />
                </div>
                <span>{user.name}</span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <LogIn className="h-3.5 w-3.5" />
                <span>Login</span>
              </Link>
              <Link
                to="/signup"
                className="flex items-center gap-1 rounded-lg bg-ocean px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#0c627a] transition-colors shadow-xs"
              >
                <UserPlus className="h-3.5 w-3.5" />
                <span>Sign Up</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
