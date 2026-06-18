import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Input from './pages/Input'
import InputPython from './pages/InputPython'
import InputUniversal from './pages/InputUniversal'
import Output from './pages/Output'
import UniversalOutput from './pages/UniversalOutput'
import Profile from './pages/Profile'
import GitHubCallback from './pages/GitHubCallback'
import AdminFeedback from './pages/AdminFeedback'
import AdminUsers from './pages/AdminUsers'
import AdminProjects from './pages/AdminProjects'
import FeedbackPage from './pages/FeedbackPage'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import ProtectedRoute from './components/ProtectedRoute'
import ToastContainer from './components/Toast'

const Published = lazy(() => import('./pages/Published'))
const PublicDoc = lazy(() => import('./pages/PublicDoc'))

export default function App() {
  return (
    <>
      <Routes>
        {/* Public Routes */}
        <Route path="/"                      element={<Home />} />
        <Route path="/login"                  element={<Login />} />
        <Route path="/register"               element={<Register />} />
        <Route path="/auth/github/callback"   element={<GitHubCallback />} />
        <Route path="/forgot-password"        element={<ForgotPassword />} />
        <Route path="/reset-password"         element={<ResetPassword />} />

        {/* Published Gallery */}
        <Route path="/published" element={
          <Suspense fallback={<div className="text-center text-ink-muted py-20">Loading...</div>}>
            <Published />
          </Suspense>
        } />
        <Route path="/public/:slug" element={
          <Suspense fallback={<div className="text-center text-ink-muted py-20">Loading...</div>}>
            <PublicDoc />
          </Suspense>
        } />

        {/* Core Authenticated App Routes */}
        <Route path="/dashboard"              element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/input"                  element={<ProtectedRoute><Input /></ProtectedRoute>} />
        <Route path="/input/python"           element={<ProtectedRoute><InputPython /></ProtectedRoute>} />
        <Route path="/input/universal"        element={<ProtectedRoute><InputUniversal /></ProtectedRoute>} />
        <Route path="/output/:docId"          element={<ProtectedRoute><Output /></ProtectedRoute>} />
        <Route path="/output/universal/:id"   element={<ProtectedRoute><UniversalOutput /></ProtectedRoute>} />
        <Route path="/profile"                element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/projects"               element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />

        {/* Unified User Feedback Hub */}
        <Route path="/feedback"               element={<ProtectedRoute><FeedbackPage /></ProtectedRoute>} />

        {/* Administration Infrastructure Management Control */}
        <Route path="/admin/stats"            element={<ProtectedRoute><AdminProjects /></ProtectedRoute>} />
        <Route path="/admin/feedback"         element={<ProtectedRoute><AdminFeedback /></ProtectedRoute>} />
        <Route path="/admin/users"            element={<ProtectedRoute><AdminUsers /></ProtectedRoute>} />
      </Routes>
      <ToastContainer />
    </>
  )
}
