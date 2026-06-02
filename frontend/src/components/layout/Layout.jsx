import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth.jsx'
import { MessageCircle, CalendarDays, LayoutDashboard, LogOut, Salad } from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { to: '/app/chat',      icon: MessageCircle,   label: 'Ask NutriGuide' },
  { to: '/app/meal-plan', icon: CalendarDays,    label: 'Meal Planner'   },
  { to: '/app/dashboard', icon: LayoutDashboard, label: 'My Profile'     },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const handleLogout = () => { logout(); navigate('/') }

  return (
    <div className="flex h-screen overflow-hidden bg-cream">
      <aside className="w-64 shrink-0 glass border-r border-warmGray/20 flex flex-col py-8 px-5 gap-8">
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 bg-terra rounded-2xl flex items-center justify-center shadow-warm">
            <Salad size={20} className="text-cream" />
          </div>
          <div>
            <p className="font-display text-lg leading-tight text-forest">NutriGuide</p>
            <p className="text-xs text-warmGray">Clinical Nutrition AI</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) => clsx(
              'flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all duration-200',
              isActive
                ? 'bg-terra text-cream shadow-warm'
                : 'text-warmGray-dark hover:bg-terra/10 hover:text-terra'
            )}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-warmGray/20 pt-4">
          <div className="flex items-center gap-3 px-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-terra/20 flex items-center justify-center text-terra font-display text-sm font-semibold">
              {user?.full_name?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-forest truncate">{user?.full_name}</p>
              <p className="text-xs text-warmGray capitalize">{user?.role}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="flex items-center gap-2 px-4 py-2 w-full rounded-xl text-sm text-warmGray hover:text-terra hover:bg-terra/8 transition-all">
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
