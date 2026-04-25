import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getConversations, invokeAgent } from '../api/client'
import { format } from 'date-fns'
import { Bot, Send, Loader2, ChevronRight } from 'lucide-react'

const AGENTS = [
  { id: 'front_desk', label: '🛎️  Front Desk',      hint: 'Check availability, book a room, check in/out a guest' },
  { id: 'accounting', label: '📊  Accounting',       hint: 'Invoice queries, payment status, overdue reminders'    },
  { id: 'inventory',  label: '📦  Inventory',        hint: 'Stock levels, room status, low-stock alerts'           },
  { id: 'sales',      label: '🤝  Sales',            hint: 'Wedding enquiries, event leads, follow-ups'            },
  { id: 'manager',    label: '👔  General Manager',  hint: 'Morning briefing, escalations, high-level overview'    },
]

export default function AgentChat() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState([])
  const [loadingConvos, setLoadingConvos] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState('front_desk')
  const [task, setTask] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    getConversations()
      .then(r => setConversations(r.data || []))
      .finally(() => setLoadingConvos(false))
  }, [])

  async function send() {
    if (!task.trim()) return
    setSending(true)
    try {
      const res = await invokeAgent(selectedAgent, task, { today: format(new Date(), 'yyyy-MM-dd') })
      navigate(`/agents/${res.data.conversation_id}`)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-2">Agent Chat</h1>
      <p className="text-sm text-gray-400 mb-6">Ask any hotel agent a question or give them a task.</p>

      {/* Compose */}
      <div className="card mb-6">
        <h2 className="font-semibold text-gray-700 mb-3">New Task</h2>

        {/* Agent selector */}
        <div className="grid grid-cols-5 gap-2 mb-4">
          {AGENTS.map(a => (
            <button
              key={a.id}
              onClick={() => setSelectedAgent(a.id)}
              className={`text-xs py-2 px-2 rounded-xl border-2 text-center leading-tight transition-colors ${
                selectedAgent === a.id
                  ? 'border-brand-500 bg-brand-50 text-brand-700 font-medium'
                  : 'border-gray-100 text-gray-500 hover:border-brand-200'
              }`}
            >
              {a.label}
            </button>
          ))}
        </div>

        <p className="text-xs text-gray-400 mb-3">
          💡 {AGENTS.find(a => a.id === selectedAgent)?.hint}
        </p>

        <div className="flex gap-2">
          <textarea
            className="input flex-1 resize-none h-20"
            placeholder="Type your task or question..."
            value={task}
            onChange={e => setTask(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) send() }}
          />
          <button
            onClick={send}
            disabled={sending || !task.trim()}
            className="btn-primary px-4 self-end"
          >
            {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
        <p className="text-[10px] text-gray-300 mt-1 text-right">⌘+Enter to send</p>
      </div>

      {/* Recent conversations */}
      <div className="card">
        <h2 className="font-semibold text-gray-700 mb-3">Recent Conversations</h2>
        {loadingConvos ? (
          <div className="text-center py-6 text-gray-400"><Loader2 size={20} className="animate-spin mx-auto" /></div>
        ) : conversations.length === 0 ? (
          <p className="text-center py-6 text-gray-400 text-sm">No conversations yet. Send your first task above!</p>
        ) : (
          <div className="space-y-1">
            {conversations.map(c => (
              <button
                key={c.conversation_id}
                onClick={() => navigate(`/agents/${c.conversation_id}`)}
                className="w-full text-left flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors"
              >
                <Bot size={18} className="text-brand-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{c.summary}</p>
                  <p className="text-xs text-gray-400">{c.agent_name?.replace('_', ' ')} · {format(new Date(c.created_at), 'd MMM, h:mm a')}</p>
                </div>
                <ChevronRight size={14} className="text-gray-300 shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
