const colors = {
  good:   'text-green-400  bg-green-900/20  border-green-800/40',
  warn:   'text-yellow-400 bg-yellow-900/20 border-yellow-800/40',
  danger: 'text-red-400    bg-red-900/20    border-red-800/40',
}

export default function VitalCard({ label, value, unit, status = 'good' }) {
  return (
    <div className={`rounded-xl border p-4 ${colors[status]}`}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-3xl font-semibold">{value}</p>
      <p className="text-xs mt-1 opacity-60">{unit}</p>
    </div>
  )
}