export default function AgentBubble({ message }) {
  const isUser = message.message_type === 'user_request'
  const isSystem = message.message_type === 'tool_result' || message.message_type === 'tool_call'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
        style={{ backgroundColor: message.bubble_color + '22', color: message.bubble_color }}
        title={message.sender}
      >
        {(message.sender || '?').slice(0, 2)}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-0.5`}>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span className="font-medium" style={{ color: message.bubble_color }}>{message.sender}</span>
          <span
            className="px-1.5 py-0.5 rounded-full text-[10px] font-medium"
            style={{ backgroundColor: message.bubble_color + '22', color: message.bubble_color }}
          >
            {message.type_label}
          </span>
        </div>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? 'bg-brand-500 text-white rounded-tr-sm'
              : isSystem
              ? 'bg-gray-100 text-gray-600 rounded-tl-sm font-mono text-xs'
              : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm'
          }`}
        >
          {message.content}
        </div>
        {message.duration_ms && (
          <span className="text-[10px] text-gray-300">{message.duration_ms}ms</span>
        )}
      </div>
    </div>
  )
}
