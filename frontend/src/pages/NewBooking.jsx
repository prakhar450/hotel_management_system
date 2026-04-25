import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAvailableRooms, searchGuests, createGuest, createBooking, invokeAgent, getConversation } from '../api/client'
import { format, differenceInDays } from 'date-fns'
import { ChevronRight, ChevronLeft, Search, Plus, Loader2, Bot, Check } from 'lucide-react'
import AgentBubble from '../components/AgentBubble'

const STEPS = ['Dates', 'Pick Room', 'Guest', 'Confirm']

export default function NewBooking() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)

  // Form state
  const [checkIn, setCheckIn] = useState('')
  const [checkOut, setCheckOut] = useState('')
  const [rooms, setRooms] = useState([])
  const [selectedRoom, setSelectedRoom] = useState(null)
  const [guestQuery, setGuestQuery] = useState('')
  const [guestResults, setGuestResults] = useState([])
  const [selectedGuest, setSelectedGuest] = useState(null)
  const [newGuest, setNewGuest] = useState({ name: '', phone: '', email: '' })
  const [isNewGuest, setIsNewGuest] = useState(false)
  const [adults, setAdults] = useState(1)
  const [children, setChildren] = useState(0)
  const [specialRequests, setSpecialRequests] = useState('')

  const [loading, setLoading] = useState(false)
  const [agentThread, setAgentThread] = useState(null)
  const [bookingDone, setBookingDone] = useState(null)

  const nights = checkIn && checkOut ? differenceInDays(new Date(checkOut), new Date(checkIn)) : 0

  async function fetchRooms() {
    setLoading(true)
    try {
      const res = await getAvailableRooms(checkIn, checkOut)
      setRooms(res.data?.rooms || res.data || [])
      setStep(1)
    } finally {
      setLoading(false)
    }
  }

  async function searchGuestFn() {
    if (!guestQuery.trim()) return
    const res = await searchGuests(guestQuery)
    setGuestResults(res.data?.guests || res.data || [])
  }

  async function confirm() {
    setLoading(true)
    try {
      let guestId = selectedGuest?.id
      if (isNewGuest) {
        const res = await createGuest(newGuest)
        guestId = res.data.id
      }

      const bookingData = {
        room_id: selectedRoom.id,
        guest_id: guestId,
        check_in: checkIn,
        check_out: checkOut,
        adults,
        children,
        special_requests: specialRequests,
        created_by: 'front_desk',
      }
      const bookingRes = await createBooking(bookingData)
      setBookingDone(bookingRes.data)

      // Ask Front Desk agent to confirm & summarise
      const agentRes = await invokeAgent('front_desk',
        `A booking has just been created. Room: ${selectedRoom.room_number} (${selectedRoom.room_type}), Guest: ${isNewGuest ? newGuest.name : selectedGuest?.name}, Check-in: ${checkIn}, Check-out: ${checkOut}, ${nights} nights. Please confirm this and note any important things the guest should know.`,
        { today: format(new Date(), 'yyyy-MM-dd') }
      )
      const thread = await getConversation(agentRes.data.conversation_id)
      setAgentThread(thread.data)
    } finally {
      setLoading(false)
    }
  }

  if (bookingDone) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="card text-center mb-4">
          <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <Check size={28} className="text-emerald-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Booking Confirmed!</h2>
          <p className="text-gray-500 text-sm mt-1">Room {selectedRoom.room_number} · {nights} nights</p>
          <div className="flex gap-3 justify-center mt-4">
            <button onClick={() => navigate('/bookings')} className="btn-secondary">View All Bookings</button>
            <button onClick={() => navigate('/')} className="btn-primary">Back to Dashboard</button>
          </div>
        </div>

        {agentThread && (
          <div className="card">
            <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Bot size={16} className="text-brand-500" /> Front Desk Confirmation
            </h3>
            <div className="space-y-2">
              {agentThread.messages?.map(msg => <AgentBubble key={msg.id} message={msg} />)}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <button onClick={() => navigate('/bookings')} className="text-gray-400 hover:text-gray-600">
          <ChevronLeft size={20} />
        </button>
        <h1 className="text-xl font-bold text-gray-900">New Booking</h1>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
              i < step ? 'bg-emerald-500 text-white' : i === step ? 'bg-brand-500 text-white' : 'bg-gray-100 text-gray-400'
            }`}>
              {i < step ? <Check size={13} /> : i + 1}
            </div>
            <span className={`text-sm ${i === step ? 'font-medium text-gray-900' : 'text-gray-400'}`}>{s}</span>
            {i < STEPS.length - 1 && <ChevronRight size={14} className="text-gray-300 ml-1" />}
          </div>
        ))}
      </div>

      <div className="card">
        {/* Step 0: Dates */}
        {step === 0 && (
          <div className="space-y-4">
            <h2 className="font-semibold text-gray-800">When is the guest staying?</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Check-in</label>
                <input type="date" className="input" value={checkIn}
                  min={format(new Date(), 'yyyy-MM-dd')}
                  onChange={e => setCheckIn(e.target.value)} />
              </div>
              <div>
                <label className="label">Check-out</label>
                <input type="date" className="input" value={checkOut}
                  min={checkIn || format(new Date(), 'yyyy-MM-dd')}
                  onChange={e => setCheckOut(e.target.value)} />
              </div>
            </div>
            {nights > 0 && <p className="text-sm text-brand-600 font-medium">{nights} night{nights > 1 ? 's' : ''}</p>}
            <button
              className="btn-primary w-full mt-2"
              disabled={!checkIn || !checkOut || nights <= 0 || loading}
              onClick={fetchRooms}
            >
              {loading ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Search Available Rooms →'}
            </button>
          </div>
        )}

        {/* Step 1: Pick room */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="font-semibold text-gray-800">Choose a room</h2>
            {rooms.length === 0 ? (
              <p className="text-gray-500 text-sm">No rooms available for those dates.</p>
            ) : (
              <div className="space-y-2">
                {rooms.map(room => (
                  <button
                    key={room.id}
                    onClick={() => { setSelectedRoom(room); setStep(2) }}
                    className={`w-full text-left p-4 rounded-xl border-2 transition-colors ${
                      selectedRoom?.id === room.id
                        ? 'border-brand-500 bg-brand-50'
                        : 'border-gray-100 hover:border-brand-200'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-gray-900">Room {room.room_number}</p>
                        <p className="text-sm text-gray-500 capitalize">{room.type} · Floor {room.floor}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{room.amenities?.join(', ')}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-gray-900">₹{room.base_rate?.toLocaleString('en-IN')}</p>
                        <p className="text-xs text-gray-400">per night</p>
                        <p className="text-xs font-medium text-brand-600 mt-1">
                          ₹{(room.base_rate * nights).toLocaleString('en-IN')} total
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
            <button onClick={() => setStep(0)} className="btn-secondary text-sm">← Change Dates</button>
          </div>
        )}

        {/* Step 2: Guest */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="font-semibold text-gray-800">Who is the guest?</h2>
            {!isNewGuest ? (
              <>
                <div className="flex gap-2">
                  <input
                    className="input flex-1"
                    placeholder="Search by name or phone..."
                    value={guestQuery}
                    onChange={e => setGuestQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && searchGuestFn()}
                  />
                  <button onClick={searchGuestFn} className="btn-secondary px-3">
                    <Search size={16} />
                  </button>
                </div>
                <div className="space-y-2">
                  {guestResults.map(g => (
                    <button
                      key={g.id}
                      onClick={() => { setSelectedGuest(g); setStep(3) }}
                      className="w-full text-left p-3 rounded-xl border border-gray-100 hover:border-brand-200 hover:bg-brand-50 transition-colors"
                    >
                      <p className="font-medium text-gray-900">{g.name}</p>
                      <p className="text-xs text-gray-500">{g.phone} · {g.email}</p>
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => setIsNewGuest(true)}
                  className="flex items-center gap-1 text-sm text-brand-600 hover:underline"
                >
                  <Plus size={14} /> Add new guest
                </button>
              </>
            ) : (
              <>
                <div className="space-y-3">
                  <div>
                    <label className="label">Full Name *</label>
                    <input className="input" value={newGuest.name}
                      onChange={e => setNewGuest(p => ({ ...p, name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="label">Phone *</label>
                    <input className="input" value={newGuest.phone}
                      onChange={e => setNewGuest(p => ({ ...p, phone: e.target.value }))} />
                  </div>
                  <div>
                    <label className="label">Email</label>
                    <input className="input" value={newGuest.email}
                      onChange={e => setNewGuest(p => ({ ...p, email: e.target.value }))} />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setIsNewGuest(false)} className="btn-secondary flex-1">Back to search</button>
                  <button
                    onClick={() => setStep(3)}
                    disabled={!newGuest.name || !newGuest.phone}
                    className="btn-primary flex-1"
                  >
                    Continue →
                  </button>
                </div>
              </>
            )}
            <button onClick={() => setStep(1)} className="btn-secondary text-sm">← Change Room</button>
          </div>
        )}

        {/* Step 3: Confirm */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="font-semibold text-gray-800">Confirm Booking</h2>
            <div className="bg-gray-50 rounded-xl p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Room</span>
                <span className="font-medium">Room {selectedRoom.room_number} ({selectedRoom.room_type})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Guest</span>
                <span className="font-medium">{isNewGuest ? newGuest.name : selectedGuest?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Check-in</span>
                <span className="font-medium">{format(new Date(checkIn), 'd MMM yyyy')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Check-out</span>
                <span className="font-medium">{format(new Date(checkOut), 'd MMM yyyy')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Duration</span>
                <span className="font-medium">{nights} night{nights > 1 ? 's' : ''}</span>
              </div>
              <div className="border-t border-gray-200 pt-2 flex justify-between">
                <span className="text-gray-500">Total (before GST)</span>
                <span className="font-bold text-gray-900">₹{(selectedRoom.base_price * nights).toLocaleString('en-IN')}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Adults</label>
                <select className="input" value={adults} onChange={e => setAdults(+e.target.value)}>
                  {[1,2,3,4].map(n => <option key={n}>{n}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Children</label>
                <select className="input" value={children} onChange={e => setChildren(+e.target.value)}>
                  {[0,1,2,3].map(n => <option key={n}>{n}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="label">Special Requests</label>
              <textarea
                className="input resize-none h-20"
                placeholder="Early check-in, extra pillow, dietary needs..."
                value={specialRequests}
                onChange={e => setSpecialRequests(e.target.value)}
              />
            </div>

            <div className="flex gap-3">
              <button onClick={() => setStep(2)} className="btn-secondary flex-1">← Back</button>
              <button onClick={confirm} disabled={loading} className="btn-primary flex-1">
                {loading ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Confirm Booking ✓'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
