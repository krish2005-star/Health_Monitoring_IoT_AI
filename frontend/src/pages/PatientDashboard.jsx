import { useState, useEffect, useRef } from 'react'
import { getMyVitals, getMyAlerts, getMyProfile } from '../api'
import BPMChart from '../components/BPMChart'
import SpO2Chart from '../components/SpO2Chart'
import AlertList from '../components/AlertList'
import VitalCard from '../components/VitalCard'
import HealthScore from '../components/HealthScore'

export default function PatientDashboard() {
  const [vitals,  setVitals]  = useState([])
  const [alerts,  setAlerts]  = useState([])
  const [profile, setProfile] = useState(null)
  const [tab,     setTab]     = useState('vitals')
  const pollRef = useRef(null)

  const fetchData = () => {
    getMyVitals().then(r => setVitals(r.data.reverse()))
    getMyAlerts().then(r => setAlerts(r.data))
  }

  useEffect(() => {
    getMyProfile().then(r => setProfile(r.data))
    fetchData()
    pollRef.current = setInterval(fetchData, 2000)
    return () => clearInterval(pollRef.current)
  }, [])

  const latest = vitals[vitals.length - 1]
  const pid    = profile?.patient?.id

  return (
    <div className="max-w-5xl mx-auto space-y-6">

      {/* Tab bar */}
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        {['vitals','alerts','profile'].map(t => (
          <button key={t} onClick={() => setTab(t)}
                  className={`px-4 py-1.5 rounded-lg text-sm capitalize
                    transition ${tab === t
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white'}`}>
            {t}
          </button>
        ))}
        {pid && (
          <a href={`http://localhost:8000/report/${pid}`}
             target="_blank" rel="noreferrer"
             className="ml-auto px-4 py-1.5 rounded-lg text-sm
                        bg-gray-800 hover:bg-gray-700 text-gray-300 transition">
            Download report
          </a>
        )}
      </div>

      {tab === 'vitals' && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <VitalCard label="Heart rate"
              value={latest?.bpm?.toFixed(0) ?? '--'} unit="BPM"
              status={latest?.bpm > 100 || latest?.bpm < 50
                      ? 'danger' : 'good'} />
            <VitalCard label="SpO2"
              value={latest?.spo2?.toFixed(1) ?? '--'} unit="%"
              status={latest?.spo2 < 94 ? 'danger'
                    : latest?.spo2 < 96 ? 'warn' : 'good'} />
            <HealthScore vitals={vitals} alerts={alerts} />
            <VitalCard label="Total alerts"
              value={alerts.length} unit="today"
              status={alerts.length > 3 ? 'warn' : 'good'} />
          </div>
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <h3 className="text-sm font-medium text-gray-300 mb-4">
              Heart rate
            </h3>
            <BPMChart data={vitals} />
          </div>
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <h3 className="text-sm font-medium text-gray-300 mb-4">
              SpO2
            </h3>
            <SpO2Chart data={vitals} />
          </div>
          {pid && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-medium text-gray-300 mb-4">
                SHAP — anomaly explanation
              </h3>
              <img src={`http://localhost:8000/shap/${pid}`}
                   alt="SHAP" className="w-full rounded-lg"
                   onError={e => e.target.style.display='none'} />
            </div>
          )}
        </>
      )}

      {tab === 'alerts' && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-4">
            Alert history
          </h3>
          <AlertList alerts={alerts} />
        </div>
      )}

      {tab === 'profile' && profile && (
        <div className="space-y-4">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <h3 className="text-sm font-medium text-gray-300 mb-4">
              My details
            </h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                ['Name',        profile.patient.name],
                ['Age',         profile.patient.age],
                ['Gender',      profile.patient.gender],
                ['Blood group', profile.patient.blood_group],
                ['Phone',       profile.patient.phone],
                ['Patient ID',  profile.patient.id],
              ].map(([k,v]) => (
                <div key={k} className="bg-gray-800 rounded-lg p-3">
                  <p className="text-gray-400 text-xs">{k}</p>
                  <p className="text-white font-medium mt-0.5">{v}</p>
                </div>
              ))}
            </div>
          </div>

          {profile.doctor && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-medium text-gray-300 mb-3">
                My doctor
              </h3>
              <p className="text-white font-medium">
                Dr. {profile.doctor.name}
              </p>
              <p className="text-gray-400 text-sm">
                {profile.doctor.specialization}
              </p>
              <p className="text-gray-400 text-sm">{profile.doctor.phone}</p>
            </div>
          )}

          {profile.guardians?.length > 0 && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-medium text-gray-300 mb-3">
                Guardians
              </h3>
              {profile.guardians.map(g => (
                <div key={g.id} className="bg-gray-800 rounded-lg p-3 mb-2">
                  <p className="text-white font-medium">{g.name}
                    <span className="text-xs text-gray-400 ml-2">
                      ({g.relation})
                    </span>
                  </p>
                  <p className="text-gray-400 text-sm">{g.phone}</p>
                  <p className="text-gray-400 text-sm">{g.email}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}