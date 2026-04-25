import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getInvoice, recordPayment, invokeAgent, getConversation } from '../api/client'
import { format } from 'date-fns'
import { ChevronLeft, Bot, Loader2, Check } from 'lucide-react'
import AgentBubble from '../components/AgentBubble'

const PAYMENT_MODES = ['cash', 'card', 'upi', 'bank_transfer', 'cheque']

export default function InvoiceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [invoice, setInvoice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [payAmount, setPayAmount] = useState('')
  const [payMode, setPayMode] = useState('upi')
  const [paying, setPaying] = useState(false)
  const [agentThread, setAgentThread] = useState(null)

  async function load() {
    setLoading(true)
    try {
      const res = await getInvoice(id)
      setInvoice(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  async function handlePayment() {
    if (!payAmount || +payAmount <= 0) return
    setPaying(true)
    try {
      await recordPayment(id, { amount: +payAmount, method: payMode })
      await load()
      setPayAmount('')

      const agentRes = await invokeAgent('accounting',
        `Payment of ₹${payAmount} received via ${payMode} for invoice ${invoice.invoice_number}. Confirm this is recorded and update the guest.`,
        {}
      )
      const thread = await getConversation(agentRes.data.conversation_id)
      setAgentThread(thread.data)
    } finally {
      setPaying(false)
    }
  }

  if (loading) return <div className="p-6 text-center"><Loader2 className="animate-spin mx-auto text-gray-400" /></div>
  if (!invoice) return <div className="p-6 text-center text-gray-400">Invoice not found</div>

  const balance = invoice.total_amount - (invoice.paid_amount || 0)

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <button onClick={() => navigate('/invoices')} className="text-gray-400 hover:text-gray-600">
          <ChevronLeft size={20} />
        </button>
        <h1 className="text-xl font-bold text-gray-900">{invoice.invoice_number}</h1>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ml-1 ${
          invoice.status === 'paid' ? 'bg-emerald-100 text-emerald-700'
          : invoice.status === 'pending' ? 'bg-amber-100 text-amber-700'
          : 'bg-gray-100 text-gray-600'
        }`}>{invoice.status}</span>
      </div>

      <div className="card mb-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-400 text-xs">Guest</p>
            <p className="font-medium">{invoice.guest_name || '—'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">Issued</p>
            <p className="font-medium">{invoice.issued_date ? format(new Date(invoice.issued_date), 'd MMM yyyy') : '—'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">Due Date</p>
            <p className="font-medium">{invoice.due_date ? format(new Date(invoice.due_date), 'd MMM yyyy') : '—'}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">GST</p>
            <p className="font-medium">₹{invoice.tax_amount?.toLocaleString('en-IN')}</p>
          </div>
        </div>

        <div className="border-t border-gray-100 mt-4 pt-4 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Subtotal</span>
            <span>₹{invoice.subtotal?.toLocaleString('en-IN')}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">GST (18%)</span>
            <span>₹{invoice.tax_amount?.toLocaleString('en-IN')}</span>
          </div>
          <div className="flex justify-between font-bold text-base border-t border-gray-100 pt-2 mt-2">
            <span>Total</span>
            <span>₹{invoice.total_amount?.toLocaleString('en-IN')}</span>
          </div>
          <div className="flex justify-between text-emerald-600">
            <span>Paid</span>
            <span>₹{invoice.paid_amount?.toLocaleString('en-IN')}</span>
          </div>
          {balance > 0 && (
            <div className="flex justify-between font-semibold text-rose-600">
              <span>Balance Due</span>
              <span>₹{balance.toLocaleString('en-IN')}</span>
            </div>
          )}
        </div>
      </div>

      {/* Payments */}
      {invoice.payments?.length > 0 && (
        <div className="card mb-4">
          <h3 className="font-semibold text-gray-700 mb-3 text-sm">Payment History</h3>
          <div className="space-y-2">
            {invoice.payments.map(p => (
              <div key={p.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500" />
                  <span className="capitalize text-gray-600">{p.payment_mode}</span>
                  <span className="text-gray-400 text-xs">{format(new Date(p.payment_date), 'd MMM yyyy')}</span>
                </div>
                <span className="font-medium text-emerald-600">₹{p.amount?.toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Record payment */}
      {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
        <div className="card mb-4">
          <h3 className="font-semibold text-gray-700 mb-3 text-sm">Record Payment</h3>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="label text-xs">Amount (₹)</label>
              <input
                type="number"
                className="input"
                placeholder={balance.toString()}
                value={payAmount}
                onChange={e => setPayAmount(e.target.value)}
              />
            </div>
            <div className="w-36">
              <label className="label text-xs">Mode</label>
              <select className="input" value={payMode} onChange={e => setPayMode(e.target.value)}>
                {PAYMENT_MODES.map(m => <option key={m} value={m}>{m.replace('_', ' ')}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={handlePayment}
            disabled={paying || !payAmount}
            className="btn-primary w-full mt-3"
          >
            {paying ? <Loader2 size={16} className="animate-spin mx-auto" /> : 'Record Payment'}
          </button>
        </div>
      )}

      {/* Agent confirmation */}
      {agentThread && (
        <div className="card">
          <h3 className="font-semibold text-gray-700 mb-3 text-sm flex items-center gap-2">
            <Bot size={15} className="text-brand-500" /> Accounting Confirmation
          </h3>
          <div className="space-y-2">
            {agentThread.messages?.map(msg => <AgentBubble key={msg.id} message={msg} />)}
          </div>
        </div>
      )}
    </div>
  )
}
