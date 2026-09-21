import { Fragment, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { compareTimeline, formatFlexDate } from '../../lib/dates'
import Badge from '../ui/Badge'
import { 
  Search, Clock, Table, ChevronDown, ChevronRight, 
  ChevronsUpDown, ArrowUpDown, X, ExternalLink, Calendar 
} from 'lucide-react'

function sentimentTone(f) {
  if (f.has_contradiction) return 'bg-danger ring-danger/30'
  if (f.sentiment_score != null && f.sentiment_score < -0.3) return 'bg-danger/80 ring-danger/25'
  if (f.sentiment_score != null && f.sentiment_score > 0.3) return 'bg-ok ring-ok/25'
  return 'bg-line-strong ring-white/10'
}

function SourceProofBadge({ fact }) {
  if (!fact.source_id) return null
  const label = fact.source_title ? (
    fact.source_title.length > 32 ? fact.source_title.slice(0, 30) + '…' : fact.source_title
  ) : 'Эх сурвалж'

  return (
    <Link
      to={`/sources/${fact.source_id}`}
      className="inline-flex items-center gap-1 text-[11px] font-medium text-accent/90 hover:text-accent bg-accent/10 hover:bg-accent/20 border border-accent/20 px-2 py-0.5 rounded transition-colors"
      title={fact.source_title || 'Эх сурвалж үзэх'}
    >
      <span>⎘</span>
      <span className="truncate max-w-[180px]">{label}</span>
    </Link>
  )
}

function YearMarker({ label, count }) {
  return (
    <div className="relative pl-10 py-3 flex items-center justify-between">
      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[19px] h-[19px] rounded-full bg-ink-900 border border-accent-line grid place-items-center">
        <span className="w-1.5 h-1.5 rounded-full bg-accent" />
      </span>
      <span className="font-display text-accent text-lg font-bold tracking-wide">{label}</span>
      {count !== undefined && (
        <span className="text-xs text-faint font-mono mr-2">{count} баримт</span>
      )}
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
      <div className="glass px-4 py-3 text-sm rounded-xl border border-line">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              {dateLabel && (
                <span className="text-xs font-mono text-accent/90 font-medium">{dateLabel}</span>
              )}
              {fact.topic && (
                <span className="text-[11px] px-2 py-0.2 rounded bg-surface-2 text-dim font-medium">
                  {fact.topic}
                </span>
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

            <p className="text-text leading-relaxed text-sm">{fact.fact_text}</p>

            {fact.source_quote && (
              <p className="text-xs text-faint mt-2 italic border-l-2 border-line-strong pl-2.5 leading-relaxed bg-surface/30 py-1 rounded-r">
                «{fact.source_quote.slice(0, 140)}
                {fact.source_quote.length > 140 ? '…' : ''}»
              </p>
            )}

            <div className="flex items-center flex-wrap gap-1.5 mt-2.5">
              <SourceProofBadge fact={fact} />

              {fact.tags.map((t) => (
                <button
                  key={t}
                  onClick={() => onTagClick?.(t)}
                  className={`text-xs px-2 py-0.5 rounded-full transition-colors cursor-pointer ${
                    activeTag === t
                      ? 'bg-accent-dim text-accent font-medium'
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
              className="text-faint hover:text-danger shrink-0 transition-colors p-1"
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
  const [viewMode, setViewMode] = useState('timeline') // 'timeline' | 'table' | 'grouped'
  const [searchQuery, setSearchQuery] = useState('')
  const [topicFilter, setTopicFilter] = useState('all')
  const [sortOrder, setSortOrder] = useState('asc') // 'asc' (oldest first) | 'desc' (newest first)
  const [collapsedYears, setCollapsedYears] = useState({})

  // Distinct topics
  const topics = useMemo(() => {
    const set = new Set()
    for (const f of facts) {
      if (f.topic) set.add(f.topic)
    }
    return Array.from(set)
  }, [facts])

  // Filter and sort facts
  const filteredFacts = useMemo(() => {
    let list = [...facts]

    // 1. Topic filter
    if (topicFilter !== 'all') {
      list = list.filter((f) => f.topic === topicFilter)
    }

    // 2. Search query
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      list = list.filter((f) => 
        (f.fact_text || '').toLowerCase().includes(q) ||
        (f.source_quote || '').toLowerCase().includes(q) ||
        (f.role_context || '').toLowerCase().includes(q) ||
        (f.source_title || '').toLowerCase().includes(q)
      )
    }

    // 3. Sort by timeline date
    list.sort(compareTimeline)
    if (sortOrder === 'desc') {
      list.reverse()
    }
    return list
  }, [facts, topicFilter, searchQuery, sortOrder])

  // Group facts by year
  const groupedByYear = useMemo(() => {
    const groups = []
    for (const f of filteredFacts) {
      const year = f.fact_date ? f.fact_date.slice(0, 4) : 'Огноогүй'
      const last = groups[groups.length - 1]
      if (last && last[0] === year) last[1].push(f)
      else groups.push([year, [f]])
    }
    return groups
  }, [filteredFacts])

  function toggleYear(year) {
    setCollapsedYears((prev) => ({ ...prev, [year]: !prev[year] }))
  }

  function toggleAllYears(collapse) {
    const update = {}
    for (const [y] of groupedByYear) {
      update[y] = collapse
    }
    setCollapsedYears(update)
  }

  return (
    <div className="space-y-4">
      {/* Их өгөгдлийг шүүх & удирдах хяналтын самбар (Toolbar) */}
      <div className="glass p-3 rounded-xl border border-line flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
        {/* Хайлт ба Сэдэв */}
        <div className="flex items-center gap-2 w-full md:w-auto flex-1">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-faint" />
            <input
              type="text"
              placeholder="Фактуудаас хайх..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface border border-line rounded-lg pl-8 pr-7 py-1.5 text-xs text-text placeholder:text-faint focus:outline-none focus:border-accent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-faint hover:text-text"
              >
                <X size={12} />
              </button>
            )}
          </div>

          {topics.length > 0 && (
            <select
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
              className="bg-surface border border-line rounded-lg px-2.5 py-1.5 text-xs text-text focus:outline-none focus:border-accent cursor-pointer max-w-[140px] truncate"
            >
              <option value="all">Бүх сэдэв ({facts.length})</option>
              {topics.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          )}

          <button
            onClick={() => setSortOrder((o) => o === 'asc' ? 'desc' : 'asc')}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-surface border border-line text-dim hover:text-text cursor-pointer shrink-0"
            title={sortOrder === 'asc' ? 'Хуучин нь эхэндээ' : 'Шинэ нь эхэндээ'}
          >
            <ArrowUpDown size={12} />
            <span className="hidden sm:inline">{sortOrder === 'asc' ? 'Эхнээсээ' : 'Сүүлээсээ'}</span>
          </button>
        </div>

        {/* Харагдацын горим солих (Timeline vs Dense Table vs Grouped Year) */}
        <div className="flex items-center gap-1 bg-surface border border-line rounded-lg p-0.5 self-end md:self-auto shrink-0">
          <button
            onClick={() => setViewMode('timeline')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
              viewMode === 'timeline' ? 'bg-surface-2 text-accent font-medium' : 'text-faint hover:text-text'
            }`}
            title="Цаг хугацааны хэлхээс"
          >
            <Clock size={13} />
            <span>Хэлхээс</span>
          </button>

          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
              viewMode === 'table' ? 'bg-surface-2 text-accent font-medium' : 'text-faint hover:text-text'
            }`}
            title="Хүснэгтэн товч харагдац"
          >
            <Table size={13} />
            <span>Хүснэгт</span>
          </button>

          <button
            onClick={() => setViewMode('grouped')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
              viewMode === 'grouped' ? 'bg-surface-2 text-accent font-medium' : 'text-faint hover:text-text'
            }`}
            title="Оноор бүлэглэсэн"
          >
            <Calendar size={13} />
            <span>Оноор</span>
          </button>
        </div>
      </div>

      {/* Шүүлтүүрийн илэрц тооцоо */}
      {(searchQuery || topicFilter !== 'all') && (
        <div className="flex items-center justify-between text-xs text-faint px-1">
          <span>Хайлтад олдсон: <strong className="text-text">{filteredFacts.length}</strong> факт</span>
          <button
            onClick={() => { setSearchQuery(''); setTopicFilter('all'); }}
            className="text-accent hover:underline"
          >
            Цэвэрлэх
          </button>
        </div>
      )}

      {/* ── 1. Хэлхээс харагдац (Timeline View) ── */}
      {viewMode === 'timeline' && (
        <div className="relative">
          <div aria-hidden className="absolute left-[9px] top-2 bottom-2 w-px bg-line-strong" />
          {groupedByYear.map(([year, items]) => (
            <Fragment key={year}>
              <YearMarker label={year} count={items.length} />
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
      )}

      {/* ── 2. Хүснэгтэн товч харагдац (Dense Table View - High Information Density) ── */}
      {viewMode === 'table' && (
        <div className="glass rounded-xl overflow-hidden border border-line">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-line bg-surface/60 text-faint font-medium">
                  <th className="py-2.5 px-3 w-28 font-mono">Огноо</th>
                  <th className="py-2.5 px-3 w-32">Сэдэв</th>
                  <th className="py-2.5 px-3">Баримтын агуулга</th>
                  <th className="py-2.5 px-3 w-48">Эх сурвалж</th>
                  <th className="py-2.5 px-2 w-16 text-center">Үнэлгээ</th>
                  {onDeleteFact && <th className="py-2.5 px-2 w-10 text-right"></th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-line/50">
                {filteredFacts.map((f) => {
                  const dateLabel = formatFlexDate(f.fact_date, f.date_precision, f.fact_date_end)
                  return (
                    <tr key={f.id} className="hover:bg-surface-2/30 transition-colors group">
                      <td className="py-2 px-3 font-mono text-accent/90 whitespace-nowrap align-top">
                        {dateLabel || '—'}
                      </td>
                      <td className="py-2 px-3 align-top">
                        {f.topic ? (
                          <span className="px-1.5 py-0.5 rounded bg-surface border border-line text-dim text-[11px] inline-block font-medium">
                            {f.topic}
                          </span>
                        ) : (
                          <span className="text-faint text-[11px]">—</span>
                        )}
                        {f.role_context && (
                          <span className="text-[10px] text-faint block mt-0.5 italic">
                            {f.role_context}
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-3 align-top leading-relaxed text-text">
                        <div>{f.fact_text}</div>
                        {f.source_quote && (
                          <div className="text-[11px] text-faint italic mt-1 border-l border-accent/40 pl-2">
                            «{f.source_quote.slice(0, 100)}{f.source_quote.length > 100 ? '…' : ''}»
                          </div>
                        )}
                        {f.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {f.tags.slice(0, 4).map((t) => (
                              <span key={t} className="text-[10px] bg-surface text-faint px-1.5 py-0.2 rounded">
                                #{t}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="py-2 px-3 align-top">
                        <SourceProofBadge fact={f} />
                      </td>
                      <td className="py-2 px-2 text-center align-top">
                        <div className="flex items-center justify-center gap-1 mt-1">
                          <span className={`w-2 h-2 rounded-full ${sentimentTone(f)}`} />
                          {f.has_contradiction && <span className="text-[10px] text-danger font-bold">⚠</span>}
                        </div>
                      </td>
                      {onDeleteFact && (
                        <td className="py-2 px-2 text-right align-top">
                          <button
                            onClick={() => onDeleteFact(f.id)}
                            className="text-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity p-1"
                            title="Устгах"
                          >
                            ✕
                          </button>
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── 3. Оноор бүлэглэсэн харагдац (Grouped Year Accordion) ── */}
      {viewMode === 'grouped' && (
        <div className="space-y-3">
          <div className="flex items-center justify-end gap-2 text-xs text-dim">
            <button
              onClick={() => toggleAllYears(false)}
              className="hover:text-accent hover:underline cursor-pointer"
            >
              Бүгдийг дэлгэх
            </button>
            <span>•</span>
            <button
              onClick={() => toggleAllYears(true)}
              className="hover:text-accent hover:underline cursor-pointer"
            >
              Бүгдийг хураах
            </button>
          </div>

          {groupedByYear.map(([year, items]) => {
            const isCollapsed = !!collapsedYears[year]
            return (
              <div key={year} className="glass rounded-xl border border-line overflow-hidden">
                <button
                  onClick={() => toggleYear(year)}
                  className="w-full px-4 py-3 bg-surface/50 hover:bg-surface flex items-center justify-between transition-colors cursor-pointer text-left"
                >
                  <div className="flex items-center gap-2.5">
                    {isCollapsed ? <ChevronRight size={16} className="text-faint" /> : <ChevronDown size={16} className="text-accent" />}
                    <span className="font-display font-bold text-accent text-base">{year}</span>
                    <span className="text-xs text-dim bg-surface-2 px-2 py-0.5 rounded-full font-mono">
                      {items.length} баримт
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-faint">
                    {items.some(x => x.topic === 'улсын_төсөв') && (
                      <span className="px-1.5 py-0.2 rounded bg-accent/15 text-accent text-[10px]">төсөв</span>
                    )}
                    {items.some(x => x.has_contradiction) && (
                      <span className="text-danger text-[10px]">⚠ зөрчил</span>
                    )}
                  </div>
                </button>

                {!isCollapsed && (
                  <div className="p-3 divide-y divide-line/40">
                    {items.map((f) => {
                      const dateLabel = formatFlexDate(f.fact_date, f.date_precision, f.fact_date_end)
                      return (
                        <div key={f.id} className="py-2.5 first:pt-1 last:pb-1 flex items-start gap-3 text-xs">
                          <span className={`w-2 h-2 rounded-full mt-1 shrink-0 ${sentimentTone(f)}`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              {dateLabel && <span className="font-mono text-accent/90 font-medium">{dateLabel}</span>}
                              {f.topic && <span className="px-1.5 py-0.2 rounded bg-surface-2 text-dim text-[10px]">{f.topic}</span>}
                              {f.has_contradiction && <Badge tone="danger">⚠ Зөрчил</Badge>}
                              <SourceProofBadge fact={f} />
                            </div>
                            <p className="text-text leading-relaxed text-xs">{f.fact_text}</p>
                            {f.source_quote && (
                              <p className="text-[11px] text-faint italic mt-1 border-l border-line-strong pl-2">
                                «{f.source_quote}»
                              </p>
                            )}
                          </div>
                          {onDeleteFact && (
                            <button
                              onClick={() => onDeleteFact(f.id)}
                              className="text-faint hover:text-danger shrink-0 p-1"
                              title="Устгах"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
