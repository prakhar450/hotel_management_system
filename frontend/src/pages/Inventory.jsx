import { useEffect, useState } from 'react'
import { getInventory, updateInventory } from '../api/client'
import { AlertTriangle, Package, Loader2, Check } from 'lucide-react'

export default function Inventory() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)
  const [editQty, setEditQty] = useState('')
  const [saving, setSaving] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const res = await getInventory()
      setItems(res.data?.items || res.data || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function saveQty(item) {
    setSaving(true)
    try {
      await updateInventory(item.id, { quantity: +editQty })
      setEditing(null)
      await load()
    } finally {
      setSaving(false)
    }
  }

  const lowStock = items.filter(i => i.available_quantity <= i.low_stock_threshold)
  const byCategory = items.reduce((acc, i) => {
    acc[i.category] = acc[i.category] || []
    acc[i.category].push(i)
    return acc
  }, {})

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Inventory</h1>

      {/* Low stock alerts */}
      {lowStock.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
          <h2 className="flex items-center gap-2 font-semibold text-amber-800 mb-2">
            <AlertTriangle size={16} /> {lowStock.length} item{lowStock.length > 1 ? 's' : ''} running low
          </h2>
          <div className="flex flex-wrap gap-2">
            {lowStock.map(i => (
              <span key={i.id} className="bg-amber-100 text-amber-700 text-xs font-medium px-2 py-1 rounded-full">
                {i.name} — {i.available_quantity} {i.unit} left
              </span>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400"><Loader2 size={28} className="animate-spin mx-auto" /></div>
      ) : (
        Object.entries(byCategory).map(([category, categoryItems]) => (
          <div key={category} className="card mb-4">
            <h2 className="font-semibold text-gray-700 mb-3 flex items-center gap-2 capitalize">
              <Package size={16} className="text-gray-400" /> {category}
            </h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 text-xs border-b border-gray-100">
                  <th className="pb-2 font-medium">Item</th>
                  <th className="pb-2 font-medium">In Stock</th>
                  <th className="pb-2 font-medium">Reorder At</th>
                  <th className="pb-2 font-medium">Unit</th>
                  <th className="pb-2 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {categoryItems.map(item => {
                  const isLow = item.available_quantity <= item.low_stock_threshold
                  return (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="py-2.5 font-medium text-gray-900">{item.name}</td>
                      <td className="py-2.5">
                        {editing === item.id ? (
                          <input
                            type="number"
                            className="input w-20 py-1 text-xs"
                            value={editQty}
                            onChange={e => setEditQty(e.target.value)}
                            autoFocus
                          />
                        ) : (
                          <span className={`font-semibold ${isLow ? 'text-rose-600' : 'text-gray-800'}`}>
                            {item.available_quantity}
                            {isLow && <AlertTriangle size={12} className="inline ml-1 text-rose-400" />}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 text-gray-500">{item.low_stock_threshold}</td>
                      <td className="py-2.5 text-gray-500">{item.unit}</td>
                      <td className="py-2.5">
                        {editing === item.id ? (
                          <div className="flex gap-1">
                            <button
                              onClick={() => saveQty(item)}
                              disabled={saving}
                              className="text-xs bg-emerald-50 text-emerald-600 hover:bg-emerald-100 px-2 py-1 rounded-lg"
                            >
                              {saving ? <Loader2 size={10} className="animate-spin" /> : <Check size={12} />}
                            </button>
                            <button
                              onClick={() => setEditing(null)}
                              className="text-xs bg-gray-50 text-gray-500 hover:bg-gray-100 px-2 py-1 rounded-lg"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => { setEditing(item.id); setEditQty(item.available_quantity) }}
                            className="text-xs text-brand-600 hover:underline"
                          >
                            Update
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  )
}
