import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Input from './pages/Input'
import Output from './pages/Output'
import Profile from './pages/Profile'
import GitHubCallback from './pages/GitHubCallback'
import ProtectedRoute from './components/ProtectedRoute'
import ToastContainer from './components/Toast'

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/"                       element={<Home />} />
        <Route path="/dashboard"              element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/login"                  element={<Login />} />
        <Route path="/register"               element={<Register />} />
        <Route path="/input"                  element={<ProtectedRoute><Input /></ProtectedRoute>} />
        <Route path="/output/:docId"          element={<ProtectedRoute><Output /></ProtectedRoute>} />
        <Route path="/profile"               element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/auth/github/callback"   element={<GitHubCallback />} />
      </Routes>
      <ToastContainer />
    </>
  )
}
