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
      return saved ? JSON.parse(saved) : null
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
        setUser(profile)
        localStorage.setItem(USER_KEY, JSON.stringify(profile))
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
   * Log in user against FastAPI backend
   */
  const login = async (email, password) => {
    try {
      const tokenData = await loginApi(email, password)
      setToken(tokenData.access_token)

      // Fetch authentic user profile from /auth/me
      const profile = await getProfileApi()
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
        error: err.message || 'Login failed. Please check your credentials.',
      }
    }
  }

  /**
   * Register a new user against FastAPI backend (defaults to citizen/normal user)
   */
  const signup = async ({ name, email, password }) => {
    try {
      await registerApi(name, email, password)

      // Automatically log in newly registered user
      return await login(email, password)
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Registration failed.',
      }
    }
  }

  /**
   * Log out current user and clear local storage
   */
  const logout = () => {
    removeToken()
    setUser(null)
  }

  const isLabAuthority =
    user?.role === 'LAB_AUTHORITY' || user?.role === 'lab_authority'
  const isNormalUser = user && !isLabAuthority

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        isLabAuthority,
        isNormalUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
