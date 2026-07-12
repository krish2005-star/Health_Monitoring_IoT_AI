import axios from 'axios'

const API = axios.create({ baseURL: 'http://localhost:8000' })

API.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

API.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.clear()
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export const login           = (data) => API.post('/login', data)
export const registerPatient = (data) => API.post('/register/patient', data)
export const registerDoctor  = (data) => API.post('/register/doctor', data)
export const getDoctors      = ()     => axios.get('http://localhost:8000/doctors/list')

export const getMyVitals     = ()     => API.get('/me/vitals')
export const getMyAlerts     = ()     => API.get('/me/alerts')
export const getMyProfile    = ()     => API.get('/me/profile')

export const getGuardianData = ()     => API.get('/guardian/patient')

export const getDoctorPatients     = ()   => API.get('/doctor/patients')
export const getDoctorPatientDetail= (id) => API.get(`/doctor/patient/${id}`)

export const getVitals  = (id) => API.get(`/vitals/${id}`)
export const getAlerts  = (id) => API.get(`/alerts/${id}`)