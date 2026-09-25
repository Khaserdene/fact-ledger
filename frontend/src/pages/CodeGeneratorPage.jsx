import { useState, useEffect, useMemo, useCallback } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { generateTimeCode, nextBlockTime, MASTER_CODE, useAuth } from '../context/AuthContext'
import { api } from '../api'
import {
  Key,
  Copy,
  Check,
  Clock,
  Shield,
  Send,
  ArrowRight,
  ArrowLeft,
  RefreshCw,
  Eye,
  EyeOff,
  Zap,
  AlertTriangle,
  Users,
  PowerOff,
  Plus,
  Edit2,
  Trash2,
  Laptop,
  Smartphone,
  Globe,
  CheckCircle2,
  Lock,
  LogOut,
} from 'lucide-react'

// Хөтөч болон үйлдлийн системийг user_agent-аас хялбархан таних туслах функц
function parseUserAgent(ua) {
  if (!ua) return { device: 'Тодорхойгүй', isMobile: false }
  const isMobile = /mobile|iphone|android|ipad/i.test(ua)
  let os = 'Desktop'
  if (/windows/i.test(ua)) os = 'Windows'
  else if (/macintosh|mac os/i.test(ua)) os = 'macOS'
  else if (/iphone|ipad/i.test(ua)) os = 'iOS'
  else if (/android/i.test(ua)) os = 'Android'
  else if (/linux/i.test(ua)) os = 'Linux'

  let browser = 'Browser'
  if (/edg/i.test(ua)) browser = 'Edge'
  else if (/chrome/i.test(ua)) browser = 'Chrome'
  else if (/safari/i.test(ua)) browser = 'Safari'
  else if (/firefox/i.test(ua)) browser = 'Firefox'

  return { device: `${browser} (${os})`, isMobile }
}

// Секундийг цаг:мин:сек болгон хувиргах
function formatRemaining(sec) {
  if (sec <= 0) return '00:00:00'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h >= 24) {
    const days = Math.floor(h / 24)
    const remH = h % 24
    return `${days}ө ${remH}ц ${m}м`
  }
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function CodeGeneratorPage() {
  const { authed, isMaster, login, logout } = useAuth()
  const [now, setNow] = useState(() => new Date())
  const [copiedCode, setCopiedCode] = useState(false)
  const [copiedNext, setCopiedNext] = useState(false)
  const [copiedShare, setCopiedShare] = useState(false)
  const [copiedMaster, setCopiedMaster] = useState(false)
  const [showMaster, setShowMaster] = useState(false)

  // Мастер нэвтрэх inline төлөвүүд
  const [masterInput, setMasterInput] = useState('')
  const [masterError, setMasterError] = useState('')
  const [unlocking, setUnlocking] = useState(false)
  const [showMasterInput, setShowMasterInput] = useState(false)

  // Сессийн удирдлагын төлөвүүд
  const [sessions, setSessions] = useState([])
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [actionMsg, setActionMsg] = useState(null)
  const [editingLabelId, setEditingLabelId] = useState(null)
  const [editingLabelText, setEditingLabelText] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Секунд тутамд цагийг шинэчлэх
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // Цагийн блокууд
  const currentCode = useMemo(() => generateTimeCode(now), [now])
  const nextDate = useMemo(() => nextBlockTime(now), [now])
  const nextCode = useMemo(() => generateTimeCode(nextDate), [nextDate])

  const currentBlock = Math.floor(now.getUTCHours() / 2)
  const blockStartUtc = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), currentBlock * 2, 0, 0)
  )

  // Үлдсэн хугацаа (ms)
  const msRemaining = Math.max(0, nextDate.getTime() - now.getTime())
  const secRemaining = Math.floor(msRemaining / 1000)
  const remHours = Math.floor(secRemaining / 3600)
  const remMins = Math.floor((secRemaining % 3600) / 60)
  const remSecs = secRemaining % 60
  const countdownStr = `${String(remHours).padStart(2, '0')}:${String(remMins).padStart(2, '0')}:${String(remSecs).padStart(2, '0')}`

  // Прогресс бар
  const totalBlockMs = 2 * 60 * 60 * 1000
  const elapsedMs = now.getTime() - blockStartUtc.getTime()
  const progressPct = Math.min(100, Math.max(0, Math.round((elapsedMs / totalBlockMs) * 100)))

  // Цаг хугацааны стрингүүд
  const ubNextStr = nextDate.toLocaleTimeString('mn-MN', {
    timeZone: 'Asia/Ulaanbaatar',
    hour: '2-digit',
    minute: '2-digit',
  })
  const ubStartStr = blockStartUtc.toLocaleTimeString('mn-MN', {
    timeZone: 'Asia/Ulaanbaatar',
    hour: '2-digit',
    minute: '2-digit',
  })
  const ubTimeStr = now.toLocaleTimeString('mn-MN', {
    timeZone: 'Asia/Ulaanbaatar',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const utcTimeStr = `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}:${String(now.getUTCSeconds()).padStart(2, '0')} UTC`
  const utcNextStr = `${String(nextDate.getUTCHours()).padStart(2, '0')}:${String(nextDate.getUTCMinutes()).padStart(2, '0')} UTC`

  // Хуулбарлах функцүүд
  const copyText = (text, setFn) => {
    navigator.clipboard.writeText(text).then(() => {
      setFn(true)
      setTimeout(() => setFn(false), 2000)
    })
  }

  // Хуваалцах бэлэн мессеж
  const currentUrl = typeof window !== 'undefined' ? `${window.location.origin}/login` : 'https://factledger.app/login'
  const shareMessage = `Үнэний Бүртгэл (Fact Ledger) нэвтрэх холбоос:
🌐 Линк: ${currentUrl}
🔑 Түр код: ${currentCode}
⏰ Хүчинтэй хугацаа: ${ubNextStr} хүртэл (УБ цагаар)
⏱ Сесс: Нэвтэрснээс хойш 2 цаг хүчинтэй байна.`

  const isEndingSoon = remHours === 0 && remMins < 10

  // ═══════════════════════════════════════════════════════════════════
  // СЕСС ТАТАХ БА УДИРДАХ ФУНКЦҮҮД
  // ═══════════════════════════════════════════════════════════════════

  const fetchSessions = useCallback(async (quiet = false) => {
    if (!quiet) setLoadingSessions(true)
    try {
      const data = await api.listSessions(50)
      setSessions(data || [])
    } catch {
      // ignore
    } finally {
      if (!quiet) setLoadingSessions(false)
    }
  }, [])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  // Автомат шинэчлэлт (10 секунд тутам)
  useEffect(() => {
    if (!autoRefresh) return
    const t = setInterval(() => {
      fetchSessions(true)
    }, 10000)
    return () => clearInterval(t)
  }, [autoRefresh, fetchSessions])

  const notify = (msg) => {
    setActionMsg(msg)
    setTimeout(() => setActionMsg(null), 3500)
  }

  // Сесс таслах (Terminate)
  const handleTerminate = async (id, label) => {
    const targetName = label || `Сесс #${id}`
    if (!window.confirm(`Та "${targetName}" хэрэглэгчийн сессийг шууд таслахдаа (Terminate) итгэлтэй байна уу? Хэрэглэгч системээс шууд хөөгдөнө.`)) {
      return
    }

    try {
      await api.terminateSession(id)
      notify(`"${targetName}" сессийг амжилттай цуцаллаа.`)
      await fetchSessions(true)
    } catch (err) {
      alert(`Алдаа: ${err.message}`)
    }
  }

  // Сессийн хугацаа сунгах (Extend)
  const handleExtend = async (id, minutes, label) => {
    try {
      const res = await api.extendSession(id, minutes)
      const hrs = minutes >= 60 ? `${minutes / 60} цагаар` : `${minutes} минутаар`
      notify(`"${label || `#${id}`}" сессийг ${hrs} амжилттай сунгалаа.`)
      await fetchSessions(true)
    } catch (err) {
      alert(`Алдаа: ${err.message}`)
    }
  }

  // Сесст нэр өгөх / засах
  const handleSaveLabel = async (id) => {
    try {
      await api.updateSessionLabel(id, editingLabelText)
      setEditingLabelId(null)
      await fetchSessions(true)
      notify('Хэрэглэгчийн нэрийг хадгаллаа.')
    } catch (err) {
      alert(`Алдаа: ${err.message}`)
    }
  }

  // Сессийг бүртгэлээс устгах
  const handleDelete = async (id) => {
    if (!window.confirm('Энэ сессийн бүртгэлийг түүхээс устгах уу?')) return
    try {
      await api.deleteSession(id)
      await fetchSessions(true)
      notify('Сесс бүртгэлээс устгагдлаа.')
    } catch (err) {
      alert(`Алдаа: ${err.message}`)
    }
  }

  const activeSessionsCount = sessions.filter((s) => s.status === 'active').length

  // Хэрэв нэвтрээгүй бол нэвтрэх хуудас руу чиглүүлнэ
  if (!authed) {
    return <Navigate to="/login" replace />
  }

  // Хэрэв мастер эрхээр нэвтрээгүй бол /generate дээрээс шууд мастер түлхүүрээ оруулж тайлах интерактив дэлгэц
  if (!isMaster) {
    const handleMasterUnlock = async (e) => {
      e.preventDefault()
      if (!masterInput.trim()) return
      setUnlocking(true)
      setMasterError('')
      try {
        const ok = await login(masterInput.trim(), 'Мастер Админ')
        if (ok) {
          setMasterInput('')
        } else {
          setMasterError('Мастер түлхүүр буруу байна. Дахин шалгана уу.')
        }
      } catch (err) {
        setMasterError(err.message || 'Нэвтрэхэд алдаа гарлаа.')
      } finally {
        setUnlocking(false)
      }
    }

    return (
      <div className="min-h-screen bg-ink-950 text-text p-4 md:p-8 relative overflow-hidden flex flex-col items-center justify-center">
        {/* Background Grid */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              'linear-gradient(rgb(56 224 255 / 0.03) 1px, transparent 1px), linear-gradient(90deg, rgb(56 224 255 / 0.03) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
        <div
          className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[350px] rounded-full opacity-20"
          style={{ background: 'radial-gradient(ellipse at center, rgb(56 224 255 / 0.2), transparent 70%)' }}
        />

        <div className="w-full max-w-md relative z-10 space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-dim border border-accent-line shadow-[0_0_40px_rgb(56_224_255/0.25)] mx-auto mb-4">
              <Key size={30} className="text-accent" />
            </div>
            <div className="inline-block px-3 py-0.5 rounded-full bg-accent/10 border border-accent/25 text-accent text-[10px] font-mono tracking-widest uppercase mb-2">
              ADMIN GATEWAY // /generate
            </div>
            <h1 className="text-xl font-bold font-display text-text">
              Мастер Түлхүүр Шаардлагатай
            </h1>
            <p className="text-xs text-dim mt-1.5 leading-relaxed font-mono">
              Энэ хуудас нь нэвтрэх кодуудыг үүсгэх болон идэвхтэй сессүүдийг удирдах админ хэсэг юм. Хандахын тулд хөгжүүлэгчийн Мастер кодоо оруулна уу.
            </p>
          </div>

          {/* Master Unlock Form */}
          <div className="glass-strong border border-line-strong rounded-2xl p-6 shadow-[0_8px_40px_rgba(0,0,0,0.5)] space-y-4">
            <form onSubmit={handleMasterUnlock} className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono text-text">
                  <span className="flex items-center gap-1.5">
                    <Lock size={13} className="text-accent" />
                    <span>МАСТЕР ТҮЛХҮҮР</span>
                  </span>
                </div>

                <div className="relative">
                  <input
                    type={showMasterInput ? 'text' : 'password'}
                    value={masterInput}
                    onChange={(e) => {
                      setMasterInput(e.target.value)
                      if (masterError) setMasterError('')
                    }}
                    placeholder="••••••••••••••"
                    autoFocus
                    spellCheck={false}
                    className="w-full bg-surface px-4 py-3 pr-11 rounded-xl font-mono text-sm text-text border border-line focus:border-accent-line outline-none transition-all placeholder:text-faint"
                  />
                  <button
                    type="button"
                    onClick={() => setShowMasterInput(!showMasterInput)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-faint hover:text-dim transition-colors p-1"
                  >
                    {showMasterInput ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {masterError && (
                <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-danger-dim border border-danger/30 text-danger text-xs font-mono animate-fadeIn">
                  <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                  <span>{masterError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={unlocking || !masterInput.trim()}
                className="w-full py-3 rounded-xl font-mono font-bold text-xs tracking-wider uppercase transition-all flex items-center justify-center gap-2 disabled:opacity-40"
                style={{
                  background: unlocking || !masterInput.trim()
                    ? 'rgb(56 224 255 / 0.1)'
                    : 'linear-gradient(135deg, rgb(56 224 255 / 0.2), rgb(56 224 255 / 0.08))',
                  border: '1px solid rgb(56 224 255 / 0.4)',
                  color: '#38e0ff',
                  boxShadow: masterInput.trim() ? '0 0 20px rgb(56 224 255 / 0.15)' : 'none',
                }}
              >
                {unlocking ? (
                  <>
                    <RefreshCw size={14} className="animate-spin text-accent" />
                    <span>ШАЛГАЖ БАЙНА...</span>
                  </>
                ) : (
                  <>
                    <Key size={14} />
                    <span>ТАЙЛАХ БА ОРОХ</span>
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="text-center pt-2">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs font-mono text-dim hover:text-accent transition-colors"
            >
              <ArrowLeft size={13} />
              <span>Үндсэн систем рүү буцах</span>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-ink-950 text-text p-4 md:p-8 relative overflow-hidden flex flex-col items-center">
      {/* Background Grid */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(rgb(56 224 255 / 0.03) 1px, transparent 1px), linear-gradient(90deg, rgb(56 224 255 / 0.03) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* Radial ambient glow */}
      <div
        className="pointer-events-none absolute top-10 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full opacity-20"
        style={{ background: 'radial-gradient(ellipse at center, rgb(56 224 255 / 0.2), transparent 70%)' }}
      />
      <div
        className="pointer-events-none absolute bottom-0 right-10 w-[500px] h-[300px] rounded-full opacity-15"
        style={{ background: 'radial-gradient(ellipse at center, rgb(52 226 138 / 0.2), transparent 70%)' }}
      />

      {/* Floating Action Notification Toast */}
      {actionMsg && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-ink-900 border border-ok/50 text-ok px-4 py-3 rounded-xl shadow-2xl backdrop-blur-md font-mono text-xs animate-fadeIn">
          <CheckCircle2 size={16} className="text-ok shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      <div className="w-full max-w-2xl relative z-10 space-y-6">
        {/* Top Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent" />
            </span>
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent font-semibold">
              ADMIN CONTROL // SESSIONS & KEYS
            </span>
          </div>

          <Link
            to={authed ? '/' : '/login'}
            className="text-xs font-mono text-dim hover:text-accent flex items-center gap-1.5 transition-colors"
          >
            {authed ? 'Систем рүү очих' : 'Нэвтрэх нүүр'}
            <ArrowRight size={13} />
          </Link>
        </div>

        {/* Title Header Card */}
        <div className="bg-ink-900/80 border border-ink-700/60 rounded-2xl p-5 backdrop-blur-md">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-accent-dim border border-accent-line flex items-center justify-center shrink-0 shadow-[0_0_25px_rgb(56_224_255/0.2)]">
              <Key size={24} className="text-accent" />
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-bold font-display text-text flex items-center gap-2">
                <span>FACT LEDGER</span>
                <span className="text-xs px-2 py-0.5 rounded bg-ink-800 text-dim font-mono border border-ink-700 font-normal">
                  /generate
                </span>
              </h1>
              <p className="text-xs text-dim mt-1">
                Нэвтрэх түр кодуудыг үүсгэх, хуулж илгээх болон нэвтэрсэн хэрэглэгчдийн сессийг шууд таслах (terminate), хугацааг сунгах (extend) админ хуудас.
              </p>
            </div>
          </div>
        </div>

        {/* Primary Card: Active Time-based Code */}
        <div className="bg-ink-900/90 border border-accent/30 rounded-2xl p-6 backdrop-blur-md shadow-[0_0_50px_rgb(56_224_255/0.08)] relative overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Zap size={15} className="text-ok" />
              <span className="font-mono text-xs text-ok font-semibold tracking-wider uppercase">
                ИДЭВХИТЭЙ НЭВТРЭХ КОД
              </span>
            </div>
            <span className="font-mono text-xs text-dim">
              Блок: #{currentBlock + 1} / 12
            </span>
          </div>

          {/* Big Code Display */}
          <div
            onClick={() => copyText(currentCode, setCopiedCode)}
            className="group relative cursor-pointer bg-ink-950/80 border border-ok/40 hover:border-ok rounded-xl py-6 px-4 text-center transition-all duration-200 hover:shadow-[0_0_30px_rgb(52_226_138/0.2)] active:scale-[0.99]"
            title="Дарж хуулна уу"
          >
            <div className="text-4xl md:text-5xl font-mono font-black tracking-[0.25em] text-ok transition-transform group-hover:scale-105 select-all">
              {currentCode}
            </div>

            <div className="mt-3 flex items-center justify-center gap-2 text-xs font-mono text-dim group-hover:text-ok transition-colors">
              {copiedCode ? (
                <>
                  <Check size={14} className="text-ok" />
                  <span className="text-ok font-semibold">САНАХ ОЙД ХУУЛАГДЛАА!</span>
                </>
              ) : (
                <>
                  <Copy size={13} />
                  <span>Дарж хуулж авах</span>
                </>
              )}
            </div>
          </div>

          {/* Progress Bar & Countdown */}
          <div className="mt-5 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-dim flex items-center gap-1.5">
                <Clock size={13} className={isEndingSoon ? 'text-warn animate-pulse' : 'text-accent'} />
                <span>Дуусах хүртэл:</span>
                <strong className={isEndingSoon ? 'text-warn font-bold' : 'text-accent font-bold'}>
                  {countdownStr}
                </strong>
              </span>
              <span className="text-dim">
                {ubStartStr} – {ubNextStr} (УБ)
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-2 rounded-full bg-ink-800 overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ${
                  isEndingSoon
                    ? 'bg-gradient-to-r from-warn to-danger'
                    : 'bg-gradient-to-r from-accent to-ok'
                }`}
                style={{ width: `${progressPct}%` }}
              />
            </div>

            {isEndingSoon && (
              <div className="flex items-center gap-2 text-[11px] text-warn bg-warn/10 border border-warn/20 rounded-lg p-2 mt-2">
                <AlertTriangle size={14} className="shrink-0" />
                <span>
                  Энэ код 10 минутын дотор дуусна. Хэрэв хүлээн авагч оройтож нэвтрэх бол <strong>дараагийн блокийн код</strong>-ыг өгөх нь найдвартай.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Next Block Code Preview */}
        <div className="bg-ink-900/70 border border-ink-700/60 rounded-2xl p-4 md:p-5 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[11px] font-mono text-dim uppercase tracking-wider">
                ⏭ ДАРААГИЙН БЛОКИЙН КОД (ХҮЛЭЭГДЭЖ БУЙ)
              </div>
              <div className="text-xs text-dim mt-0.5">
                Эхлэх: <span className="text-text font-mono font-medium">{ubNextStr} (УБ)</span> /{' '}
                <span className="text-dim font-mono">{utcNextStr}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="font-mono text-xl font-bold tracking-widest text-text/80 bg-ink-950 px-3 py-1.5 rounded-lg border border-ink-700">
                {nextCode}
              </span>
              <button
                type="button"
                onClick={() => copyText(nextCode, setCopiedNext)}
                className="p-2 rounded-lg bg-ink-800 hover:bg-ink-700 text-dim hover:text-text transition-colors border border-ink-700"
                title="Дараагийн кодыг хуулах"
              >
                {copiedNext ? <Check size={16} className="text-ok" /> : <Copy size={16} />}
              </button>
            </div>
          </div>
        </div>

        {/* Quick Share Card */}
        <div className="bg-ink-900/70 border border-ink-700/60 rounded-2xl p-5 backdrop-blur-md space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Send size={15} className="text-accent" />
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-text">
                ХҮНД ИЛГЭЭХ БЭЛЭН ТЕКСТ
              </span>
            </div>

            <button
              type="button"
              onClick={() => copyText(shareMessage, setCopiedShare)}
              className="flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg bg-accent/15 border border-accent/40 text-accent hover:bg-accent/25 transition-all"
            >
              {copiedShare ? (
                <>
                  <Check size={13} className="text-ok" />
                  <span className="text-ok">Хуулагдлаа!</span>
                </>
              ) : (
                <>
                  <Copy size={13} />
                  <span>Текст хуулах</span>
                </>
              )}
            </button>
          </div>

          <pre className="text-xs font-mono bg-ink-950/80 border border-ink-800 rounded-xl p-3.5 text-text/80 whitespace-pre-wrap leading-relaxed select-all">
            {shareMessage}
          </pre>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════ */}
        {/* NEW: LIVE SESSIONS MANAGEMENT (TERMINATE & EXTEND) */}
        {/* ═══════════════════════════════════════════════════════════════════ */}
        <div className="bg-ink-900/90 border border-accent/20 rounded-2xl p-5 md:p-6 backdrop-blur-md shadow-[0_0_40px_rgba(0,0,0,0.4)] space-y-4">
          {/* Header of Sessions */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-ink-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center text-accent">
                <Users size={17} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-text">
                    НЭВТРЭСЭН ХЭРЭГЛЭГЧИД БА СЕССҮҮД
                  </h2>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
                    Идэвхтэй: {activeSessionsCount}
                  </span>
                </div>
                <p className="text-[11px] text-dim font-mono">
                  Хэрэглэгчийн сессийг шууд таслах (Terminate) эсвэл хугацааг сунгах (Extend)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono">
              <button
                type="button"
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-2.5 py-1 rounded-lg border text-[11px] transition-colors ${
                  autoRefresh
                    ? 'bg-ok/10 border-ok/30 text-ok'
                    : 'bg-ink-800 border-ink-700 text-dim'
                }`}
                title="10 секунд тутам автоматаар шинэчлэх"
              >
                {autoRefresh ? '● Авто-шинэчлэлт ON' : '○ Авто-шинэчлэлт OFF'}
              </button>

              <button
                type="button"
                onClick={() => fetchSessions()}
                disabled={loadingSessions}
                className="p-1.5 rounded-lg bg-ink-800 hover:bg-ink-700 text-dim hover:text-accent border border-ink-700 transition-colors"
                title="Шинэчлэх"
              >
                <RefreshCw size={14} className={loadingSessions ? 'animate-spin text-accent' : ''} />
              </button>
            </div>
          </div>

          {/* Sessions List */}
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-dim font-mono text-xs bg-ink-950/40 rounded-xl border border-ink-800/60">
              {loadingSessions ? 'Сессүүдийг уншиж байна...' : 'Одоогоор бүртгэгдсэн сесс байхгүй байна.'}
            </div>
          ) : (
            <div className="space-y-3">
              {sessions.map((sess) => {
                const uaParsed = parseUserAgent(sess.user_agent)
                const isActive = sess.status === 'active'
                const isTerminated = sess.status === 'terminated'
                const isExpired = sess.status === 'expired'

                const loginDateStr = new Date(sess.created_at).toLocaleTimeString('mn-MN', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })

                const remSec = sess.remaining_seconds || 0
                const remStr = formatRemaining(remSec)

                return (
                  <div
                    key={sess.id}
                    className={`rounded-xl border p-4 transition-all duration-200 ${
                      isActive
                        ? 'bg-ink-950/80 border-ink-700 hover:border-accent/40 shadow-sm'
                        : isTerminated
                        ? 'bg-danger-dim/20 border-danger/20 opacity-75'
                        : 'bg-ink-950/40 border-ink-800/80 opacity-60'
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      {/* Left: Client info and label */}
                      <div className="space-y-1.5 flex-1 min-w-[220px]">
                        <div className="flex items-center gap-2">
                          {/* Status Badge */}
                          {isActive && (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-ok/10 text-ok border border-ok/30">
                              <span className="w-1.5 h-1.5 rounded-full bg-ok animate-pulse" />
                              ИДЭВХТЭЙ
                            </span>
                          )}
                          {isTerminated && (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-danger-dim text-danger border border-danger/30">
                              <PowerOff size={10} />
                              ЦУЦАЛСАН (TERMINATED)
                            </span>
                          )}
                          {isExpired && (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-ink-800 text-dim border border-ink-700">
                              <Clock size={10} />
                              ХУГАЦАА ДУУССАН
                            </span>
                          )}

                          <span className="font-mono text-[11px] text-faint">
                            #{sess.id} · {sess.code_type === 'master' ? 'МАСТЕР' : `КОД: ${sess.code_value || '???'}`}
                          </span>
                        </div>

                        {/* Editable User Label */}
                        <div className="flex items-center gap-2">
                          {editingLabelId === sess.id ? (
                            <div className="flex items-center gap-1.5 mt-1">
                              <input
                                type="text"
                                value={editingLabelText}
                                onChange={(e) => setEditingLabelText(e.target.value)}
                                placeholder="Хэрэглэгчийн нэр..."
                                className="bg-surface px-2.5 py-1 rounded text-xs font-mono text-text border border-accent/40 outline-none focus:border-accent"
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleSaveLabel(sess.id)
                                  if (e.key === 'Escape') setEditingLabelId(null)
                                }}
                              />
                              <button
                                type="button"
                                onClick={() => handleSaveLabel(sess.id)}
                                className="px-2 py-1 rounded bg-accent/20 text-accent hover:bg-accent/30 text-xs font-mono"
                              >
                                Хадгалах
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditingLabelId(null)}
                                className="px-1.5 py-1 rounded bg-ink-800 text-dim hover:text-text text-xs font-mono"
                              >
                                Болих
                              </button>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1.5 group/label">
                              <span className="font-semibold text-sm text-text">
                                {sess.client_label || 'Нэргүй хэрэглэгч'}
                              </span>
                              <button
                                type="button"
                                onClick={() => {
                                  setEditingLabelId(sess.id)
                                  setEditingLabelText(sess.client_label || '')
                                }}
                                className="text-dim/50 hover:text-accent p-1 transition-colors"
                                title="Нэр өгөх / засах"
                              >
                                <Edit2 size={12} />
                              </button>
                            </div>
                          )}
                        </div>

                        {/* Device & IP details */}
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] font-mono text-dim">
                          <span className="flex items-center gap-1">
                            {uaParsed.isMobile ? <Smartphone size={11} /> : <Laptop size={11} />}
                            <span>{uaParsed.device}</span>
                          </span>
                          <span className="flex items-center gap-1">
                            <Globe size={11} />
                            <span>{sess.ip_address || '127.0.0.1'}</span>
                          </span>
                          <span>Нэвтэрсэн: {loginDateStr}</span>
                        </div>
                      </div>

                      {/* Right: Remaining time & Action controls */}
                      <div className="flex flex-col items-end gap-2.5">
                        {/* Countdown display */}
                        <div className="text-right">
                          <div className="text-[10px] font-mono text-dim uppercase">Үлдсэн хугацаа</div>
                          <div
                            className={`font-mono font-bold text-sm ${
                              isActive
                                ? remSec < 600
                                  ? 'text-warn animate-pulse'
                                  : 'text-ok'
                                : 'text-faint'
                            }`}
                          >
                            {isActive ? remStr : isTerminated ? 'Хаагдсан' : '00:00:00'}
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center gap-1.5">
                          {/* Terminate button */}
                          {isActive && (
                            <button
                              type="button"
                              onClick={() => handleTerminate(sess.id, sess.client_label)}
                              className="flex items-center gap-1 text-[11px] font-mono px-2.5 py-1.5 rounded-lg bg-danger-dim text-danger hover:bg-danger/25 border border-danger/40 transition-colors"
                              title="Сессийг шууд хүчингүй болгож хэрэглэгчийг хөөх"
                            >
                              <PowerOff size={12} />
                              <span>Terminate</span>
                            </button>
                          )}

                          {/* Quick Extend presets */}
                          <div className="flex items-center gap-1 bg-ink-900 border border-ink-700 rounded-lg p-0.5">
                            <button
                              type="button"
                              onClick={() => handleExtend(sess.id, 60, sess.client_label)}
                              className="px-2 py-1 text-[10px] font-mono text-dim hover:text-accent hover:bg-ink-800 rounded transition-colors"
                              title="+1 цаг сунгах"
                            >
                              +1ц
                            </button>
                            <button
                              type="button"
                              onClick={() => handleExtend(sess.id, 1440, sess.client_label)}
                              className="px-2 py-1 text-[10px] font-mono text-dim hover:text-accent hover:bg-ink-800 rounded transition-colors"
                              title="+24 цаг (1 хоног) сунгах"
                            >
                              +24ц
                            </button>
                            <button
                              type="button"
                              onClick={() => handleExtend(sess.id, 10080, sess.client_label)}
                              className="px-2 py-1 text-[10px] font-mono text-dim hover:text-accent hover:bg-ink-800 rounded transition-colors"
                              title="+7 хоног сунгах"
                            >
                              +7х
                            </button>
                          </div>

                          {/* Delete historical record */}
                          {!isActive && (
                            <button
                              type="button"
                              onClick={() => handleDelete(sess.id)}
                              className="p-1.5 text-dim hover:text-danger rounded-lg hover:bg-ink-800 transition-colors"
                              title="Бүртгэлээс устгах"
                            >
                              <Trash2 size={13} />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Master Code Section (Toggleable) */}
        <div className="bg-ink-900/50 border border-ink-800 rounded-2xl p-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield size={15} className="text-dim" />
              <div>
                <span className="text-xs font-mono text-dim font-medium uppercase tracking-wider">
                  Хөгжүүлэгчийн мастер код
                </span>
                <div className="text-[11px] text-dim/70">Хугацаа дуусахгүй, байнгын нэвтрэх түлхүүр</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {showMaster ? (
                <span className="font-mono text-xs text-accent px-2 py-1 rounded bg-ink-950 border border-accent-line">
                  {MASTER_CODE}
                </span>
              ) : (
                <span className="font-mono text-xs text-dim px-2 py-1 rounded bg-ink-950 border border-ink-800">
                  ••••••••••••••
                </span>
              )}

              <button
                type="button"
                onClick={() => setShowMaster(!showMaster)}
                className="p-1.5 rounded-lg bg-ink-800 text-dim hover:text-text border border-ink-700"
                title={showMaster ? 'Нуух' : 'Харах'}
              >
                {showMaster ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>

              <button
                type="button"
                onClick={() => copyText(MASTER_CODE, setCopiedMaster)}
                className="p-1.5 rounded-lg bg-ink-800 text-dim hover:text-text border border-ink-700"
                title="Мастер код хуулах"
              >
                {copiedMaster ? <Check size={14} className="text-ok" /> : <Copy size={14} />}
              </button>
            </div>
          </div>
        </div>

        {/* System & Time Info footer */}
        <div className="text-center text-[11px] font-mono text-dim/60 space-y-1">
          <div>
            УБ Цаг: <span className="text-dim">{ubTimeStr}</span> | UTC: <span className="text-dim">{utcTimeStr}</span>
          </div>
          <div>Session Management: Active DB-backed tokens | Dynamic termination & extension</div>
        </div>
      </div>
    </div>
  )
}
