import { useEffect, useState } from 'react'
import { getEvents, getEventSpaces, createEvent } from '../api/client'
import { format } from 'date-fns'
import { Plus, Loader2, Check, X } from 'lucide-react'

const EVENT_TYPES = ['wedding', 'corporate', 'birthday', 'conference', 'other']
const STATUS_COLORS = {
  tentative: 'bg-amber-100 text-amber-700',
  confirmed: 'bg-emerald-100 text-emerald-700',
  cancelled: 'bg-gray-100 text-gray-500',
  completed: 'bg-blue-100 text-blue-700',
}

export default function Events() {
  const [events, setEvents] = useState([])
  const [spaces, setSpaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    space_id: '',
    event_type: 'wedding',
    event_date: '',
    start_time: '10:00',
    end_time: '22:00',
    guest_count: 100,
    name: '',
  })

  async function load() {
    const [evRes, spRes] = await Promise.all([getEvents(), getEventSpaces()])
    setEvents(evRes.data?.events || evRes.data || [])
    setSpaces(spRes.data?.spaces || spRes.data || [])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function submit() {
    setSaving(true)
    try {
      await createEvent(form)
      setShowForm(false)
      await load()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Events</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> New Event
        </button>
      </div>

      {/* New Event Form */}
      {showForm && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">Book an Event Space</h2>
            <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Event Space *</label>
              <select className="input" value={form.space_id} onChange={e => setForm(p => ({ ...p, space_id: +e.target.value }))}>
                <option value="">Select space...</option>
                {spaces.map(s => <option key={s.id} value={s.id}>{s.name} (cap: {s.capacity})</option>)}
              </select>
            </div>
            <div>
              <label className="label">Event Type *</label>
              <select className="input" value={form.event_type} onChange={e => setForm(p => ({ ...p, event_type: e.target.value }))}>
                {EVENT_TYPES.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Event Name *</label>
              <input className="input" placeholder="e.g. Sharma Wedding" value={form.name}
                onChange={e => setForm(p => ({ ...p, name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Event Date *</label>
              <input type="date" className="input" value={form.event_date}
                onChange={e => setForm(p => ({ ...p, event_date: e.target.value }))} />
            </div>
            <div>
              <label className="label">Guest Count</label>
              <input type="number" className="input" value={form.guest_count}
                onChange={e => setForm(p => ({ ...p, guest_count: +e.target.value }))} />
            </div>
            <div>
              <label className="label">Start Time</label>
              <input type="time" className="input" value={form.start_time}
                onChange={e => setForm(p => ({ ...p, start_time: e.target.value }))} />
            </div>
            <div>
              <label className="label">End Time</label>
              <input type="time" className="input" value={form.end_time}
                onChange={e => setForm(p => ({ ...p, end_time: e.target.value }))} />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button onClick={() => setShowForm(false)} className="btn-secondary flex-1">Cancel</button>
            <button
              onClick={submit}
              disabled={saving || !form.space_id || !form.event_date || !form.name}
              className="btn-primary flex-1"
            >
              {saving ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Book Event'}
            </button>
          </div>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="text-center py-8 text-gray-400"><Loader2 size={24} className="animate-spin mx-auto" /></div>
        ) : events.length === 0 ? (
          <p className="text-center py-8 text-gray-400">No events booked yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 text-xs border-b border-gray-100">
                <th className="pb-3 font-medium">Event Name</th>
                <th className="pb-3 font-medium">Type</th>
                <th className="pb-3 font-medium">Space</th>
                <th className="pb-3 font-medium">Date</th>
                <th className="pb-3 font-medium">Guests</th>
                <th className="pb-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {events.map(ev => (
                <tr key={ev.id} className="hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-900">{ev.name}</td>
                  <td className="py-3 text-gray-600 capitalize">{ev.event_type}</td>
                  <td className="py-3 text-gray-600">{ev.space_name || '—'}</td>
                  <td className="py-3 text-gray-600">{format(new Date(ev.event_date), 'd MMM yyyy')}</td>
                  <td className="py-3 text-gray-600">{ev.guest_count}</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[ev.status] || 'bg-gray-100 text-gray-500'}`}>
                      {ev.status}
                    </span>
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
