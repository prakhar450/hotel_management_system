import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, BedDouble, CalendarDays, FileText,
  Package, BarChart2, Bot, Users, Sparkles,
} from 'lucide-react'

const nav = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard'   },
  { to: '/rooms',     icon: BedDouble,       label: 'Rooms'       },
  { to: '/bookings',  icon: CalendarDays,    label: 'Bookings'    },
  { to: '/events',    icon: Sparkles,        label: 'Events'      },
  { to: '/invoices',  icon: FileText,        label: 'Invoices'    },
  { to: '/inventory', icon: Package,         label: 'Inventory'   },
  { to: '/reports',   icon: BarChart2,       label: 'Reports'     },
  { to: '/agents',    icon: Bot,             label: 'Agent Chat'  },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-100 flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-gray-100">
          <span className="text-lg font-bold text-brand-600">Hotel PMS</span>
          <p className="text-xs text-gray-400 mt-0.5">Management System</p>
        </div>
        <nav className="flex-1 py-3 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-brand-50 text-brand-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-gray-100 text-xs text-gray-400">
          Powered by Claude AI
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
