export default function HealthScore({ vitals, alerts }) {
  const compute = () => {
    if (!vitals.length) return 50
    const recent = vitals.slice(-20)
    const avgBpm  = recent.reduce((s, v) => s + v.bpm,  0) / recent.length
    const avgSpo2 = recent.reduce((s, v) => s + v.spo2, 0) / recent.length

    let score = 100
    // penalise abnormal BPM
    if (avgBpm > 100) score -= 20
    if (avgBpm < 55)  score -= 25
    if (avgBpm > 120) score -= 20
    // penalise low SpO2
    if (avgSpo2 < 96) score -= 10
    if (avgSpo2 < 94) score -= 20
    // penalise alerts
    score -= Math.min(alerts.length * 5, 30)
    return Math.max(0, Math.min(100, Math.round(score)))
  }

  const score  = compute()
  const color  = score > 75 ? 'text-green-400'
               : score > 50 ? 'text-yellow-400'
               : 'text-red-400'
  const label  = score > 75 ? 'Good' : score > 50 ? 'Fair' : 'Critical'

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-800/30 p-4">
      <p className="text-xs text-gray-400 mb-1">Health score</p>
      <p className={`text-3xl font-semibold ${color}`}>{score}</p>
      <p className={`text-xs mt-1 ${color}`}>{label}</p>
    </div>
  )
}