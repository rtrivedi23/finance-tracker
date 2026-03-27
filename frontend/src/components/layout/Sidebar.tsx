import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  ArrowLeftRight,
  Upload,
  BarChart2,
  Target,
  Wallet,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/transactions', icon: ArrowLeftRight, label: 'Transactions' },
  { to: '/upload', icon: Upload, label: 'Import' },
  { to: '/reports', icon: BarChart2, label: 'Reports' },
  { to: '/budgets', icon: Target, label: 'Budgets' },
]

export default function Sidebar() {
  return (
    <aside
      style={{ width: 240 }}
      className="h-screen flex-shrink-0 flex flex-col bg-[#080810] border-r border-white/[0.06] relative overflow-hidden"
    >
      {/* Top decorative glow blob */}
      <div
        className="absolute top-0 left-0 w-full h-48 opacity-20 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at 50% 0%, #7C3AED 0%, transparent 70%)',
        }}
      />

      {/* Logo */}
      <div className="px-6 py-7 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center shadow-glow-purple">
            <Wallet className="w-4 h-4 text-white" />
          </div>
          <span className="text-white font-bold text-lg tracking-tight">
            FinTrack
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-1 relative z-10">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-gradient-to-r from-purple-600/20 to-indigo-600/20 text-white border border-purple-500/20 rounded-xl'
                  : 'text-[#64748B] hover:text-[#F1F5F9] hover:bg-white/5 rounded-xl'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={clsx(
                    'w-4 h-4 flex-shrink-0 transition-colors',
                    isActive ? 'text-purple-400' : 'text-current'
                  )}
                />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom tag */}
      <div className="px-6 py-4 border-t border-white/[0.06] relative z-10">
        <p className="text-xs text-text-muted">v1.0 · Finance Tracker</p>
      </div>
    </aside>
  )
}
