import { useEffect, useState } from 'react'
import { getRooms } from '../api/client'
import { BedDouble, Loader2 } from 'lucide-react'

const STATUS_STYLE = {
  available:    { bg: 'bg-emerald-50',  border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700' },
  occupied:     { bg: 'bg-rose-50',     border: 'border-rose-200',    badge: 'bg-rose-100 text-rose-700'       },
  maintenance:  { bg: 'bg-amber-50',    border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-700'     },
  cleaning:     { bg: 'bg-blue-50',     border: 'border-blue-200',    badge: 'bg-blue-100 text-blue-700'       },
}

export default function Rooms() {
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getRooms()
      .then(r => setRooms(r.data?.rooms || r.data || []))
      .finally(() => setLoading(false))
  }, [])

  const byFloor = rooms.reduce((acc, r) => {
    acc[r.floor] = acc[r.floor] || []
    acc[r.floor].push(r)
    return acc
  }, {})

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Rooms</h1>
        <div className="flex gap-3 text-xs text-gray-500">
          {Object.entries(STATUS_STYLE).map(([s, { badge }]) => (
            <span key={s} className={`px-2 py-0.5 rounded-full font-medium ${badge}`}>{s}</span>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400"><Loader2 size={28} className="animate-spin mx-auto" /></div>
      ) : (
        Object.entries(byFloor).sort(([a], [b]) => +a - +b).map(([floor, floorRooms]) => (
          <div key={floor} className="mb-6">
            <h2 className="text-sm font-semibold text-gray-400 mb-3">Floor {floor}</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {floorRooms.map(room => {
                const style = STATUS_STYLE[room.status] || STATUS_STYLE.available
                return (
                  <div
                    key={room.id}
                    className={`${style.bg} border ${style.border} rounded-xl p-4 cursor-default`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-bold text-gray-800">{room.room_number}</span>
                      <BedDouble size={16} className="text-gray-400" />
                    </div>
                    <p className="text-xs text-gray-500 capitalize mb-2">{room.type || room.room_type}</p>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${style.badge}`}>
                      {room.status}
                    </span>
                    <p className="text-xs text-gray-400 mt-2">₹{(room.base_rate || room.base_price)?.toLocaleString('en-IN')}/night</p>
                  </div>
                )
              })}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
