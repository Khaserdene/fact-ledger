import { Fragment } from 'react'
import { Link } from 'react-router-dom'
import { compareTimeline, formatFlexDate } from '../../lib/dates'
import Badge from '../ui/Badge'

/**
 * Тасралтгүй цагийн шугам: НЭГ absolute зураас бүх жагсаалтын дээгүүр үргэлжилнэ,
 * жилийн тэмдэглэгээ болон факт бүрийн цэг мөн тэр зураасан дээр байрлана —
 * бүлэглэлт, шүүлтээс үл хамааран шугам геометрийн хувьд хэзээ ч тасрахгүй.
 */

function sentimentTone(f) {
  if (f.has_contradiction) return 'bg-danger ring-danger/30'
  if (f.sentiment_score != null && f.sentiment_score < -0.3) return 'bg-danger/80 ring-danger/25'
  if (f.sentiment_score != null && f.sentiment_score > 0.3) return 'bg-ok ring-ok/25'
  return 'bg-line-strong ring-white/10'
}

function YearMarker({ label }) {
  return (
    <div className="relative pl-10 py-3">
      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[19px] h-[19px] rounded-full bg-ink-900 border border-accent-line grid place-items-center">
        <span className="w-1.5 h-1.5 rounded-full bg-accent" />
      </span>
      <span className="font-display text-accent text-lg font-bold tracking-wide">{label}</span>
    </div>
  )
}

function TimelineItem({ fact, onDelete, activeTag, onTagClick }) {
  const dateLabel = formatFlexDate(fact.fact_date, fact.date_precision, fact.fact_date_end)
  return (
    <div className="relative pl-10 pb-3">
      {/* Зураасан дээрх пин */}
      <span
        className={`absolute left-[5px] top-[18px] w-[9px] h-[9px] rounded-full ring-4 ${sentimentTone(fact)}`}
      />
      <div className="glass px-4 py-3 text-sm">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              {dateLabel && (
                <span className="text-xs font-mono text-accent/90">{dateLabel}</span>
              )}
              {fact.has_contradiction && <Badge tone="danger">⚠ Зөрчил</Badge>}
              {fact.sentiment_score != null && fact.sentiment_score < -0.3 && (
                <Badge tone="danger">сөрөг</Badge>
              )}
              {fact.sentiment_score != null && fact.sentiment_score > 0.3 && (
                <Badge tone="ok">эерэг</Badge>
              )}
              {fact.role_context && (
                <span className="text-xs text-faint italic">{fact.role_context}</span>
              )}
            </div>
            <p className="text-text leading-relaxed">{fact.fact_text}</p>
            {fact.source_quote && (
              <p className="text-xs text-faint mt-1.5 italic border-l-2 border-line-strong pl-2 leading-relaxed">
                «{fact.source_quote.slice(0, 120)}
                {fact.source_quote.length > 120 ? '…' : ''}»
              </p>
            )}
            <div className="flex items-center flex-wrap gap-1.5 mt-2">
              {fact.source_id && (
                <Link
                  to={`/sources/${fact.source_id}`}
                  className="text-xs text-accent/80 hover:text-accent hover:underline mr-1"
                >
                  ⎘ Эх сурвалж
                </Link>
              )}
              {fact.tags.map((t) => (
                <button
                  key={t}
                  onClick={() => onTagClick?.(t)}
                  className={`text-xs px-2 py-0.5 rounded-full transition-colors ${
                    activeTag === t
                      ? 'bg-accent-dim text-accent'
                      : 'bg-surface-2 text-faint hover:text-dim'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          {onDelete && (
            <button
              onClick={() => onDelete(fact.id)}
              className="text-faint hover:text-danger shrink-0 transition-colors"
              title="Устгах"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Timeline({ facts, onDeleteFact, activeTag, onTagClick }) {
  const sorted = [...facts].sort(compareTimeline)

  // Жилээр бүлэглэнэ (огноогүй нь төгсгөлд)
  const groups = []
  for (const f of sorted) {
    const year = f.fact_date ? f.fact_date.slice(0, 4) : 'Огноогүй'
    const last = groups[groups.length - 1]
    if (last && last[0] === year) last[1].push(f)
    else groups.push([year, [f]])
  }

  return (
    <div className="relative">
      {/* Ганц тасралтгүй зураас */}
      <div aria-hidden className="absolute left-[9px] top-2 bottom-2 w-px bg-line-strong" />
      {groups.map(([year, items]) => (
        <Fragment key={year}>
          <YearMarker label={year} />
          {items.map((f) => (
            <TimelineItem
              key={f.id}
              fact={f}
              onDelete={onDeleteFact}
              activeTag={activeTag}
              onTagClick={onTagClick}
            />
          ))}
        </Fragment>
      ))}
    </div>
  )
}
