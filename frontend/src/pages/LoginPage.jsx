import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { nextBlockTime } from '../context/AuthContext'
import { Lock, Eye, EyeOff, ShieldCheck, AlertTriangle, Activity, Clock } from 'lucide-react'

// Ар дэвсгэрийн хөдөлгөөнт терминал мөрүүд
const TERMINAL_LINES = [
  '> INITIALIZING FACT-LEDGER INTELLIGENCE ENGINE...',
  '> LOADING ENTITY GRAPH... 1,240 NODES',
  '> MOUNTING CASE DATABASE... 29 ACTIVE',
  '> MACRO SERIES: 1990–2026 | 35 YR',
  '> CROSS-REFERENCE INDEX: READY',
  '> ENCRYPTION: AES-256-GCM',
  '> AWAITING AUTHENTICATION...',
]

function TerminalLine({ text, delay }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  if (!visible) return null
  return (
    <div className="font-mono text-[11px] text-ok/70 leading-relaxed animate-fadeIn">
      {text}
    </div>
  )
}

export default function LoginPage() {
  const { login, kickReason } = useAuth()
  const [code, setCode] = useState('')
  const [show, setShow] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [attempts, setAttempts] = useState(0)
  const [expiryStr, setExpiryStr] = useState('')
  const inputRef = useRef(null)

  // Кодын дуусах цагийг шинэчлэх
  useEffect(() => {
    function updateExpiry() {
      const next = nextBlockTime()
      const h = String(next.getUTCHours()).padStart(2, '0')
      const m = String(next.getUTCMinutes()).padStart(2, '0')
      setExpiryStr(`${h}:${m} UTC`)
    }
    updateExpiry()
    const t = setInterval(updateExpiry, 30_000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const t = setTimeout(() => inputRef.current?.focus(), 800)
    return () => clearTimeout(t)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!code.trim()) return

    setLoading(true)
    setError('')

    try {
      const ok = await login(code)
      if (!ok) {
        const next = attempts + 1
        setAttempts(next)
        setError(
          next >= 3
            ? `ACCESS DENIED [${next}x] — Нэвтрэх код буруу эсвэл хүчингүй болсон байна.`
            : 'НЭВТРЭХ КОД БУРУУ — Дахин оролдоно уу.'
        )
        setCode('')
        setLoading(false)
        inputRef.current?.focus()
      }
    } catch {
      setError('Нэвтрэхэд алдаа гарлаа. Кодоо дахин шалгана уу.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-ink-950 flex items-center justify-center p-4 relative overflow-hidden">

      {/* Ар дэвсгэрийн grid гэрэл */}
      <div className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: 'linear-gradient(rgb(56 224 255 / 0.03) 1px, transparent 1px), linear-gradient(90deg, rgb(56 224 255 / 0.03) 1px, transparent 1px)',
          backgroundSize: '44px 44px',
        }}
      />

      {/* Радиаль гэрлийн ул */}
      <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] rounded-full opacity-20"
        style={{ background: 'radial-gradient(ellipse at center, rgb(56 224 255 / 0.15), transparent 70%)' }}
      />
      <div className="pointer-events-none absolute bottom-0 right-0 w-[500px] h-[300px] opacity-10"
        style={{ background: 'radial-gradient(ellipse at bottom right, rgb(52 226 138 / 0.2), transparent 70%)' }}
      />

      <div className="w-full max-w-md relative z-10">

        {/* Лого + Гарчиг */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-dim border border-accent-line mb-4 shadow-[0_0_40px_rgb(56_224_255/0.2)]">
            <ShieldCheck size={32} className="text-accent" strokeWidth={1.5} />
          </div>
          <h1 className="font-display font-bold text-2xl text-text tracking-tight">
            <span className="text-accent">◉</span> FACT LEDGER
          </h1>
          <p className="text-dim text-xs font-mono uppercase tracking-[0.25em] mt-1">
            Intelligence Platform v2.0
          </p>
        </div>

        {/* Терминал лог самбар */}
        <div className="glass rounded-xl border border-line p-4 mb-6 min-h-[120px] space-y-1">
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-line/40">
            <Activity size={12} className="text-accent animate-pulse" />
            <span className="text-[10px] font-mono text-dim uppercase tracking-widest">SYSTEM BOOT LOG</span>
          </div>
          {TERMINAL_LINES.map((line, i) => (
            <TerminalLine key={i} text={line} delay={i * 200 + 300} />
          ))}
        </div>

        {/* Нэвтрэх форм */}
        <div className="glass-strong rounded-2xl border border-line-strong p-6 shadow-[0_8px_40px_rgba(0,0,0,0.5)]">
          <div className="flex items-center gap-2 mb-5">
            <Lock size={15} className="text-accent" />
            <span className="text-sm font-mono text-text font-medium">НЭВТРЭХ КОД</span>
            {expiryStr && (
              <span className="ml-auto flex items-center gap-1 text-[10px] font-mono text-faint">
                <Clock size={10} className="text-warn" />
                <span className="text-warn">{expiryStr}</span>
                <span>дуусана</span>
              </span>
            )}
          </div>

          {kickReason && (
            <div className="mb-4 flex items-start gap-2.5 px-3.5 py-3 rounded-xl bg-danger-dim/80 border border-danger/30 text-danger text-xs font-mono animate-fadeIn">
              <AlertTriangle size={15} className="shrink-0 mt-0.5" />
              <span>{kickReason}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <input
                ref={inputRef}
                type={show ? 'text' : 'password'}
                value={code}
                onChange={(e) => {
                  setCode(e.target.value)
                  if (error) setError('')
                }}
                placeholder="••••••••••••••"
                autoComplete="current-password"
                spellCheck={false}
                className={`w-full bg-surface px-4 py-3 pr-11 rounded-xl font-mono text-sm text-text border outline-none transition-all placeholder:text-faint ${
                  error
                    ? 'border-danger shadow-[0_0_0_1px_rgb(255_84_100/0.3)]'
                    : 'border-line focus:border-accent-line focus:shadow-[0_0_0_1px_rgb(56_224_255/0.2)]'
                }`}
              />
              <button
                type="button"
                onClick={() => setShow((s) => !s)}
                tabIndex={-1}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-faint hover:text-dim transition-colors p-1"
              >
                {show ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>

            {/* Алдааны мессеж */}
            {error && (
              <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-danger-dim border border-danger/20 animate-fadeIn">
                <AlertTriangle size={13} className="text-danger shrink-0 mt-0.5" />
                <span className="text-danger text-xs font-mono leading-snug">{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !code.trim()}
              className="w-full py-3 rounded-xl font-mono font-bold text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                background: loading || !code.trim()
                  ? 'rgb(56 224 255 / 0.1)'
                  : 'linear-gradient(135deg, rgb(56 224 255 / 0.18), rgb(56 224 255 / 0.08))',
                border: '1px solid rgb(56 224 255 / 0.38)',
                color: '#38e0ff',
                boxShadow: code.trim() && !loading ? '0 0 24px rgb(56 224 255 / 0.12)' : 'none',
              }}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                  <span>ШАЛГАЖ БАЙНА...</span>
                </>
              ) : (
                <>
                  <ShieldCheck size={15} />
                  <span>НЭВТРЭХ</span>
                </>
              )}
            </button>
          </form>

          <p className="text-center text-[10px] font-mono text-faint mt-5">
            SHA-256 VERIFIED · SESSION ENCRYPTED
          </p>
        </div>

        {/* Доод мэдээлэл */}
        <p className="text-center text-[10px] font-mono text-faint mt-4">
          FACT LEDGER © 2024 — RESTRICTED ACCESS
        </p>
      </div>
    </div>
  )
}
