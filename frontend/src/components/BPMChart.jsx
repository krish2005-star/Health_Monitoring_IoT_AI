import React, { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer
} from 'recharts'
import { format } from 'date-fns'

export default function BPMChart({ data }) {
  const MAX_POINTS = 60
  const [chartData, setChartData] = useState([])

  useEffect(() => {
    const all = data.map((v, i) => ({
      time: format(new Date(v.timestamp), 'HH:mm:ss'),
      bpm: Math.round(v.bpm),
      spo2: parseFloat(v.spo2?.toFixed(1)),
      idx: i
    }))
    setChartData(all.slice(-MAX_POINTS))
  }, [data])

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }}
               interval="preserveStartEnd" />
        <YAxis domain={[40, 160]} tick={{ fontSize: 10, fill: '#6b7280' }} />
        <Tooltip
          contentStyle={{ background:'#111827', border:'1px solid #374151',
                          borderRadius:8, fontSize:12 }}
          labelStyle={{ color:'#9ca3af' }}
        />
        <ReferenceLine y={100} stroke="#ef4444" strokeDasharray="4 4"
                       label={{ value:'Max', fontSize:10, fill:'#ef4444' }} />
        <ReferenceLine y={50}  stroke="#f59e0b" strokeDasharray="4 4"
                       label={{ value:'Min', fontSize:10, fill:'#f59e0b' }} />
        <Line type="monotone" dataKey="bpm" stroke="#3b82f6"
              dot={false} strokeWidth={2} name="BPM" isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}