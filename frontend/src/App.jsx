import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import WaterMap from './pages/WaterMap'
import TestWater from './pages/TestWater'
import WaterIntelligence from './pages/WaterIntelligence'
import About from './pages/About'
import Login from './pages/Login'
import SignUp from './pages/SignUp'

export default function App() {
  return (
    <AuthProvider>
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            {/* Public routes accessible to everyone without login */}
            <Route path="/" element={<Home />} />
            <Route path="/map" element={<WaterMap />} />
            <Route path="/water-quality-map" element={<Navigate to="/map" replace />} />
            <Route path="/intelligence" element={<WaterIntelligence />} />
            <Route path="/about" element={<About />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/sign-up" element={<Navigate to="/signup" replace />} />

            {/* Protected routes restricted to Lab Authority only */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute allowedRoles={['LAB_AUTHORITY', 'lab_authority']}>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/test"
              element={
                <ProtectedRoute allowedRoles={['LAB_AUTHORITY', 'lab_authority']}>
                  <TestWater />
                </ProtectedRoute>
              }
            />
            <Route path="/test-water" element={<Navigate to="/test" replace />} />

            {/* Fallback route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </AuthProvider>
  )
}
