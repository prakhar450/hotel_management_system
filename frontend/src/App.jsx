import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Rooms from './pages/Rooms'
import Bookings from './pages/Bookings'
import NewBooking from './pages/NewBooking'
import Events from './pages/Events'
import Invoices from './pages/Invoices'
import InvoiceDetail from './pages/InvoiceDetail'
import Inventory from './pages/Inventory'
import Reports from './pages/Reports'
import AgentChat from './pages/AgentChat'
import ConversationView from './pages/ConversationView'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="rooms" element={<Rooms />} />
        <Route path="bookings" element={<Bookings />} />
        <Route path="bookings/new" element={<NewBooking />} />
        <Route path="events" element={<Events />} />
        <Route path="invoices" element={<Invoices />} />
        <Route path="invoices/:id" element={<InvoiceDetail />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="reports" element={<Reports />} />
        <Route path="agents" element={<AgentChat />} />
        <Route path="agents/:conversationId" element={<ConversationView />} />
      </Route>
    </Routes>
  )
}
