import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { getBookings, checkIn, checkOut } from '../api/client'
import { format } from 'date-fns'
import { Plus, LogIn, LogOut, Loader2 } from 'lucide-react'

const STATUS_COLORS = {
  confirmed: 'bg-blue-100 text-blue-700',
  checked_in: 'bg-emerald-100 text-emerald-700',
  checked_out: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-red-100 text-red-600',
  no_show: 'bg-orange-100 text-orange-600',
}

export default function Bookings() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionId, setActionId] = useState(null)
  const today = format(new Date(), 'yyyy-MM-dd')

  async function load() {
    setLoading(true)
    try {
      const res = await getBookings({ limit: 100 })
      let data = res.data?.bookings || res.data || []
      const filter = params.get('filter')
      if (filter === 'checkin_today') data = data.filter(b => b.check_in === today && b.status === 'confirmed')
      if (filter === 'checkout_today') data = data.filter(b => b.check_out === today && b.status === 'checked_in')
      setBookings(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [params])

  async function handleCheckIn(id) {
    setActionId(id)
    try { await checkIn(id); await load() } finally { setActionId(null) }
  }
  async function handleCheckOut(id) {
    setActionId(id)
    try { await checkOut(id); await load() } finally { setActionId(null) }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Bookings</h1>
        <button onClick={() => navigate('/bookings/new')} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> New Booking
        </button>
      </div>

      <div className="card">
        {loading ? (
          <div className="text-center py-8 text-gray-400"><Loader2 size={24} className="animate-spin mx-auto" /></div>
        ) : bookings.length === 0 ? (
          <p className="text-center py-8 text-gray-400">No bookings found</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 text-xs border-b border-gray-100">
                <th className="pb-3 font-medium">Guest</th>
                <th className="pb-3 font-medium">Room</th>
                <th className="pb-3 font-medium">Check-in</th>
                <th className="pb-3 font-medium">Check-out</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {bookings.map(b => (
                <tr key={b.id} className="hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-900">{b.guest_name || '—'}</td>
                  <td className="py-3 text-gray-600">{b.room_number ? `Room ${b.room_number}` : '—'}</td>
                  <td className="py-3 text-gray-600">{format(new Date(b.check_in), 'd MMM yyyy')}</td>
                  <td className="py-3 text-gray-600">{format(new Date(b.check_out), 'd MMM yyyy')}</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[b.status] || 'bg-gray-100 text-gray-600'}`}>
                      {b.status?.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3">
                    <div className="flex gap-2">
                      {b.status === 'confirmed' && (
                        <button
                          onClick={() => handleCheckIn(b.id)}
                          disabled={actionId === b.id}
                          className="flex items-center gap-1 text-xs bg-emerald-50 text-emerald-600 hover:bg-emerald-100 px-2 py-1 rounded-lg transition-colors"
                        >
                          {actionId === b.id ? <Loader2 size={11} className="animate-spin" /> : <LogIn size={11} />}
                          Check In
                        </button>
                      )}
                      {b.status === 'checked_in' && (
                        <button
                          onClick={() => handleCheckOut(b.id)}
                          disabled={actionId === b.id}
                          className="flex items-center gap-1 text-xs bg-amber-50 text-amber-600 hover:bg-amber-100 px-2 py-1 rounded-lg transition-colors"
                        >
                          {actionId === b.id ? <Loader2 size={11} className="animate-spin" /> : <LogOut size={11} />}
                          Check Out
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
