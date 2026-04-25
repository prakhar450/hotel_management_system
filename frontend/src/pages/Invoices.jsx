import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { getInvoices } from '../api/client'
import { format } from 'date-fns'
import { Loader2 } from 'lucide-react'

const STATUS_COLORS = {
  pending: 'bg-amber-100 text-amber-700',
  paid: 'bg-emerald-100 text-emerald-700',
  partial: 'bg-blue-100 text-blue-700',
  cancelled: 'bg-gray-100 text-gray-500',
}

export default function Invoices() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const status = params.get('status')
    getInvoices(status ? { status } : {})
      .then(r => setInvoices(r.data?.invoices || r.data || []))
      .finally(() => setLoading(false))
  }, [params])

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Invoices</h1>
        <div className="flex gap-2 text-xs">
          {['all', 'pending', 'paid', 'partial'].map(s => (
            <button
              key={s}
              onClick={() => navigate(s === 'all' ? '/invoices' : `/invoices?status=${s}`)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                (params.get('status') || 'all') === s
                  ? 'bg-brand-500 text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="text-center py-8 text-gray-400"><Loader2 size={24} className="animate-spin mx-auto" /></div>
        ) : invoices.length === 0 ? (
          <p className="text-center py-8 text-gray-400">No invoices found</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 text-xs border-b border-gray-100">
                <th className="pb-3 font-medium">Invoice #</th>
                <th className="pb-3 font-medium">Guest</th>
                <th className="pb-3 font-medium">Total</th>
                <th className="pb-3 font-medium">Paid</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Date</th>
                <th className="pb-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {invoices.map(inv => (
                <tr key={inv.id} className="hover:bg-gray-50">
                  <td className="py-3 font-mono text-xs text-gray-700">{inv.invoice_number}</td>
                  <td className="py-3 font-medium text-gray-900">{inv.guest_name || '—'}</td>
                  <td className="py-3 text-gray-700">₹{inv.total_amount?.toLocaleString('en-IN')}</td>
                  <td className="py-3 text-gray-700">₹{inv.paid_amount?.toLocaleString('en-IN')}</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[inv.status] || 'bg-gray-100 text-gray-600'}`}>
                      {inv.status}
                    </span>
                  </td>
                  <td className="py-3 text-gray-500">
                    {inv.issued_date ? format(new Date(inv.issued_date), 'd MMM yyyy') : '—'}
                  </td>
                  <td className="py-3">
                    <button
                      onClick={() => navigate(`/invoices/${inv.id}`)}
                      className="text-xs text-brand-600 hover:underline"
                    >
                      View →
                    </button>
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
