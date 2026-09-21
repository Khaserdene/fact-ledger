import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Network,
  Search,
  X,
  ExternalLink,
  AlertTriangle,
  FileText,
  Ghost,
  FolderGit2,
  Filter,
  Sparkles,
  Layers,
  Calendar,
  Compass,
  Target
} from 'lucide-react'
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
  const [onlyCases, setOnlyCases] = useState(false)
  const [hideGhosts, setHideGhosts] = useState(false)
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(null)
  const [yearBounds, setYearBounds] = useState(null) // [minYear, maxYear]
  const [yearRange, setYearRange] = useState(null) // null = бүх цаг үе
  const [layoutMode, setLayoutMode] = useState('force') // 'force' | 'timeline' | 'cluster' | 'radial'

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
    if (onlyCases && !n.is_case) return false

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
  }, [data, typeFilter, onlyContradictions, onlyCases, hideGhosts, query, yearRange])

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
  const caseCount = data.nodes.filter((n) => n.is_case).length

  return (
    <div className="flex flex-col-reverse lg:flex-row gap-4 -mx-4 md:-mx-8 -my-6 md:-my-8">
      {/* ── Хяналтын panel ── */}
      <aside className="lg:w-72 shrink-0 lg:h-[calc(100vh-4rem)] overflow-y-auto p-4 md:p-6 space-y-4 bg-surface-1/40 border-r border-line/60">
        <div className="flex items-center gap-2.5">
          <Network size={20} className="text-accent" />
          <h1 className="font-display font-bold text-lg tracking-wide text-text">Knowledge Graph</h1>
        </div>
        <div className="data-label leading-relaxed">
          {totalEntities} СУБЪЕКТ · {data.edges.length} ХОЛБООС · {caseCount} МӨРДЛӨГ
        </div>

        {/* Хайлтын талбар */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Хайх (нэр, сэдэв, мөрдлөг)…"
            className="w-full glass bg-transparent pl-9 pr-8 py-2 text-sm outline-none focus:border-accent-line placeholder:text-faint rounded-lg font-mono text-text"
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

        {/* ── Онцгой горимууд (Quick Filters) ── */}
        <div className="space-y-1.5 pt-2 border-t border-line/60">
          <div className="terminal-label">Шуурхай сонголт</div>

          {/* Мөрдлөгүүдээр шүүх */}
          <button
            onClick={() => setOnlyCases(!onlyCases)}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono border transition ${
              onlyCases
                ? 'border-rose-500/60 bg-rose-500/15 text-rose-300 font-bold shadow-[0_0_12px_rgb(244_63_94/0.2)]'
                : 'border-transparent hover:bg-surface-2 text-dim'
            }`}
          >
            <span className="flex items-center gap-2">
              <FolderGit2 size={14} className={onlyCases ? 'text-rose-400' : 'text-dim'} />
              Зөвхөн Мөрдлөгүүд
            </span>
            <Badge tone={onlyCases ? 'accent' : 'neutral'}>{caseCount}</Badge>
          </button>

          {/* Зөрчлүүд */}
          <button
            onClick={() => setOnlyContradictions(!onlyContradictions)}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono border transition ${
              onlyContradictions
                ? 'border-warn-line bg-warn-dim text-warn font-bold'
                : 'border-transparent hover:bg-surface-2 text-dim'
            }`}
          >
            <span className="flex items-center gap-2">
              <AlertTriangle size={14} className={onlyContradictions ? 'text-warn' : 'text-dim'} />
              Зөрчилтэй мэдээллүүд
            </span>
            <Badge tone={onlyContradictions ? 'warn' : 'neutral'}>{contradictionCount}</Badge>
          </button>
        </div>

        {/* Төрлийн шүүлтүүр */}
        <div className="space-y-1.5 pt-2 border-t border-line/60">
          <div className="flex items-center justify-between">
            <span className="terminal-label">Төрлөөр шүүх</span>
            {typeFilter.size > 0 && (
              <button
                onClick={() => setTypeFilter(new Set())}
                className="text-[10px] font-mono text-accent hover:underline"
              >
                Бүгдийг сонгох
              </button>
            )}
          </div>
          <div className="max-h-56 overflow-y-auto space-y-1 pr-1">
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
                  className={`w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs font-mono border transition-all ${
                    active
                      ? 'border-accent-line bg-accent-dim text-text font-bold'
                      : 'border-transparent hover:bg-surface-2 text-dim'
                  }`}
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: info.color, boxShadow: `0 0 8px ${info.color}` }}
                  />
                  <span className="flex-1 text-left truncate">{info.label}</span>
                  <span className="data-label">{counts[t]}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Цаг хугацааны цонх */}
        {yearBounds && (
          <div className="space-y-2 pt-2 border-t border-line/60">
            <div className="flex items-center justify-between">
              <span className="terminal-label">Он цагийн интервал</span>
              <button
                onClick={() => setYearRange([...yearBounds])}
                disabled={yearRange && yearRange[0] === yearBounds[0] && yearRange[1] === yearBounds[1]}
                className="data-label hover:text-accent transition-colors disabled:opacity-30 text-[10px]"
              >
                БҮХ ЦАГ ҮЕ
              </button>
            </div>
            <div className="font-mono text-xs text-accent">
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
                className="absolute inset-x-0 top-0 w-full appearance-none bg-transparent pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent [&::-webkit-slider-thumb]:cursor-pointer"
              />
              <input
                type="range"
                min={yearBounds[0]}
                max={yearBounds[1]}
                value={yearRange[1]}
                onChange={(e) => setYearRange([yearRange[0], Math.max(+e.target.value, yearRange[0] + 1)])}
                className="absolute inset-x-0 top-0 w-full appearance-none bg-transparent pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent [&::-webkit-slider-thumb]:cursor-pointer"
              />
            </div>
            <div className="flex justify-between data-label text-[10px]">
              <span>{yearBounds[0]}</span>
              <span>{yearBounds[1]}</span>
            </div>
          </div>
        )}

        {/* Тайлбар тэмдэглэгээ (Legend) */}
        <div className="data-label space-y-1.5 pt-2 border-t border-line/60 text-[10px]">
          <div className="flex items-center gap-2 text-rose-400 font-bold">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" /> ★ Мөрдлөг / Case Hub
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full border border-accent" /> Фактын тоогоор хэмжээ
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full border border-dashed border-dim" /> Ghost (нэрээр холбогдсон)
          </div>
          <div className="flex items-center gap-2 text-warn">
            <span className="inline-block w-2 h-2 rounded-full bg-warn" /> Зөрчилтэй
          </div>
        </div>
      </aside>

      {/* ── График + сонгосон node ── */}
      <div className="relative min-w-0 h-[75vh] shrink-0 lg:flex-1 lg:shrink lg:h-[calc(100vh-4rem)]">
        <KnowledgeGraph
          data={data}
          filteredNodeIds={visibleNodeIds}
          yearRange={yearRange}
          selectedId={selected?.id}
          onSelect={setSelected}
          layoutMode={layoutMode}
          onLayoutChange={setLayoutMode}
        />

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
  const isCase = !!node.is_case
  const [rels, setRels] = useState(null)
  const [facts, setFacts] = useState(null)
  const [loadingProfile, setLoadingProfile] = useState(false)

  useEffect(() => {
    if (isGhost || isCase) return
    let alive = true
    setLoadingProfile(true)

    Promise.all([
      api.getEntityRelationships(node.id),
      api.getIncomingRelationships(node.id),
      api.getEntityFacts(node.id)
    ])
      .then(([out, inc, factData]) => {
        if (!alive) return
        const items = [
          ...out.map((r) => ({
            id: `o${r.id}`,
            other: r.target_entity_id ? { id: r.target_entity_id, name: r.target_name } : null,
            label: r.rel_type,
            otherName: r.target_name,
            period: [r.start_date, r.end_date].filter(Boolean).map((d) => d.slice(0, 4)).join(' ~ '),
          })),
          ...inc.map((r) => ({
            id: `i${r.id}`,
            other: r.source_entity_id ? { id: r.source_entity_id, name: r.source_entity_name } : null,
            label: r.rel_type,
            otherName: r.source_entity_name,
            period: [r.start_date, r.end_date].filter(Boolean).map((d) => d.slice(0, 4)).join(' ~ '),
          })),
        ]
        setRels(items)
        setFacts(factData)
      })
      .catch(() => {
        if (alive) {
          setRels([])
          setFacts([])
        }
      })
      .finally(() => {
        if (alive) setLoadingProfile(false)
      })

    return () => { alive = false }
  }, [node.id, isGhost, isCase])

  return (
    <div
      className="absolute z-20 inset-x-0 bottom-0 lg:inset-auto lg:top-4 lg:right-4 lg:bottom-4 lg:w-[420px]"
      onClick={(e) => e.stopPropagation()}
    >
      <GlassCard className="glass-strong p-5 h-full max-h-[80vh] lg:max-h-none overflow-y-auto relative border-accent/30 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-1 text-faint hover:text-text rounded-md hover:bg-surface-2 transition-colors"
        >
          <X size={18} />
        </button>

        {/* ── Төлөв & Нэр ── */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className="w-3 h-3 rounded-full shrink-0"
            style={{ background: isCase ? '#f43f5e' : t.color, boxShadow: `0 0 10px ${isCase ? '#f43f5e' : t.color}` }}
          />
          <span className="terminal-label">
            {isCase ? '★ МӨРДЛӨГИЙН ДЭД-ГРАФ' : t.label}
            {isGhost && ' · GHOST'}
          </span>
          {isCase && <Badge tone="warn">{node.status || 'PUBLISHED'}</Badge>}
        </div>

        <h2 className="font-display font-bold text-xl leading-snug pr-6 text-text">{node.name}</h2>

        {node.active_from && (
          <p className="data-label mt-1 text-accent">
            {node.active_from.slice(0, 4)} — {node.active_to ? node.active_to.slice(0, 4) : 'одоо'}
          </p>
        )}

        {/* ── Дэлгэрэнгүй товч тайлбар ── */}
        {node.tldr_summary && (
          <div className="mt-3 p-2.5 rounded-lg bg-surface-2/60 border border-line/40 text-xs text-dim leading-relaxed">
            <span className="font-mono text-[10px] text-accent font-bold uppercase block mb-1">Товч хураангуй</span>
            {node.tldr_summary}
          </div>
        )}
        {node.description && !node.tldr_summary && (
          <p className="text-sm text-dim mt-2 leading-relaxed">{node.description}</p>
        )}

        {/* Хэрэв Case Node бол шууд Case Editor руу очих товч */}
        {isCase && (
          <div className="mt-4 p-3 bg-surface-2 border border-line rounded-lg space-y-3">
            <div className="text-xs font-mono text-dim flex items-center gap-2">
              <FolderGit2 size={16} className="text-accent" />
              <span>Тусгай мөрдлөгийн дэд-граф болон цаг хугацааны тоглуулагч</span>
            </div>
            <Link
              to={`/cases/${node.slug}`}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-accent text-ink-950 font-bold font-mono text-xs hover:bg-accent/90 transition shadow-[0_0_12px_rgb(56_224_255/0.25)]"
            >
              <span>Мөрдлөгийн Canvas нээх</span>
              <ExternalLink size={14} />
            </Link>
          </div>
        )}

        {!isGhost && !isCase && (
          <div className="flex gap-4 mt-3 data-label border-y border-line/40 py-2">
            <span className="flex items-center gap-1.5 text-text">
              <FileText size={13} className="text-accent" /> {facts ? facts.length : node.fact_count} ФАКТ
            </span>
            {node.has_contradiction && (
              <span className="flex items-center gap-1.5 text-warn font-semibold">
                <AlertTriangle size={13} /> ЗӨРЧИЛТЭЙ
              </span>
            )}
          </div>
        )}

        {/* ── Холбоосууд ── */}
        {rels && rels.length > 0 && (
          <div className="mt-4">
            <div className="terminal-label mb-1.5 text-accent">Бүх Холбоосууд ({rels.length})</div>
            <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {rels.map((r) => (
                <div key={r.id} className="text-xs glass px-2.5 py-1.5 rounded flex items-center justify-between border border-line/30">
                  <div className="flex items-center gap-1.5 truncate">
                    {r.other ? (
                      <Link to={`/entities/${r.other.id}`} className="text-accent hover:underline font-medium">
                        {r.otherName}
                      </Link>
                    ) : (
                      <span className="text-dim">{r.otherName}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Badge>{r.label}</Badge>
                    {r.period && <span className="text-[10px] text-faint font-mono">{r.period}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!isGhost && !isCase && (
          <div className="mt-5 pt-3 border-t border-line/50 flex items-center justify-between">
            <Link
              to={`/entities/${node.id}`}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-accent/15 border border-accent/40 text-accent hover:bg-accent hover:text-ink-950 font-medium text-sm transition-all font-mono"
            >
              <span>Бүтэн профайл руу очих</span>
              <ExternalLink size={15} />
            </Link>
          </div>
        )}
      </GlassCard>
    </div>
  )
}
