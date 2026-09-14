import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Network, Search, X, ExternalLink, AlertTriangle, FileText, Ghost } from 'lucide-react'
import { api } from '../api'
import { ENTITY_TYPES, entityType, TYPE_ORDER } from '../components/entity/EntityBadge'
import KnowledgeGraph from '../components/graph/KnowledgeGraph'
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

export default function GraphHub() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [typeFilter, setTypeFilter] = useState(new Set())
  const [onlyContradictions, setOnlyContradictions] = useState(false)
  const [hideGhosts, setHideGhosts] = useState(false)
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(null)
  const [yearBounds, setYearBounds] = useState(null) // [minYear, maxYear]
  const [yearRange, setYearRange] = useState(null) // null = бүх цаг үе

  useEffect(() => {
    api
      .getGraph()
      .then((d) => {
        setData(d)
        const years = []
        for (const n of d.nodes) {
          if (n.active_from) years.push(parseInt(n.active_from.slice(0, 4), 10))
          if (n.active_to) years.push(parseInt(n.active_to.slice(0, 4), 10))
        }
        for (const e of d.edges) {
          if (e.start_date) years.push(parseInt(e.start_date.slice(0, 4), 10))
          if (e.end_date) years.push(parseInt(e.end_date.slice(0, 4), 10))
        }
        if (years.length) {
          const [lo, hi] = [Math.min(...years), Math.max(...years)]
          setYearBounds([lo, hi])
          setYearRange([lo, hi])
        }
      })
      .catch((e) => setError(e.message))
  }, [])

  const counts = useMemo(() => {
    if (!data) return {}
    const c = {}
    for (const n of data.nodes) {
      if (n.ghost) continue
      c[n.entity_type] = (c[n.entity_type] || 0) + 1
    }
    return c
  }, [data])

  const matches = (n) => {
    if (n.ghost) {
      if (hideGhosts) return false
      if (typeFilter.size && !typeFilter.has(n.entity_type)) return false
    } else {
      if (typeFilter.size && !typeFilter.has(n.entity_type)) return false
      if (onlyContradictions && !n.has_contradiction) return false
    }
    if (query) {
      const q = query.toLowerCase()
      const hay = [n.name, ...(n.aliases || [])].join(' ').toLowerCase()
      if (!hay.includes(q)) return false
    }
    // Хугацааны шүүлт: огноотой node зөвхөн цонхтой давхцах үед
    if (yearRange && (n.active_from || n.active_to)) {
      const from = n.active_from ? parseInt(n.active_from.slice(0, 4), 10) : null
      const to = n.active_to ? parseInt(n.active_to.slice(0, 4), 10) : null
      const [y1, y2] = yearRange
      if ((from !== null && from > y2) || (to !== null && to < y1)) return false
    }
    return true
  }

  const visibleNodeIds = useMemo(() => {
    if (!data) return []
    return data.nodes.filter(matches).map((n) => n.id)
  }, [data, typeFilter, onlyContradictions, hideGhosts, query, yearRange])

  if (error)
    return (
      <GlassCard className="p-6 text-danger">
        График ачааллахад алдаа: {error}
      </GlassCard>
    )
  if (!data)
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner />
      </div>
    )

  const totalEntities = data.nodes.filter((n) => !n.ghost).length
  const contradictionCount = data.nodes.filter((n) => n.has_contradiction).length

  return (
    <div className="flex flex-col-reverse lg:flex-row gap-4 -mx-4 md:-mx-8 -my-6 md:-my-8">
      {/* ── Хяналтын panel ── */}
      <aside className="lg:w-72 shrink-0 lg:h-[calc(100vh-4rem)] overflow-y-auto p-4 md:p-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <Network size={20} className="text-accent" />
          <h1 className="font-display font-bold text-lg tracking-wide">Knowledge Graph</h1>
        </div>
        <div className="data-label">
          {totalEntities} СУБЪЕКТ · {data.edges.length} ХОЛБООС · {contradictionCount} ЗӨРЧИЛТЭЙ
        </div>

        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Хайх…"
            className="w-full glass bg-transparent pl-9 pr-8 py-2 text-sm outline-none focus:border-accent-line placeholder:text-faint"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-faint hover:text-text"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Төрлийн шүүлтүүр */}
        <div className="space-y-1.5">
          <div className="terminal-label">Шүүлтүүр</div>
          {TYPE_ORDER.filter((t) => counts[t]).map((t) => {
            const info = entityType(t)
            const active = typeFilter.has(t)
            const toggle = () => {
              const next = new Set(typeFilter)
              if (active) next.delete(t)
              else next.add(t)
              setTypeFilter(next)
            }
            return (
              <button
                key={t}
                onClick={toggle}
                className={`w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-sm border transition-all ${
                  active
                    ? 'border-accent-line bg-accent-dim text-text'
                    : 'border-transparent hover:bg-surface-2 text-dim'
                }`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ background: info.color, boxShadow: `0 0 8px ${info.color}` }}
                />
                <span className="flex-1 text-left">{info.label}</span>
                <span className="data-label">{counts[t]}</span>
              </button>
            )
          })}
        </div>

        <div className="space-y-2 pt-1">
          <label className="flex items-center gap-2.5 text-sm text-dim cursor-pointer">
            <input
              type="checkbox"
              checked={onlyContradictions}
              onChange={(e) => setOnlyContradictions(e.target.checked)}
              className="accent-[var(--color-accent)]"
            />
            <AlertTriangle size={14} className="text-warn" /> Зөвхөн зөрчилтэй
          </label>
          <label className="flex items-center gap-2.5 text-sm text-dim cursor-pointer">
            <input
              type="checkbox"
              checked={hideGhosts}
              onChange={(e) => setHideGhosts(e.target.checked)}
              className="accent-[var(--color-accent)]"
            />
            <Ghost size={14} /> Тодорхойгүй холбоос нуух
          </label>
        </div>

        {/* Хугацааны шүүлтүүр */}
        {yearBounds && (
          <div className="space-y-2 pt-1">
            <div className="flex items-center justify-between">
              <div className="terminal-label">Цаг хугацаа</div>
              <button
                onClick={() => setYearRange([...yearBounds])}
                disabled={yearRange && yearRange[0] === yearBounds[0] && yearRange[1] === yearBounds[1]}
                className="data-label hover:text-accent transition-colors disabled:opacity-30"
              >
                БҮХ ЦАГ ҮЕ
              </button>
            </div>
            <div className="font-mono text-sm text-accent text-shadow-[0_0_12px_var(--color-accent-line)]">
              {yearRange[0]} — {yearRange[1] === yearBounds[1] ? 'одоо' : yearRange[1]}
            </div>
            <div className="relative h-6">
              <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-1 bg-ink-700 rounded-full" />
              <div
                className="absolute top-1/2 -translate-y-1/2 h-1 bg-accent/40 rounded-full"
                style={{
                  left: `${((yearRange[0] - yearBounds[0]) / (yearBounds[1] - yearBounds[0])) * 100}%`,
                  right: `${100 - ((yearRange[1] - yearBounds[0]) / (yearBounds[1] - yearBounds[0])) * 100}%`,
                }}
              />
              <input
                type="range"
                min={yearBounds[0]}
                max={yearBounds[1]}
                value={yearRange[0]}
                onChange={(e) => setYearRange([Math.min(+e.target.value, yearRange[1] - 1), yearRange[1]])}
                className="absolute inset-x-0 top-0 w-full appearance-none bg-transparent pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent [&::-webkit-slider-thumb]:shadow-[0_0_10px_var(--color-accent-line)] [&::-webkit-slider-thumb]:cursor-pointer"
              />
              <input
                type="range"
                min={yearBounds[0]}
                max={yearBounds[1]}
                value={yearRange[1]}
                onChange={(e) => setYearRange([yearRange[0], Math.max(+e.target.value, yearRange[0] + 1)])}
                className="absolute inset-x-0 top-0 w-full appearance-none bg-transparent pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent [&::-webkit-slider-thumb]:shadow-[0_0_10px_var(--color-accent-line)] [&::-webkit-slider-thumb]:cursor-pointer"
              />
            </div>
            <div className="flex justify-between data-label">
              <span>{yearBounds[0]}</span>
              <span>{yearBounds[1]}</span>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="data-label space-y-1.5 pt-2 border-t border-line">
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full border border-accent" /> Фактын тоогоор хэмжээ
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full border border-dashed border-dim" /> Ghost (нэрээр л холбогдсон)
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-warn" /> Зөрчилтэй
          </div>
          <div className="pt-1 text-faint">Node чирж байрлуул · дугуйгаар томруул · дарж дэлгэрэнгүй</div>
        </div>
      </aside>

      {/* ── График + сонгосон node ── */}
      <div className="relative min-w-0 h-[70vh] shrink-0 lg:flex-1 lg:shrink lg:h-[calc(100vh-4rem)]">
        <KnowledgeGraph data={data} filteredNodeIds={visibleNodeIds} yearRange={yearRange} selectedId={selected?.id} onSelect={setSelected} />

        {selected && (
          <NodePanel node={selected} onClose={() => setSelected(null)} />
        )}
      </div>
    </div>
  )
}

function NodePanel({ node, onClose }) {
  const t = entityType(node.entity_type)
  const isGhost = !!node.ghost
  const [rels, setRels] = useState(null)

  useEffect(() => {
    if (isGhost) return
    let alive = true
    Promise.all([
      api.getEntityRelationships(node.id),
      api.getIncomingRelationships(node.id),
    ])
      .then(([out, inc]) => {
        if (!alive) return
        const items = [
          ...out.map((r) => ({
            id: `o${r.id}`,
            other: r.target_entity_id ? { id: r.target_entity_id, name: r.target_name } : null,
            label: r.rel_type,
            otherName: r.target_name,
            period: [r.start_date, r.end_date].filter(Boolean).join(' ~ '),
          })),
          ...inc.map((r) => ({
            id: `i${r.id}`,
            other: r.source_entity_id ? { id: r.source_entity_id, name: r.source_entity_name } : null,
            label: r.rel_type,
            otherName: r.source_entity_name,
            period: [r.start_date, r.end_date].filter(Boolean).join(' ~ '),
          })),
        ]
        setRels(items)
      })
      .catch(() => setRels([]))
    return () => { alive = false }
  }, [node.id, isGhost])

  return (
    <div className="absolute z-20 inset-x-0 bottom-0 lg:inset-auto lg:top-4 lg:right-4 lg:bottom-4 lg:w-96">
      <GlassCard className="glass-strong p-5 h-full max-h-[70vh] lg:max-h-none overflow-y-auto relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-faint hover:text-text transition-colors"
        >
          <X size={16} />
        </button>
        <div className="flex items-center gap-2 mb-2">
          <span
            className="w-3 h-3 rounded-full"
            style={{ background: t.color, boxShadow: `0 0 10px ${t.color}` }}
          />
          <span className="terminal-label">{t.label}{isGhost && ' · GHOST'}</span>
        </div>
        <h2 className="font-display font-bold text-lg leading-snug pr-5">{node.name}</h2>
        {node.active_from && (
          <p className="data-label mt-1">
            {node.active_from.slice(0, 4)} — {node.active_to ? node.active_to.slice(0, 4) : 'одоо'}
          </p>
        )}
        {node.tldr_summary && <p className="text-sm text-dim mt-2 leading-relaxed">{node.tldr_summary}</p>}
        {node.description && !node.tldr_summary && (
          <p className="text-sm text-dim mt-2 leading-relaxed">{node.description}</p>
        )}

        {!isGhost && (
          <div className="flex gap-4 mt-4 data-label">
            <span className="flex items-center gap-1.5">
              <FileText size={13} /> {node.fact_count} ФАКТ
            </span>
            {node.has_contradiction && (
              <span className="flex items-center gap-1.5 text-warn">
                <AlertTriangle size={13} /> ЗӨРЧИЛТЭЙ
              </span>
            )}
          </div>
        )}

        {!isGhost && node.aliases?.length > 0 && (
          <div className="mt-4">
            <div className="terminal-label mb-1.5">Хувилбарууд</div>
            <div className="flex flex-wrap gap-1.5">
              {node.aliases.map((a) => (
                <span key={a} className="text-xs text-dim glass px-2 py-0.5 rounded-md">
                  {a}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Холбоосууд */}
        {rels && rels.length > 0 && (
          <div className="mt-5">
            <div className="terminal-label mb-2">ХОЛБООСУУД ({rels.length})</div>
            <div className="space-y-1.5">
              {rels.slice(0, 12).map((r) => (
                <div key={r.id} className="text-xs glass px-2.5 py-1.5 rounded-md">
                  <div className="flex items-center gap-2 flex-wrap">
                    {r.other ? (
                      <Link to={`/entities/${r.other.id}`} className="text-accent hover:underline font-mono">
                        {r.otherName}
                      </Link>
                    ) : (
                      <span className="text-dim">{r.otherName}</span>
                    )}
                    <Badge>{r.label}</Badge>
                    {r.period && <span className="text-faint">{r.period}</span>}
                  </div>
                </div>
              ))}
              {rels.length > 12 && (
                <p className="data-label">+ {rels.length - 12} дараагийн холбоос…</p>
              )}
            </div>
          </div>
        )}

        {!isGhost && (
          <Link
            to={`/entities/${node.id}`}
            className="mt-5 inline-flex items-center gap-2 text-sm text-accent hover:text-accent-bright font-medium transition-colors"
          >
            Дэлгэрэнгүй профайл <ExternalLink size={14} />
          </Link>
        )}
      </GlassCard>
    </div>
  )
}
