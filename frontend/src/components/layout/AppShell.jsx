import { NavLink, useLocation } from 'react-router-dom'
import { Network, FolderGit2, FileText, TrendingUp, Radio, PlusCircle, Search, LogOut } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'

const NAV_ITEMS = [
  { to: '/',        label: 'Сүлжээ',     Icon: Network,     end: true,  desc: 'Knowledge Graph & Субъектүүд' },
  { to: '/cases',   label: 'Мөрдлөг',    Icon: FolderGit2,  end: false, desc: 'Хэргүүд & Огтлолцол' },
  { to: '/sources', label: 'Эх сурвалж', Icon: FileText,   end: false, desc: 'Нийтлэлүүд & Баримт' },
  { to: '/macro',   label: 'Макро',      Icon: TrendingUp,  end: false, desc: 'Төсөв, Валют, Инфляц' },
  { to: '/media',   label: 'Радар',      Icon: Radio,       end: false, desc: 'Хэвлэлийн Мониторинг' },
  { to: '/capture', label: 'Нэмэх',      Icon: PlusCircle,  end: false, desc: 'Шинэ баримт оруулах' },
]

function Brand() {
  return (
    <div className="px-4 pb-2">
      <div className="font-display font-bold text-text text-base leading-tight tracking-tight">
        <span className="text-accent">◉</span> FACT LEDGER
      </div>
      <div className="text-[10px] font-mono text-dim uppercase tracking-[0.25em] mt-0.5">
        ▸ Intelligence v2.0
      </div>
    </div>
  )
}

function SideNav() {
  const { logout } = useAuth()

  const linkCls = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-sm font-mono transition-all group ${
      isActive
        ? 'bg-accent-dim text-accent border border-accent-line shadow-[0_0_18px_rgba(56,224,255,0.10)]'
        : 'text-dim border border-transparent hover:bg-surface-2 hover:text-text'
    }`

  return (
    <aside className="w-56 shrink-0 hidden md:flex flex-col gap-0.5 sticky top-0 h-screen py-6 px-2 border-r border-line bg-ink-900/50">
      <div className="mb-7 px-2">
        <Brand />
      </div>

      {NAV_ITEMS.map(({ to, label, Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={linkCls}>
          <Icon size={16} strokeWidth={1.75} />
          <span>{label}</span>
        </NavLink>
      ))}

      {/* Тусгаарлагч шугам */}
      <div className="my-3 mx-3 border-t border-line/40" />

      {/* Хайх товч */}
      <NavLink
        to="/entities"
        className="flex items-center gap-3 px-3 py-2.5 rounded-[10px] text-sm font-mono text-dim border border-transparent hover:bg-surface-2 hover:text-text transition-all"
      >
        <Search size={16} strokeWidth={1.75} />
        <span>Субъект хайх</span>
      </NavLink>

      <div className="mt-auto px-3 space-y-1">
        <div className="text-[10px] font-mono text-dim leading-relaxed">
          <span className="text-ok">●</span> SHA-256 VERIFIED
        </div>
        <div className="text-[10px] font-mono text-dim">SYSTEM ONLINE</div>
        <button
          onClick={logout}
          className="mt-2 w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs font-mono text-faint hover:text-danger hover:bg-danger-dim border border-transparent hover:border-danger/20 transition-all"
        >
          <LogOut size={13} />
          <span>Гарах</span>
        </button>
      </div>
    </aside>
  )
}

function MobileBottomNav() {
  const linkCls = ({ isActive }) =>
    `flex flex-col items-center justify-center gap-0.5 flex-1 py-2 min-h-[52px] text-[11px] font-mono transition-all ${
      isActive
        ? 'text-accent'
        : 'text-faint hover:text-dim'
    }`

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 glass-strong rounded-none border-x-0 border-b-0 flex items-stretch px-1 pt-1 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
      {NAV_ITEMS.map(({ to, label, Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={linkCls}>
          <Icon size={20} strokeWidth={1.75} />
          <span className="leading-none mt-0.5">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

function MobileTopBar() {
  const { pathname } = useLocation()
  const current = NAV_ITEMS.find(n => n.end ? pathname === n.to : pathname.startsWith(n.to))

  return (
    <header className="md:hidden sticky top-0 z-40 glass-strong rounded-none border-x-0 border-t-0 flex items-center h-12 px-4 gap-3">
      <div className="font-display font-bold text-sm text-text">
        <span className="text-accent">◉</span> FACT LEDGER
      </div>
      {current && (
        <>
          <span className="text-line">›</span>
          <span className="text-xs font-mono text-accent">{current.label}</span>
        </>
      )}
      <span className="ml-auto text-[11px] font-mono text-ok flex items-center gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-ok inline-block animate-pulse" />
        LIVE
      </span>
    </header>
  )
}

export default function AppShell({ children }) {
  const { pathname } = useLocation()
  const isFullBleed = pathname === '/' || pathname === '/macro' || pathname.startsWith('/cases/')
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-ink-950">
      <SideNav />
      <MobileTopBar />
      <main
        className={`flex-1 min-w-0 px-3 md:px-6 py-4 md:py-6 pb-[calc(4rem+env(safe-area-inset-bottom))] md:pb-6 ${
          isFullBleed ? '' : 'max-w-5xl mx-auto w-full'
        }`}
      >
        {children}
      </main>
      <MobileBottomNav />
    </div>
  )
}
