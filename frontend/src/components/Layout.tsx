import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ClipboardList,
  Users,
  PhoneCall,
  BarChart2,
  Download,
  Settings,
  PhoneOutgoing,
} from 'lucide-react'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/surveys', icon: ClipboardList, label: 'Surveys' },
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/calls', icon: PhoneCall, label: 'Calls' },
  { to: '/results', icon: BarChart2, label: 'Results' },
  { to: '/exports', icon: Download, label: 'Exports' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-gray-900 text-gray-100 flex flex-col">
        <div className="flex items-center gap-2 px-4 py-5 border-b border-gray-700">
          <PhoneOutgoing className="text-brand-500" size={22} />
          <span className="font-semibold text-lg tracking-tight">CATI Caller</span>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 space-y-0.5">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-none transition-colors ${
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-500">
          v0.1.0
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
