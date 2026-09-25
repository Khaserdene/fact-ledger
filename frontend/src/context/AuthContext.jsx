import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'
import { api } from '../api'

// ═══════════════════════════════════════════════════════════════════
// КОД ҮҮСГЭЛТ — Цаг хугацаанд суурилсан, обфускацитай
// ═══════════════════════════════════════════════════════════════════

/** Нууц давхар хамгаалалтын мөр — frontend-д байрласан тул GitHub-д push хийхгүй байх */
const SECRET_SALT = 'MNT_FL_INTEL_K99'

/** Master код — хөгжүүлэгчийн байнгын нэвтрэх код */
export const MASTER_CODE = 'factledger2026'

/** Session үргэлжлэх анхдагч хугацаа: 2 цаг (ms) */
const SESSION_DURATION_MS = 2 * 60 * 60 * 1000

/**
 * djb2 hash — string → unsigned 32-bit integer
 */
function djb2(str) {
  let h = 5381
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h, 33) ^ str.charCodeAt(i)
  }
  return h >>> 0
}

/**
 * LCG нэмэлт холилт
 */
function lcgMix(n) {
  return (Math.imul(n, 1664525) + 1013904223) >>> 0
}

/**
 * Тухайн UTC цаг үед хамааралтай нэвтрэх код үүсгэнэ (2 цагийн блок).
 */
export function generateTimeCode(date) {
  const now = date || new Date()
  const yyyy = now.getUTCFullYear()
  const mm = String(now.getUTCMonth() + 1).padStart(2, '0')
  const dd = String(now.getUTCDate()).padStart(2, '0')
  const block = Math.floor(now.getUTCHours() / 2) // 0–11

  const raw = `${SECRET_SALT}|${yyyy}-${mm}-${dd}|${String(block).padStart(2, '0')}`
  const mixed = lcgMix(djb2(raw))

  // base-36 (0-9, A-Z) → 6 тэмдэгт
  const B36 = 36 ** 6
  return (mixed % B36).toString(36).toUpperCase().padStart(6, '0')
}

/**
 * Дараагийн блок хэдий үед эхлэхийг буцаана (UTC)
 */
export function nextBlockTime(date) {
  const now = date || new Date()
  const block = Math.floor(now.getUTCHours() / 2)
  const nextBlock = (block + 1) * 2
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), nextBlock, 0, 0))
}

// ═══════════════════════════════════════════════════════════════════
// AUTH CONTEXT
// ═══════════════════════════════════════════════════════════════════

const AuthContext = createContext(null)

function checkLocalSession() {
  try {
    const raw = sessionStorage.getItem('fl_auth')
    if (!raw) return { valid: false, isMaster: false }
    const parsed = JSON.parse(raw)
    const expiry = parsed.expiresAt || (parsed.loginTime ? parsed.loginTime + SESSION_DURATION_MS : 0)
    return {
      valid: Date.now() < expiry,
      isMaster: Boolean(parsed.isMaster),
    }
  } catch {
    return { valid: false, isMaster: false }
  }
}

export function AuthProvider({ children }) {
  const localInit = checkLocalSession()
  const [authed, setAuthed] = useState(() => localInit.valid)
  const [isMaster, setIsMaster] = useState(() => localInit.isMaster)
  const [sessionData, setSessionData] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem('fl_auth') || 'null')
    } catch {
      return null
    }
  })
  const [kickReason, setKickReason] = useState(null)
  const isVerifyingRef = useRef(false)

  const logout = useCallback((reason = null) => {
    sessionStorage.removeItem('fl_auth')
    sessionStorage.removeItem('fl_token')
    setSessionData(null)
    setAuthed(false)
    setIsMaster(false)
    if (reason) {
      setKickReason(reason)
    }
  }, [])

  // Сессийг backend-ээр шалгах (Terminate хийгдсэн эсэх болон эрх шалгах)
  const verifySession = useCallback(async () => {
    if (isVerifyingRef.current) return
    const token = sessionStorage.getItem('fl_token')
    if (!token) {
      const chk = checkLocalSession()
      if (!chk.valid) {
        logout('Хугацаа дууссан тул гарлаа.')
      } else {
        setIsMaster(chk.isMaster)
      }
      return
    }

    try {
      isVerifyingRef.current = true
      const res = await api.verifySession()
      if (!res.valid) {
        if (res.reason === 'terminated') {
          logout('Админ таны эрхийг цуцаллаа (Terminated).')
        } else if (res.reason === 'expired') {
          logout('Таны нэвтрэх сессийн хугацаа дууслаа.')
        } else {
          logout('Сесс хүчингүй болсон байна.')
        }
      } else if (res.session) {
        const masterStatus = Boolean(res.is_master || res.session.code_type === 'master')
        setIsMaster(masterStatus)

        // Хугацаа сунгагдсан байж болзошгүй тул local expiresAt шинэчлэх
        const newExpiry = new Date(res.session.expires_at).getTime()
        const raw = sessionStorage.getItem('fl_auth')
        if (raw) {
          try {
            const parsed = JSON.parse(raw)
            parsed.expiresAt = newExpiry
            parsed.isMaster = masterStatus
            sessionStorage.setItem('fl_auth', JSON.stringify(parsed))
            setSessionData(parsed)
          } catch {
            // ignore
          }
        }
      }
    } catch {
      const chk = checkLocalSession()
      if (!chk.valid) {
        logout('Сессийн хугацаа дууслаа.')
      }
    } finally {
      isVerifyingRef.current = false
    }
  }, [logout])

  // Тогтмол давтамжтайгаар (15 сек) болон цонх идэвхжихэд verify хийх
  useEffect(() => {
    if (!authed) return

    verifySession()
    const interval = setInterval(verifySession, 15000)
    const onFocus = () => verifySession()
    window.addEventListener('focus', onFocus)

    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', onFocus)
    }
  }, [authed, verifySession])

  const login = useCallback(async (code, clientLabel = '') => {
    const trimmed = code.trim()
    setKickReason(null)

    // 1. Эхлээд Backend Auth API-аар нэвтрэхийг оролдох
    try {
      const res = await api.login(trimmed, clientLabel)
      if (res && res.token) {
        const masterStatus = Boolean(res.is_master || res.code_type === 'master' || trimmed.toLowerCase() === MASTER_CODE.toLowerCase())
        const expiresAt = new Date(res.expires_at).getTime()
        const payload = {
          token: res.token,
          sessionId: res.session_id,
          isMaster: masterStatus,
          expiresAt,
          loginTime: Date.now(),
        }
        sessionStorage.setItem('fl_token', res.token)
        sessionStorage.setItem('fl_auth', JSON.stringify(payload))
        setSessionData(payload)
        setIsMaster(masterStatus)
        setAuthed(true)
        return true
      }
    } catch (err) {
      if (err.message && (err.message.includes('буруу') || err.message.includes('401'))) {
        return false
      }
    }

    // 2. Local Fallback
    const currentCode = generateTimeCode()
    const isMasterCode = trimmed.toLowerCase() === MASTER_CODE.toLowerCase()
    const isTimeBased = trimmed.toUpperCase() === currentCode

    if (isMasterCode || isTimeBased) {
      const payload = {
        loginTime: Date.now(),
        isMaster: isMasterCode,
        expiresAt: Date.now() + SESSION_DURATION_MS,
      }
      sessionStorage.setItem('fl_auth', JSON.stringify(payload))
      setSessionData(payload)
      setIsMaster(isMasterCode)
      setAuthed(true)
      return true
    }

    return false
  }, [])

  // DevTools console helper
  useEffect(() => {
    window.flCode = () => {
      const code = generateTimeCode()
      const next = nextBlockTime()
      console.log(
        `%cFACT LEDGER — Одоогийн нэвтрэх код`,
        'color:#38e0ff;font-weight:bold;font-size:14px'
      )
      console.log(`%c${code}`, 'color:#34e28a;font-weight:bold;font-size:28px;letter-spacing:4px')
      console.log(`%cДараагийн код (UTC): ${next.toISOString().slice(11, 16)}`, 'color:#7c93a3')
      return code
    }
  }, [])

  return (
    <AuthContext.Provider value={{ authed, isMaster, sessionData, kickReason, login, logout, verifySession }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
