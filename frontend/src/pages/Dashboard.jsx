import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getBookings, getInvoices, getInventory, invokeAgent, getConversation } from '../api/client'
import { format } from 'date-fns'
import {
  BedDouble, FileText, Package, AlertTriangle,
  Plus, LogIn, LogOut, Bot, Loader2,
} from 'lucide-react'
import AgentBubble from '../components/AgentBubble'

export default function Dashboard() {
  const navigate = useNavigate()
  const today = format(new Date(), 'yyyy-MM-dd')

  const [stats, setStats] = useState({ checkIns: 0, checkOuts: 0, unpaidInvoices: 0, lowStock: 0 })
  const [loading, setLoading] = useState(true)
  const [briefing, setBriefing] = useState(null)
  const [briefingLoading, setBriefingLoading] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const [bookingsRes, invoicesRes, inventoryRes] = await Promise.all([
          getBookings({ limit: 200 }),
          getInvoices({ status: 'pending', limit: 200 }),
          getInventory(),
        ])
        const bookings = bookingsRes.data?.bookings || bookingsRes.data || []
        const invoices = invoicesRes.data?.invoices || invoicesRes.data || []
        const items = inventoryRes.data?.items || inventoryRes.data || []

        setStats({
          checkIns: bookings.filter(b => b.check_in === today && b.status === 'confirmed').length,
          checkOuts: bookings.filter(b => b.check_out === today && b.status === 'checked_in').length,
          unpaidInvoices: invoices.length,
          lowStock: items.filter(i => i.quantity <= i.reorder_level).length,
        })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [today])

  async function getMorningBriefing() {
    setBriefingLoading(true)
    try {
      const res = await invokeAgent('manager', 'Give me a quick morning briefing: any check-ins today, pending payments, or inventory issues I should know about.', { today })
      const thread = await getConversation(res.data.conversation_id)
      setBriefing(thread.data)
    } finally {
      setBriefingLoading(false)
    }
  }

  const quickActions = [
    { label: 'New Booking', icon: Plus, color: 'bg-brand-500 text-white', action: () => navigate('/bookings/new') },
    { label: 'Check-ins Today', icon: LogIn, color: 'bg-emerald-500 text-white', action: () => navigate('/bookings?filter=checkin_today') },
    { label: 'Check-outs Today', icon: LogOut, color: 'bg-amber-500 text-white', action: () => navigate('/bookings?filter=checkout_today') },
    { label: 'Pending Invoices', icon: FileText, color: 'bg-rose-500 text-white', action: () => navigate('/invoices?status=pending') },
  ]

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Good morning 👋</h1>
          <p className="text-gray-500 text-sm mt-0.5">{format(new Date(), 'EEEE, d MMMM yyyy')}</p>
        </div>
        <button
          onClick={getMorningBriefing}
          disabled={briefingLoading}
          className="flex items-center gap-2 btn-primary"
        >
          {briefingLoading ? <Loader2 size={16} className="animate-spin" /> : <Bot size={16} />}
          Morning Briefing
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Check-ins Today", value: stats.checkIns, icon: LogIn, color: 'text-emerald-500' },
          { label: "Check-outs Today", value: stats.checkOuts, icon: LogOut, color: 'text-amber-500' },
          { label: "Unpaid Invoices", value: stats.unpaidInvoices, icon: FileText, color: 'text-rose-500' },
          { label: "Low Stock Items", value: stats.lowStock, icon: AlertTriangle, color: 'text-orange-500' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className={`${color} bg-opacity-10 p-2.5 rounded-lg`}>
              <Icon size={20} className={color} />
            </div>
            <div>
              <p className="text-2xl font-bold">{loading ? '—' : value}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="card mb-6">
        <h2 className="font-semibold text-gray-700 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-4 gap-3">
          {quickActions.map(({ label, icon: Icon, color, action }) => (
            <button
              key={label}
              onClick={action}
              className={`${color} flex flex-col items-center gap-2 py-4 px-3 rounded-xl font-medium text-sm transition-opacity hover:opacity-90`}
            >
              <Icon size={22} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Agent briefing thread */}
      {briefing && (
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Bot size={18} className="text-brand-500" /> Morning Briefing
          </h2>
          <div className="space-y-2">
            {briefing.messages?.map(msg => (
              <AgentBubble key={msg.id} message={msg} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
