import { createContext, useContext, useState, useEffect } from 'react'
import {
  getToken,
  setToken,
  removeToken,
  loginApi,
  registerApi,
  getProfileApi,
  USER_KEY,
} from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem(USER_KEY)
      if (!saved) return null
      const parsed = JSON.parse(saved)
      // Only retain saved session if user is a Lab Authority
      const isLab =
        parsed?.role === 'LAB_AUTHORITY' || parsed?.role === 'lab_authority'
      return isLab ? parsed : null
    } catch (_) {
      return null
    }
  })
  const [loading, setLoading] = useState(true)

  // Validate existing session token against backend on mount
  useEffect(() => {
    async function verifySession() {
      const token = getToken()
      if (!token) {
        setLoading(false)
        return
      }

      try {
        const profile = await getProfileApi()
        const isLab =
          profile?.role === 'LAB_AUTHORITY' || profile?.role === 'lab_authority'

        if (!isLab) {
          // If a non-lab account token was stored, clear it immediately
          console.warn('Non-lab account detected; clearing session token.')
          removeToken()
          setUser(null)
        } else {
          setUser(profile)
          localStorage.setItem(USER_KEY, JSON.stringify(profile))
        }
      } catch (err) {
        // If token has expired or is invalid, safely clear state
        console.warn('Session verification failed, logging out:', err.message)
        removeToken()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    verifySession()
  }, [])

  /**
   * Log in user against FastAPI backend (restricted to Laboratory Authorities)
   */
  const login = async (email, password) => {
    try {
      const tokenData = await loginApi(email, password)
      setToken(tokenData.access_token)

      // Fetch verified user profile from /auth/me
      const profile = await getProfileApi()
      const isLab =
        profile?.role === 'LAB_AUTHORITY' || profile?.role === 'lab_authority'

      if (!isLab) {
        removeToken()
        setUser(null)
        return {
          success: false,
          error:
            'Access restricted: This portal is exclusively for authorized Laboratory Authorities. Public features do not require an account.',
        }
      }

      setUser(profile)
      localStorage.setItem(USER_KEY, JSON.stringify(profile))

      return {
        success: true,
        user: profile,
        role: profile.role,
      }
    } catch (err) {
      removeToken()
      setUser(null)
      return {
        success: false,
        error:
          err.message || 'Login failed. Please check your credentials.',
      }
    }
  }

  /**
   * Register a new Lab Authority account
   */
  const signup = async ({ name, email, password }) => {
    try {
      const regUser = await registerApi(name, email, password)
      if (regUser && regUser.is_active === false) {
        return {
          success: true,
          pendingApproval: true,
          user: regUser,
          message:
            'Registration submitted successfully! Your account is pending administrator approval before you can access the Laboratory Authority dashboard.',
        }
      }
      // If immediately active, automatically log in
      return await login(email, password)
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Registration failed.',
      }
    }
  }

  /**
   * Log out current Lab Authority and clear session tokens
   */
  const logout = () => {
    removeToken()
    setUser(null)
  }

  const isLabAuthority = Boolean(
    user && (user.role === 'LAB_AUTHORITY' || user.role === 'lab_authority')
  )

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        isLabAuthority,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
