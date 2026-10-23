import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading, isLabAuthority } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ocean border-t-transparent" />
      </div>
    )
  }

  // Not authenticated -> redirect to login
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Role check: if route requires lab authority and user is not lab authority
  if (allowedRoles && allowedRoles.length > 0) {
    const requiresLab = allowedRoles.some((r) =>
      ['LAB_AUTHORITY', 'lab_authority'].includes(r)
    )

    if (requiresLab && !isLabAuthority) {
      // Non-lab user trying to access lab dashboard or test water -> redirect to Lab Login
      return <Navigate to="/login" state={{ from: location }} replace />
    }
  }

  return children
}
