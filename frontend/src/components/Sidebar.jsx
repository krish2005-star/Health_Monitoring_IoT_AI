export default function Sidebar({ patients, selected, onSelect }) {
  return (
    <div className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-sm font-semibold text-white">HealthMonitor</h1>
        <p className="text-xs text-gray-500 mt-0.5">Live patient monitoring</p>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {patients.map(p => (
          <button
            key={p.id}
            onClick={() => onSelect(p)}
            className={`w-full text-left px-3 py-2.5 rounded-lg transition-all text-sm
              ${selected?.id === p.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'}`}
          >
            <p className="font-medium">{p.name}</p>
            <p className="text-xs opacity-70">Age {p.age} · {p.id}</p>
          </button>
        ))}
      </div>
    </div>
  )
}