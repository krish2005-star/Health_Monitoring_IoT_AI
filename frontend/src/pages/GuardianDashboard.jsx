import { useState, useEffect, useRef } from 'react'
import { getGuardianData } from '../api'
import BPMChart from '../components/BPMChart'
import AlertList from '../components/AlertList'
import VitalCard from '../components/VitalCard'
import HealthScore from '../components/HealthScore'

export default function GuardianDashboard() {
  const [data,   setData]   = useState(null)
  const pollRef = useRef(null)

  const fetchData = () =>
    getGuardianData().then(r => setData(r.data))

  useEffect(() => {
    fetchData()
    pollRef.current = setInterval(fetchData, 2000)
    return () => clearInterval(pollRef.current)
  }, [])

  if (!data) return (
    <p className="text-center text-gray-500 mt-20">Loading...</p>
  )

  const vitals = [...(data.vitals || [])].reverse()
  const alerts =   data.alerts || []
  const patient=   data.patient
  const latest =   vitals[vitals.length - 1]

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold">
          {patient.name}
        </h2>
        <p className="text-sm text-gray-400">
          Age {patient.age} · {patient.blood_group} · ID {patient.id}
        </p>
      </div>

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
        <VitalCard label="Alerts today"
          value={alerts.length} unit="total"
          status={alerts.length > 3 ? 'warn' : 'good'} />
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4">
          Heart rate — live
        </h3>
        <BPMChart data={vitals} />
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4">
          Alert history
        </h3>
        <AlertList alerts={alerts} />
      </div>

      <a href={`http://localhost:8000/report/${patient.id}`}
         target="_blank" rel="noreferrer"
         className="inline-block text-sm bg-gray-800 hover:bg-gray-700
                    border border-gray-700 px-4 py-2 rounded-lg
                    text-gray-300 transition">
        Download PDF report
      </a>
    </div>
  )
}