import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Input from './pages/Input'
import Output from './pages/Output'
import Profile from './pages/Profile'
import GitHubCallback from './pages/GitHubCallback'
import AdminFeedback from './pages/AdminFeedback'
import AdminUsers from './pages/AdminUsers'
import AdminProjects from './pages/AdminProjects'
import FeedbackPage from './pages/FeedbackPage' // The unified hub
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import ProtectedRoute from './components/ProtectedRoute'
import ToastContainer from './components/Toast'

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

        {/* Core Authenticated App Routes */}
        <Route path="/dashboard"              element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/input"                  element={<ProtectedRoute><Input /></ProtectedRoute>} />
        <Route path="/output/:docId"          element={<ProtectedRoute><Output /></ProtectedRoute>} />
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