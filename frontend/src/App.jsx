import { useState, useEffect } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import PatientDashboard from './pages/PatientDashboard'
import GuardianDashboard from './pages/GuardianDashboard'
import DoctorDashboard from './pages/DoctorDashboard'

export default function App() {
  const [page, setPage]   = useState('login')
  const [user, setUser]   = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const role  = localStorage.getItem('role')
    const name  = localStorage.getItem('name')
    if (token) setUser({ role, name })
  }, [])

  const handleLogin = (userData) => {
  localStorage.setItem('token', userData.access_token)
  localStorage.setItem('role', userData.role)
  localStorage.setItem('name', userData.name)

  if (userData.patient_id) {
    localStorage.setItem(
      'patient_id',
      userData.patient_id
    )
  }

  setUser(userData)
}

  const handleLogout = () => {
    localStorage.clear()
    setUser(null)
    setPage('login')
  }

  if (!user) {
    return page === 'login'
      ? <Login onLogin={handleLogin} onRegister={() => setPage('register')} />
      : <Register onBack={() => setPage('login')} onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Top nav */}
      <nav className="bg-gray-900 border-b border-gray-800
                      px-6 py-3 flex justify-between items-center">
        <span className="font-semibold text-blue-400">HealthMonitor</span>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">
            {user.name}
            <span className="ml-2 text-xs bg-blue-900 text-blue-300
                             px-2 py-0.5 rounded-full capitalize">
              {user.role}
            </span>
          </span>
          <button onClick={handleLogout}
                  className="text-xs text-gray-500 hover:text-white transition">
            Logout
          </button>
        </div>
      </nav>

      {/* Role-based view */}
      <div className="p-6">
        {user.role === 'patient'  && <PatientDashboard />}
        {user.role === 'guardian' && <GuardianDashboard />}
        {user.role === 'doctor'   && <DoctorDashboard />}
        {user.role === 'admin'    && <div>Admin panel coming soon</div>}
      </div>
    </div>
  )
}