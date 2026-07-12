import { useState, useEffect } from 'react'
import { registerPatient, registerDoctor, getDoctors } from '../api'

export default function Register({ onBack, onLogin }) {
  const [role,    setRole]    = useState(null)  // "patient" or "doctor"
  const [step,    setStep]    = useState(1)
  const [doctors, setDoctors] = useState([])
  // inline error box used for validation and server errors
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const [patientForm, setPatientForm] = useState({
    name:'', email:'', password:'', age:'', gender:'',
    blood_group:'', phone:'', address:'',
    guardian_name:'', guardian_phone:'',
    guardian_email:'', guardian_relation:'',
    doctor_id:''
  })

  const [doctorForm, setDoctorForm] = useState({
    name:'', email:'', password:'',
    specialization:'', phone:''
  })

  useEffect(() => {
    getDoctors().then(r => setDoctors(r.data)).catch(() => {})
  }, [])

  const setP = (k, v) => setPatientForm(f => ({...f, [k]: v}))
  const setD = (k, v) => setDoctorForm(f  => ({...f, [k]: v}))

  const inp = (label, val, onChange, type='text', opts=null) => (
    <div>
      <label className="text-xs text-gray-400 mb-1 block">{label}</label>
      {opts
        ? <select value={val} onChange={e => onChange(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700
                             rounded-lg px-3 py-2 text-sm text-white
                             focus:outline-none focus:border-blue-500">
            <option value="">Select...</option>
            {opts.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        : <input type={type} value={val}
                 onChange={e => onChange(e.target.value)}
                 className="w-full bg-gray-800 border border-gray-700
                            rounded-lg px-3 py-2 text-sm text-white
                            placeholder-gray-500 focus:outline-none
                            focus:border-blue-500"/>
      }
    </div>
  )

  const submitDoctor = async () => {
    setLoading(true)
    try {
      await registerDoctor(doctorForm)
      alert('Doctor registered! You can now login.')
      onBack()
    } catch (e) {
      const msg = e.response?.data?.detail || 'Registration failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const submitPatient = async () => {
    setLoading(true)
    try {
      // validate all steps before submitting
      if (!validateAll()) {
        setLoading(false)
        return
      }
      const payload = {...patientForm, age: parseInt(patientForm.age)}
      if (!payload.doctor_id) delete payload.doctor_id
      await registerPatient(payload)
      alert('Registered! Please login.')
      onBack()
    } catch (e) {
      const msg = e.response?.data?.detail || 'Registration failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const validateStep = (whichStep = step) => {
    // returns true if valid; shows inline error box on error
    setError('')
    if (whichStep === 1) {
      const req = ['name','email','password','age','phone','address','blood_group']
      const missing = req.filter(k => !patientForm[k] || String(patientForm[k]).trim() === '')
      if (missing.length) {
        setError('Please fill all required personal details before continuing.')
        return false
      }

      // email format
      const emailRe = /^\S+@\S+\.\S+$/
      if (!emailRe.test(patientForm.email)) {
        setError('Please enter a valid email address.')
        return false
      }

      // age numeric
      const ageNum = parseInt(patientForm.age)
      if (Number.isNaN(ageNum) || ageNum <= 0 || ageNum > 120) {
        setError('Please enter a valid age (1-120).')
        return false
      }

      // phone length (digits only)
      const phoneDigits = (patientForm.phone || '').replace(/\D/g, '')
      if (phoneDigits.length < 7 || phoneDigits.length > 15) {
        setError('Please enter a valid phone number (7-15 digits).')
        return false
      }

      // password strength
      const pw = patientForm.password || ''
      const pwOk = pw.length >= 8 && /[A-Za-z]/.test(pw) && /[0-9]/.test(pw)
      if (!pwOk) {
        setError('Password should be at least 8 characters and include letters and numbers.')
        return false
      }
    }

    if (whichStep === 2) {
      // guardian details required
      const req = ['guardian_name','guardian_phone','guardian_relation']
      const missing = req.filter(k => !patientForm[k] || String(patientForm[k]).trim() === '')
      if (missing.length) {
        setError('Please fill guardian details or go back if you want to skip.')
        return false
      }
    }

    setError('')
    return true
  }

  const validateAll = () => {
    // validate step 1 and 2 before final submit
    if (!validateStep(1)) return false
    if (!validateStep(2)) return false
    return true
  }

  const handleNext = () => {
    if (!validateStep()) return
    setError('')
    setStep(s => s+1)
  }

  // ── Role selector screen ──────────────────────────────
  if (!role) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center
                      justify-center">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl
                        p-8 w-full max-w-sm">
          <button onClick={onBack}
                  className="text-gray-500 hover:text-white text-sm mb-6 block">
            ← Back to login
          </button>
          <h2 className="text-lg font-semibold mb-1 text-white">Create account</h2>
          <p className="text-sm text-gray-400 mb-6">
            Who are you registering as?
          </p>
          <div className="space-y-3">
            <button onClick={() => setRole('patient')}
                    className="w-full bg-gray-800 hover:bg-blue-600
                               border border-gray-700 hover:border-blue-500
                               rounded-xl p-4 text-left transition-all group">
              <p className="font-medium text-white">Patient</p>
              <p className="text-xs text-gray-400 group-hover:text-blue-200 mt-0.5">
                Register yourself for health monitoring
              </p>
            </button>
            <button onClick={() => setRole('doctor')}
                    className="w-full bg-gray-800 hover:bg-teal-700
                               border border-gray-700 hover:border-teal-500
                               rounded-xl p-4 text-left transition-all group">
              <p className="font-medium text-white">Doctor</p>
              <p className="text-xs text-gray-400 group-hover:text-teal-200 mt-0.5">
                Register to monitor your patients
              </p>
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── Doctor registration form ──────────────────────────
  if (role === 'doctor') {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center
                      justify-center py-10">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl
                        p-8 w-full max-w-md">
          <div className="flex items-center gap-3 mb-6">
            <button onClick={() => setRole(null)}
                    className="text-gray-500 hover:text-white text-sm">
              ←
            </button>
            <div>
              <h2 className="text-lg font-semibold text-white">Doctor Registration</h2>
              <p className="text-xs text-gray-400">
                Create your doctor account
              </p>
            </div>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-700
                            text-red-400 text-sm rounded-lg
                            px-4 py-2 mb-4">{error}</div>
          )}

          <div className="space-y-3">
            {inp('Full name',      doctorForm.name,
                 v => setD('name', v))}
            {inp('Email',          doctorForm.email,
                 v => setD('email', v), 'email')}
            {inp('Password',       doctorForm.password,
                 v => setD('password', v), 'password')}
            {inp('Specialization', doctorForm.specialization,
                 v => setD('specialization', v), 'text', [
                   'Cardiology', 'Neurology', 'General Medicine',
                   'Orthopedics', 'Geriatrics', 'Pulmonology', 'Other'
                 ])}
            {inp('Phone', doctorForm.phone,
                 v => setD('phone', v))}
          </div>

          <button onClick={submitDoctor} disabled={loading}
                  className="w-full mt-6 bg-teal-600 hover:bg-teal-700
                             text-white rounded-lg py-2.5 text-sm
                             font-medium transition disabled:opacity-50">
            {loading ? 'Registering...' : 'Create doctor account'}
          </button>

          <p className="text-xs text-gray-500 text-center mt-3">
            After registering, patients can select you during their signup
          </p>
        </div>
      </div>
    )
  }

  // ── Patient registration form (3 steps) ──────────────
  return (
    <div className="min-h-screen bg-gray-950 flex items-center
                    justify-center py-10">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl
                      p-8 w-full max-w-lg">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => step > 1
                    ? setStep(s => s-1) : setRole(null)}
                  className="text-gray-500 hover:text-white text-sm">
            ←
          </button>
          <div>
            <h2 className="text-lg font-semibold text-white">Patient Registration</h2>
            <p className="text-xs text-gray-400">Step {step} of 3</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="flex gap-2 mb-6">
          {[1,2,3].map(s => (
            <div key={s} className={`flex-1 h-1 rounded-full transition-all
              ${s <= step ? 'bg-blue-500' : 'bg-gray-700'}`} />
          ))}
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700
                          text-red-400 text-sm rounded-lg
                          px-4 py-2 mb-4">{error}</div>
        )}

        {step === 1 && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-gray-300 mb-2">
              Personal details
            </p>
            {inp('Full name',   patientForm.name,
                 v => setP('name', v))}
            {inp('Email',       patientForm.email,
                 v => setP('email', v), 'email')}
            {inp('Password',    patientForm.password,
                 v => setP('password', v), 'password')}
            {inp('Age',         patientForm.age,
                 v => setP('age', v), 'number')}
            {inp('Gender',      patientForm.gender,
                 v => setP('gender', v), 'text',
                 ['Male', 'Female', 'Other'])}
            {inp('Blood group', patientForm.blood_group,
                 v => setP('blood_group', v), 'text',
                 ['A+','A-','B+','B-','AB+','AB-','O+','O-'])}
            {inp('Phone',       patientForm.phone,
                 v => setP('phone', v))}
            {inp('Address',     patientForm.address,
                 v => setP('address', v))}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-gray-300 mb-2">
              Guardian details
            </p>
            <p className="text-xs text-gray-500 mb-3">
              Your guardian will receive emergency alerts and can
              monitor your vitals.
            </p>
            {inp('Guardian full name', patientForm.guardian_name,
                 v => setP('guardian_name', v))}
            {inp('Guardian phone',     patientForm.guardian_phone,
                 v => setP('guardian_phone', v))}
            {inp('Guardian email',     patientForm.guardian_email,
                 v => setP('guardian_email', v), 'email')}
            {inp('Relation to you',    patientForm.guardian_relation,
                 v => setP('guardian_relation', v), 'text',
                 ['Son','Daughter','Spouse','Parent','Sibling','Other'])}
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-gray-300 mb-2">
              Doctor assignment
            </p>
            <p className="text-xs text-gray-500 mb-3">
              Optional — assign a doctor who will monitor your health data
              and receive emergency alerts.
            </p>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">
                Select your doctor
              </label>
              <select value={patientForm.doctor_id}
                      onChange={e => setP('doctor_id', e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700
                                 rounded-lg px-3 py-2 text-sm text-white
                                 focus:outline-none focus:border-blue-500">
                <option value="">No doctor (skip for now)</option>
                {doctors.map(d => (
                  <option key={d.id} value={d.id}>
                    Dr. {d.name} — {d.specialization}
                  </option>
                ))}
              </select>
            </div>
            {doctors.length === 0 && (
              <p className="text-xs text-yellow-500">
                No doctors registered yet. You can skip this step.
              </p>
            )}
          </div>
        )}

        <div className="flex gap-3 mt-6">
          {step < 3
            ? <button onClick={handleNext}
                      className="flex-1 bg-blue-600 hover:bg-blue-700
                                 text-white rounded-lg py-2.5 text-sm
                                 font-medium transition">
                Next
              </button>
            : <button onClick={submitPatient} disabled={loading}
                      className="flex-1 bg-green-600 hover:bg-green-700
                                 text-white rounded-lg py-2.5 text-sm
                                 font-medium transition disabled:opacity-50">
                {loading ? 'Registering...' : 'Complete registration'}
              </button>
          }
        </div>
      </div>
    </div>
  )
}