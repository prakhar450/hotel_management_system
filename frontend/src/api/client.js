import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

// Rooms & availability
export const getRooms = () => api.get('/inventory/rooms')
export const getAvailableRooms = (checkIn, checkOut) =>
  api.get('/availability/rooms', { params: { check_in: checkIn, check_out: checkOut } })

// Guests
export const searchGuests = (q) => api.get('/guests', { params: { search: q, limit: 20 } })
export const createGuest = (data) => api.post('/guests', data)
export const getGuest = (id) => api.get(`/guests/${id}`)

// Bookings
export const getBookings = (params) => api.get('/bookings', { params })
export const createBooking = (data) => api.post('/bookings', data)
export const getBooking = (id) => api.get(`/bookings/${id}`)
export const checkIn = (id) => api.put(`/bookings/${id}/checkin`)
export const checkOut = (id) => api.put(`/bookings/${id}/checkout`)
export const cancelBooking = (id) => api.put(`/bookings/${id}/cancel`)

// Events
export const getEvents = (params) => api.get('/events', { params })
export const createEvent = (data) => api.post('/events', data)
export const getEventSpaces = () => api.get('/events/spaces')

// Invoices & payments
export const getInvoices = (params) => api.get('/invoices', { params })
export const getInvoice = (id) => api.get(`/invoices/${id}`)
export const recordPayment = (invoiceId, data) =>
  api.post('/payments', { ...data, invoice_id: invoiceId })

// Inventory
export const getInventory = () => api.get('/inventory/consumables')
export const updateInventory = (id, data) => api.put(`/inventory/items/${id}`, data)

// Reports
export const getOccupancyReport = (params) => api.get('/reports/occupancy', { params })
export const getRevenueReport = (params) => api.get('/reports/revenue', { params })

// Agents
export const invokeAgent = (agentName, task, context = {}) =>
  api.post('/agent/invoke', { agent_name: agentName, task, context })
export const getConversations = () => api.get('/agent/conversations')
export const getConversation = (id) => api.get(`/agent/conversations/${id}`)
export const getAgentLogs = (params) => api.get('/agent/logs', { params })

export default api
