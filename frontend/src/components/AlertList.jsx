export default function AlertList({ alerts }) {
  if (!alerts.length)
    return <p className="text-gray-500 text-sm">No alerts yet.</p>

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {alerts.map(a => (
        <div key={a.id ?? a.timestamp}
             className="flex items-start gap-3 bg-gray-800/50
                        border border-gray-700/50 rounded-lg px-4 py-3">
          <span className="w-2 h-2 mt-1.5 rounded-full bg-red-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-red-300">{a.alert_type}</p>
            <p className="text-xs text-gray-400 mt-0.5 break-words">{a.shap_reason}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-xs text-gray-500">
              {new Date(a.timestamp).toLocaleTimeString()}
            </p>
            <p className="text-xs text-orange-400 mt-0.5">
              Score: {a.anomaly_score?.toFixed(2)}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}