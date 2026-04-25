import { useEffect, useState } from 'react'
import { getRevenueReport, getOccupancyReport } from '../api/client'
import { format, subDays } from 'date-fns'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { Loader2 } from 'lucide-react'

export default function Reports() {
  const [revenue, setRevenue] = useState([])
  const [totalRevenue, setTotalRevenue] = useState(0)
  const [occupancy, setOccupancy] = useState(null)
  const [loading, setLoading] = useState(true)

  const endDate = format(new Date(), 'yyyy-MM-dd')
  const startDate = format(subDays(new Date(), 29), 'yyyy-MM-dd')

  useEffect(() => {
    async function load() {
      try {
        const [revRes, occRes] = await Promise.all([
          getRevenueReport({ from_date: startDate, to_date: endDate }),
          getOccupancyReport({ from_date: startDate, to_date: endDate }),
        ])
        setTotalRevenue(revRes.data?.total_revenue || 0)
        setRevenue(revRes.data?.daily || [])
        setOccupancy(occRes.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Reports</h1>

      {loading ? (
        <div className="text-center py-16 text-gray-400"><Loader2 size={28} className="animate-spin mx-auto" /></div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="card text-center">
              <p className="text-3xl font-bold text-gray-900">₹{totalRevenue.toLocaleString('en-IN')}</p>
              <p className="text-sm text-gray-400 mt-1">Revenue — last 30 days</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-gray-900">
                {occupancy?.occupancy_pct != null ? `${Math.round(occupancy.occupancy_pct)}%` : '—'}
              </p>
              <p className="text-sm text-gray-400 mt-1">Avg Occupancy — last 30 days</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-gray-900">{occupancy?.occupied_room_nights ?? '—'}</p>
              <p className="text-sm text-gray-400 mt-1">Room-nights sold</p>
            </div>
          </div>

          {/* Revenue chart */}
          <div className="card">
            <h2 className="font-semibold text-gray-700 mb-4">Daily Revenue (last 30 days)</h2>
            {revenue.length === 0 ? (
              <p className="text-center py-8 text-gray-400 text-sm">No revenue data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={revenue} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                    tickFormatter={d => format(new Date(d), 'd MMM')}
                    interval="preserveStartEnd"
                  />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                  <Tooltip
                    formatter={v => [`₹${v.toLocaleString('en-IN')}`, 'Revenue']}
                    labelFormatter={d => format(new Date(d), 'd MMM yyyy')}
                  />
                  <Bar dataKey="revenue" fill="#4f6ef7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}
    </div>
  )
}
