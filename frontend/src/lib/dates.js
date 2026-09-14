/** Нарийвчлал (precision)-д тохируулсан огнооны хэвлэлт. */

export function formatFlexDate(dateStr, precision, endStr) {
  if (!dateStr) return null
  const year = dateStr.slice(0, 4)
  switch (precision) {
    case 'year':
      return year
    case 'month':
      return dateStr.slice(0, 7)
    case 'range':
      return endStr ? `${year}–${endStr.slice(0, 4)}` : year
    case 'day':
      return dateStr.slice(0, 10)
    default: {
      // precision байхгүй (хуучин өгөгдөл) — heuristic
      if (dateStr.endsWith('-01-01')) return year
      if (/-01$/.test(dateStr.slice(0, 10))) return dateStr.slice(0, 7)
      return dateStr.slice(0, 10)
    }
  }
}

/** Холбоосын хугацааны интервал: "1996 – 2000", "1996 – одоо" */
export function formatPeriod(start, startPrec, end, endPrec) {
  const s = formatFlexDate(start, startPrec)
  const e = formatFlexDate(end, endPrec)
  if (s && e) return s === e ? s : `${s} – ${e}`
  if (s) return `${s} – одоо`
  if (e) return `… – ${e}`
  return null
}

/** Фактыг он цагийн дарааллаар эрэмбэлэх түлхүүр (координат нь fact_date,
 * ижил өдөр дээр бүдүүн нарийвчлалтай нь түрүүлнэ). */
const PRECISION_ORDER = { range: 0, year: 1, month: 2, day: 3 }

export function timelineSortKey(f) {
  return [f.fact_date || '9999-99-99', PRECISION_ORDER[f.date_precision] ?? 4]
}

export function compareTimeline(a, b) {
  const [da, pa] = timelineSortKey(a)
  const [db, pb] = timelineSortKey(b)
  if (da !== db) return da.localeCompare(db)
  return pa - pb
}
