import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getConversation } from '../api/client'
import { ChevronLeft, Loader2 } from 'lucide-react'
import AgentBubble from '../components/AgentBubble'

export default function ConversationView() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const [thread, setThread] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getConversation(conversationId)
      .then(r => setThread(r.data))
      .finally(() => setLoading(false))
  }, [conversationId])

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <button onClick={() => navigate('/agents')} className="text-gray-400 hover:text-gray-600">
          <ChevronLeft size={20} />
        </button>
        <h1 className="text-xl font-bold text-gray-900">Conversation</h1>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">
          <Loader2 size={28} className="animate-spin mx-auto mb-2" />
          <p className="text-sm">Loading conversation...</p>
        </div>
      ) : !thread ? (
        <div className="card text-center py-8 text-gray-400">Conversation not found</div>
      ) : (
        <div className="space-y-3">
          {thread.messages?.length === 0 ? (
            <p className="text-center text-gray-400 text-sm">No messages in this conversation</p>
          ) : (
            thread.messages.map(msg => <AgentBubble key={msg.id} message={msg} />)
          )}
        </div>
      )}
    </div>
  )
}
