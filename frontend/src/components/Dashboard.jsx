import { useState, useEffect, useRef, useCallback } from 'react'
import SpO2Chart from './SpO2Chart'
import { getVitals, getAlerts } from '../api'
import VitalCard from './VitalCard'
import BPMChart from './BPMChart'
import AlertList from './AlertList'
import HealthScore from './HealthScore'

export default function Dashboard({ patient }) {
  const [vitals,  setVitals]  = useState([])
  const [alerts,  setAlerts]  = useState([])
  const pollRef = useRef(null)
  const [activityState, setActivityState] = useState('--')

  const fetchData = useCallback(() => {
  getVitals(patient.id).then(r => {
    const data = r.data.reverse()
    setVitals(data)

    if (data.length > 0) {
      const bpm = data[data.length - 1].bpm

      if (bpm < 60)       setActivityState('Sleeping')
      else if (bpm < 75)  setActivityState('Resting')
      else if (bpm < 100) setActivityState('Active')
      else                setActivityState('Exercising')
    }
  })

  getAlerts(patient.id).then(r => setAlerts(r.data))
}, [patient.id])

  useEffect(() => {
    fetchData()
    pollRef.current = setInterval(fetchData, 2000) // poll every 2s
    return () => clearInterval(pollRef.current)
  }, [fetchData])

  const latest = vitals[vitals.length - 1]
  const activeAlerts = alerts.filter(a => !a.resolved)

  return (
    <div className="space-y-6 max-w-6xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{patient.name}</h2>
          <p className="text-sm text-gray-400">Age {patient.age} · ID {patient.id}</p>
        </div>
        {activeAlerts.length > 0 && (
          <div className="flex items-center gap-2 bg-red-900/40 border border-red-500/50
                          text-red-400 px-4 py-2 rounded-lg text-sm animate-pulse">
            <span className="w-2 h-2 bg-red-400 rounded-full"></span>
            {activeAlerts.length} active alert{activeAlerts.length > 1 ? 's' : ''}
          </div>
        )}
        <a href={`http://localhost:8000/report/${patient.id}`}
            target="_blank" rel="noreferrer"
            className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 px-4 py-2 rounded-lg transition-all text-gray-300">
                Download report
        </a>
      </div>

      {/* Vital cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <VitalCard
          label="Heart rate"
          value={latest?.bpm?.toFixed(0) ?? '--'}
          unit="BPM"
          status={latest?.bpm > 100 || latest?.bpm < 50 ? 'danger' : 'good'}
        />
        <VitalCard
          label="SpO2"
          value={latest?.spo2?.toFixed(1) ?? '--'}
          unit="%"
          status={latest?.spo2 < 94 ? 'danger' : latest?.spo2 < 96 ? 'warn' : 'good'}
        />
        <HealthScore vitals={vitals} alerts={alerts} />
        <VitalCard
          label="Total alerts"
          value={alerts.length}
          unit="today"
          status={alerts.length > 5 ? 'warn' : 'good'}
        />
        <VitalCard
          label="Activity"
          value={activityState}
          unit="current state"
          status="good"
        />
        {/* add this after the Total alerts VitalCard */}
        <VitalCard
          label="Fall detected"
          value={vitals.some(v => v.fall_detected) ? 'YES' : 'No'}
          unit="last 100 readings"
          status={vitals.some(v => v.fall_detected) ? 'danger' : 'good'}
        />
      </div>

      {/* BPM Chart */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4">
          Heart rate — last 100 readings
        </h3>
        <BPMChart data={vitals} />
      </div>

      {/* SpO2 Chart */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <h3 className="text-sm font-medium text-gray-300 mb-4">
                SpO2 — blood oxygen level
            </h3>
            <SpO2Chart data={vitals} />
        </div>

        {/* SHAP Panel */}
<div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
  <h3 className="text-sm font-medium text-gray-300 mb-4">
    SHAP — why was the last alert triggered?
  </h3>
  <img
    src={`http://localhost:8000/shap/${patient.id}?t=${Date.now()}`}
    alt="SHAP explanation"
    className="w-full rounded-lg"
    onError={e => e.target.style.display='none'}
  />
</div>

      {/* Alerts */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4">Alert history</h3>
        <AlertList alerts={alerts} />
      </div>

    </div>
    
  )
}