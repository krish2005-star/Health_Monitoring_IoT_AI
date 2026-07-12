import React, { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis,
         CartesianGrid, Tooltip, ReferenceLine,
         ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

export default function SpO2Chart({ data }) {
  const MAX_POINTS = 60
  const [chartData, setChartData] = useState([])

  useEffect(() => {
    const all = data.map((v, i) => ({
      time: format(new Date(v.timestamp), 'HH:mm:ss'),
      spo2: parseFloat(v.spo2?.toFixed(1)),
      idx: i
    }))
    setChartData(all.slice(-MAX_POINTS))
  }, [data])

  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="spo2grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="time" tick={{ fontSize:10, fill:'#6b7280' }}
               interval="preserveStartEnd" />
        <YAxis domain={[85,101]} tick={{ fontSize:10, fill:'#6b7280' }} />
        <Tooltip
          contentStyle={{ background:'#111827', border:'1px solid #374151',
                          borderRadius:8, fontSize:12 }}
        />
        <ReferenceLine y={94} stroke="#ef4444" strokeDasharray="4 4"
                       label={{ value:'Min safe', fontSize:10, fill:'#ef4444' }}/>
        <Area type="monotone" dataKey="spo2" stroke="#10b981"
              fill="url(#spo2grad)" strokeWidth={2} dot={false} name="SpO2 %" isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}