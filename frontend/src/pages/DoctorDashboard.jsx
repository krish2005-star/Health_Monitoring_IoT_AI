import { useState, useEffect, useRef } from 'react'
import { getDoctorPatients, getDoctorPatientDetail } from '../api'
import BPMChart from '../components/BPMChart'
import AlertList from '../components/AlertList'
import VitalCard from '../components/VitalCard'
import HealthScore from '../components/HealthScore'

export default function DoctorDashboard() {
  const [patients, setPatients] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail,   setDetail]   = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    getDoctorPatients().then(r => {
      setPatients(r.data)
      if (r.data.length > 0) setSelected(r.data[0])
    })
  }, [])

  const fetchDetail = () => {
    if (!selected) return
    getDoctorPatientDetail(selected.id).then(r => setDetail(r.data))
  }

  useEffect(() => {
    clearInterval(pollRef.current)
    fetchDetail()
    pollRef.current = setInterval(fetchDetail, 2000)
    return () => clearInterval(pollRef.current)
  }, [selected])

  const vitals = detail ? [...detail.vitals].reverse() : []
  const alerts = detail?.alerts || []
  const latest = vitals[vitals.length - 1]

  return (
    <div className="flex gap-6 max-w-6xl mx-auto">

      {/* Patient list */}
      <div className="w-52 shrink-0">
        <h3 className="text-xs text-gray-500 uppercase tracking-wider
                       mb-3 font-medium">
          My patients
        </h3>
        <div className="space-y-1">
          {patients.map(p => (
            <button key={p.id} onClick={() => setSelected(p)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg
                      text-sm transition
                      ${selected?.id === p.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                      }`}>
              <p className="font-medium">{p.name}</p>
              <p className="text-xs opacity-70">Age {p.age} · {p.id}</p>
            </button>
          ))}
          {patients.length === 0 && (
            <p className="text-gray-600 text-sm px-3">No patients yet</p>
          )}
        </div>
      </div>

      {/* Detail */}
      <div className="flex-1 space-y-5">
        {detail && selected ? (
          <>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">{selected.name}</h2>
                <p className="text-sm text-gray-400">
                  Age {selected.age} · {selected.blood_group}
                  · ID {selected.id}
                </p>
              </div>
              <a href={`http://localhost:8000/report/${selected.id}`}
                 target="_blank" rel="noreferrer"
                 className="text-sm bg-gray-800 hover:bg-gray-700
                            border border-gray-700 px-4 py-2 rounded-lg
                            text-gray-300 transition">
                Download report
              </a>
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
              <VitalCard label="Alerts"
                value={alerts.length} unit="total"
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
                Alert history
              </h3>
              <AlertList alerts={alerts} />
            </div>
          </>
        ) : (
          <p className="text-gray-500 mt-20 text-center">
            Select a patient from the left
          </p>
        )}
      </div>
    </div>
  )
}