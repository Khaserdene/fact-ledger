import { NavLink, useLocation } from 'react-router-dom'
import { Network, FileText, Users, PlusCircle, TrendingUp } from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', label: 'Сүлжээ', Icon: Network, end: true },
  { to: '/macro', label: 'Макро', Icon: TrendingUp },
  { to: '/entities', label: 'Субъектүүд', Icon: Users },
  { to: '/sources', label: 'Эх сурвалж', Icon: FileText },
  { to: '/capture', label: 'Нэмэх', Icon: PlusCircle },
]

function Brand({ compact = false }) {
  return (
    <div className="px-3">
      <div className={`font-display font-bold text-text leading-tight ${compact ? 'text-base' : 'text-lg'}`}>
        <span className="text-accent">◉</span> FACT LEDGER
      </div>
      <div className="data-label uppercase mt-1 tracking-[0.25em]">
        ▸ v2.0
      </div>
    </div>
  );
}

function SideNav() {
  const linkCls = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-[8px] text-sm font-mono transition-all ${
      isActive
        ? 'bg-accent-dim text-accent border border-accent-line shadow-[0_0_16px_rgb(56_224_255/0.12)]'
        : 'text-dim border border-transparent hover:bg-surface-2 hover:text-text'
    }`
  return (
    <aside className="w-60 shrink-0 hidden md:flex flex-col gap-1 sticky top-0 h-screen py-6 px-3 border-r border-line bg-ink-900/40">
      <div className="mb-8">
        <Brand />
      </div>
      {NAV_ITEMS.map(({ to, label, Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={linkCls}>
          <Icon size={16} strokeWidth={1.75} />
          {label}
        </NavLink>
      ))}
      <div className="mt-auto px-3 data-label leading-relaxed">
        <span className="text-ok">●</span> SHA-256 VERIFIED
        <br />
        SYSTEM ONLINE
      </div>
    </aside>
  )
}

function MobileBottomNav() {
  const linkCls = ({ isActive }) =>
    `flex flex-col items-center gap-0.5 flex-1 py-1.5 text-[10px] font-mono transition-colors ${
      isActive ? 'text-accent' : 'text-faint'
    }`
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 glass-strong rounded-none border-x-0 border-b-0 flex items-stretch px-2 pt-1 pb-[max(0.35rem,env(safe-area-inset-bottom))]">
      {NAV_ITEMS.map(({ to, label, Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={linkCls}>
          <Icon size={19} strokeWidth={1.75} />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

function MobileTopBar() {
  return (
    <header className="md:hidden sticky top-0 z-40 glass-strong rounded-none border-x-0 border-t-0 flex items-center h-12 px-4">
      <div className="font-display font-bold text-sm text-text">
        <span className="text-accent">◉</span> FACT LEDGER
      </div>
      <span className="ml-auto data-label text-ok">● LIVE</span>
    </header>
  )
}

export default function AppShell({ children }) {
  const { pathname } = useLocation()
  const isFullBleed = pathname === '/' || pathname === '/macro' // graph болон macro хуудас өргөн харагдана
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <SideNav />
      <MobileTopBar />
      <main
        className={`flex-1 min-w-0 px-4 md:px-8 py-6 md:py-8 pb-24 md:pb-8 ${
          isFullBleed ? '' : 'max-w-4xl mx-auto w-full'
        }`}
      >
        {children}
      </main>
      <MobileBottomNav />
    </div>
  )
}
