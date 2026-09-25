import React, { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  Grid3X3,
  Search,
  Filter,
  Users,
  ShieldAlert,
  Layers,
  ArrowUpDown,
  ExternalLink,
  ChevronRight,
  Info,
  X
} from 'lucide-react'
import GlassCard from '../ui/GlassCard'

const ROLE_COLORS = {
  SUSPECT: {
    bg: 'bg-rose-500/20',
    border: 'border-rose-500/60',
    text: 'text-rose-400',
    dot: 'bg-rose-500',
    badge: 'Сэжигтэн / Яллагдагч'
  },
  BENEFICIARY: {
    bg: 'bg-amber-500/20',
    border: 'border-amber-500/60',
    text: 'text-amber-400',
    dot: 'bg-amber-500',
    badge: 'Ашиг хүртэгч / Компани'
  },
  DECISION_MAKER: {
    bg: 'bg-sky-500/20',
    border: 'border-sky-500/60',
    text: 'text-sky-400',
    dot: 'bg-sky-500',
    badge: 'Шийдвэр гаргагч / Албан тушаалтан'
  },
  INVOLVED_IN: {
    bg: 'bg-violet-500/20',
    border: 'border-violet-500/60',
    text: 'text-violet-400',
    dot: 'bg-violet-500',
    badge: 'Холбогдогч / Гэрч'
  }
}

export default function CrossCaseMatrix({ data }) {
  const [searchEntity, setSearchEntity] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [selectedCell, setSelectedCell] = useState(null)
  const [activeCategory, setActiveCategory] = useState('ALL')

  const cases = useMemo(() => {
    if (!data?.cases_summary) return []
    if (activeCategory === 'ALL') return data.cases_summary
    return data.cases_summary.filter(c => (c.category || 'scandal') === activeCategory)
  }, [data, activeCategory])

  const matrixEntities = useMemo(() => {
    if (!data?.matrix_entities) return []
    return data.matrix_entities.filter(ent => {
      if (typeFilter !== 'ALL' && ent.entity_type !== typeFilter) return false
      if (searchEntity.trim()) {
        const query = searchEntity.toLowerCase()
        return ent.name.toLowerCase().includes(query)
      }
      return true
    })
  }, [data, searchEntity, typeFilter])

  const [matrixViewMode, setMatrixViewMode] = useState('matrix') // 'matrix' | 'cartels'

  const cartels = useMemo(() => {
    return data?.procurement_cartels || []
  }, [data])

  return (
    <div className="space-y-4">
      {/* Top Controls */}
      <GlassCard className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 border-line">
        <div className="flex flex-wrap items-center gap-3">
          {/* Sub-view switcher */}
          <div className="flex items-center p-0.5 bg-surface-1 border border-line rounded">
            <button
              onClick={() => setMatrixViewMode('matrix')}
              className={`px-3 py-1.5 rounded text-xs font-mono transition ${
                matrixViewMode === 'matrix'
                  ? 'bg-accent/20 text-accent font-bold border border-accent/40'
                  : 'text-dim hover:text-text'
              }`}
            >
              МАТРИЦ ({matrixEntities.length})
            </button>
            <button
              onClick={() => setMatrixViewMode('cartels')}
              className={`px-3 py-1.5 rounded text-xs font-mono transition flex items-center gap-1.5 ${
                matrixViewMode === 'cartels'
                  ? 'bg-rose-500/20 text-rose-300 font-bold border border-rose-500/40'
                  : 'text-dim hover:text-text'
              }`}
            >
              <ShieldAlert size={13} className="text-rose-400" />
              <span>ТЕНДЕР & ОФФТЕЙК ЗАНГИЛАА ({cartels.length})</span>
            </button>
          </div>

          {matrixViewMode === 'matrix' && (
            <>
              {/* Search */}
              <div className="relative w-56">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-dim" size={14} />
                <input
                  type="text"
                  placeholder="Субъект хайх..."
                  value={searchEntity}
                  onChange={(e) => setSearchEntity(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-surface-2 border border-line rounded text-xs text-text font-mono placeholder:text-faint focus:border-accent focus:outline-none"
                />
              </div>

              {/* Type Filter */}
              <div className="flex items-center gap-1 bg-surface-2 p-1 border border-line rounded">
                {['ALL', 'PERSON', 'COMPANY'].map(t => (
                  <button
                    key={t}
                    onClick={() => setTypeFilter(t)}
                    className={`px-2.5 py-1 text-[11px] font-mono rounded transition ${
                      typeFilter === t
                        ? 'bg-accent/20 text-accent font-bold border border-accent/40'
                        : 'text-dim hover:text-text'
                    }`}
                  >
                    {t === 'ALL' ? 'Бүх' : t === 'PERSON' ? 'Хүн' : 'Байгууллага'}
                  </button>
                ))}
              </div>

              {/* Category Filter */}
              <select
                value={activeCategory}
                onChange={(e) => setActiveCategory(e.target.value)}
                className="bg-surface-2 border border-line text-xs font-mono text-text px-3 py-1.5 rounded focus:border-accent focus:outline-none"
              >
                <option value="ALL">Бүх 29 хэрэг</option>
                <option value="scandal">🚨 Авлига & Дуулиант</option>
                <option value="crisis">⚡ Засаглалын хямрал</option>
                <option value="megaproject">🏗️ Мега төсөл & Хувьчлал</option>
                <option value="faction">🌐 Фракц & Оффшор</option>
                <option value="procurement">💰 Сан & Худалдан авалт</option>
              </select>
            </>
          )}
        </div>

        {/* Legend */}
        {matrixViewMode === 'matrix' && (
          <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono">
            <span className="text-dim mr-1">Тайлбар:</span>
            {Object.entries(ROLE_COLORS).map(([key, style]) => (
              <div key={key} className="flex items-center gap-1 bg-surface-2 px-2 py-0.5 rounded border border-line">
                <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                <span className={style.text}>{style.badge}</span>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Cartel Cards View */}
      {matrixViewMode === 'cartels' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {cartels.map((c) => (
            <GlassCard key={c.id} className="p-4 border-line space-y-2.5 hover:border-rose-500/40 transition">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${
                    c.risk_score >= 80
                      ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                      : c.risk_score >= 60
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      : 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                  }`}>
                    ЭРСДЭЛ {c.risk_score}%
                  </span>
                  <span className="text-[11px] font-mono text-dim">
                    {c.rel_type}
                  </span>
                </div>
                {c.shared_cases_count > 0 && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30">
                    {c.shared_cases_count} хэрэгт хамт
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between gap-2 p-2.5 rounded bg-surface-2/60 border border-line font-mono text-xs">
                <div className="truncate">
                  <span className="text-[10px] text-dim block">Субъект 1 ({c.source_entity.type}):</span>
                  <span className="font-bold text-text truncate">{c.source_entity.name}</span>
                </div>
                <ArrowUpDown size={14} className="text-accent shrink-0 rotate-90" />
                <div className="truncate text-right">
                  <span className="text-[10px] text-dim block">Субъект 2 ({c.target_entity.type}):</span>
                  <span className="font-bold text-text truncate">{c.target_entity.name}</span>
                </div>
              </div>

              {c.shared_cases.length > 0 && (
                <div className="text-[11px] font-mono text-dim flex items-center gap-1.5 flex-wrap">
                  <span className="text-faint">Огтлолцсон:</span>
                  {c.shared_cases.map((title, i) => (
                    <span key={i} className="px-1.5 py-0.5 bg-surface-2 rounded text-text text-[10px] border border-line">
                      {title}
                    </span>
                  ))}
                </div>
              )}

              {c.source_quote && (
                <p className="text-[11px] font-mono text-text/80 italic bg-surface-1 p-2 rounded border border-line/40 line-clamp-2">
                  "{c.source_quote}"
                </p>
              )}
            </GlassCard>
          ))}
        </div>
      )}

      {/* Heatmap Matrix View */}
      {matrixViewMode === 'matrix' && (
        <div className="relative border border-line rounded-lg bg-surface-1 overflow-hidden">
        <div className="overflow-x-auto max-h-[640px] overflow-y-auto scrollbar-thin">
          <table className="w-full border-collapse text-left text-xs font-mono">
            {/* Header Row (Cases) */}
            <thead className="sticky top-0 z-20 bg-surface-1/95 backdrop-blur shadow-sm border-b border-line">
              <tr>
                <th className="sticky left-0 z-30 bg-surface-1 p-3 min-w-[200px] border-r border-line font-bold text-text">
                  <div className="flex items-center justify-between">
                    <span>СУБЪЕКТ ({matrixEntities.length})</span>
                    <span className="text-[10px] text-accent">Хэрэг #</span>
                  </div>
                </th>
                {cases.map((c) => (
                  <th
                    key={c.id}
                    title={c.title}
                    className="p-2 min-w-[140px] max-w-[160px] text-center border-r border-line/40 align-bottom group"
                  >
                    <Link
                      to={`/cases/${c.slug}`}
                      className="flex flex-col items-center gap-1 hover:text-accent transition"
                    >
                      <span className="text-[10px] text-dim group-hover:text-accent font-semibold line-clamp-2">
                        {c.title}
                      </span>
                      <div className="flex items-center gap-1">
                        {c.amount_billion ? (
                          <span className="text-[9px] px-1.5 py-0.5 bg-rose-500/15 border border-rose-500/30 rounded text-rose-400 font-bold whitespace-nowrap">
                            {c.amount_billion >= 1000 
                              ? `${(c.amount_billion / 1000).toFixed(1)} Их наяд ₮` 
                              : `${c.amount_billion} Тэрбум ₮`}
                          </span>
                        ) : null}
                        <span className="text-[9px] px-1.5 py-0.5 bg-surface-2 rounded text-faint group-hover:text-accent">
                          {c.links_count} холбоос
                        </span>
                      </div>
                    </Link>
                  </th>
                ))}
              </tr>
            </thead>

            {/* Body Rows (Entities) */}
            <tbody>
              {matrixEntities.map((ent, idx) => {
                const isEven = idx % 2 === 0
                return (
                  <tr
                    key={ent.id}
                    className={`border-b border-line/30 transition hover:bg-surface-2/60 ${
                      isEven ? 'bg-surface-1/40' : 'bg-surface-1/10'
                    }`}
                  >
                    {/* Entity Name (Sticky Left Column) */}
                    <td className="sticky left-0 z-10 bg-surface-1 p-2.5 border-r border-line font-medium text-text flex items-center justify-between gap-2 shadow-[2px_0_5px_rgba(0,0,0,0.3)]">
                      <div className="flex items-center gap-1.5 truncate">
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            ent.entity_type === 'PERSON' ? 'bg-cyan-400' : 'bg-purple-400'
                          }`}
                        />
                        <span className="truncate hover:text-accent cursor-pointer" title={ent.name}>
                          {ent.name}
                        </span>
                      </div>
                      <span
                        className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                          ent.case_count >= 3
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : ent.case_count === 2
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                            : 'bg-surface-2 text-dim'
                        }`}
                        title={`${ent.case_count} хэрэгт холбогдсон`}
                      >
                        {ent.case_count}
                      </span>
                    </td>

                    {/* Case Cells */}
                    {cases.map((c) => {
                      const linkData = ent.cases[String(c.id)]
                      if (!linkData) {
                        return (
                          <td
                            key={c.id}
                            className="p-2 text-center border-r border-line/20 text-faint"
                          >
                            <span className="text-[10px] opacity-10">·</span>
                          </td>
                        )
                      }

                      const roleStyle = ROLE_COLORS[linkData.role] || {
                        bg: 'bg-surface-2',
                        border: 'border-line',
                        text: 'text-dim',
                        dot: 'bg-dim',
                        badge: linkData.role
                      }

                      return (
                        <td
                          key={c.id}
                          onClick={() =>
                            setSelectedCell({
                              entity: ent,
                              caseItem: c,
                              linkData: linkData,
                              roleStyle: roleStyle
                            })
                          }
                          className="p-1.5 text-center border-r border-line/20 cursor-pointer"
                        >
                          <div
                            className={`p-1 rounded border text-[10px] font-bold transition transform hover:scale-105 ${roleStyle.bg} ${roleStyle.border} ${roleStyle.text} shadow-sm`}
                            title={`${ent.name} -> ${c.title} (${roleStyle.badge})`}
                          >
                            <div className="truncate">
                              {linkData.role === 'SUSPECT'
                                ? 'СЭЖИГТЭН'
                                : linkData.role === 'BENEFICIARY'
                                ? 'АШИГ'
                                : linkData.role === 'DECISION_MAKER'
                                ? 'ШИЙДВЭР'
                                : 'ХОЛБОГДОГЧ'}
                            </div>
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Selected Cell Detail Drawer / Modal */}
      {selectedCell && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-surface-1 border border-line rounded-lg shadow-2xl p-5 relative space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-start justify-between border-b border-line pb-3">
              <div>
                <span className="text-[10px] font-mono text-accent uppercase tracking-wider">
                  Матрицын нарийвчилсан мэдээлэл
                </span>
                <h3 className="font-bold text-text font-display text-base mt-0.5">
                  {selectedCell.entity.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedCell(null)}
                className="text-dim hover:text-text font-mono text-sm p-1 rounded hover:bg-surface-2"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 rounded bg-surface-2/60 border border-line space-y-1">
                <div className="text-[10px] text-dim">ХОЛБОГДСОН МӨРДЛӨГИЙН ХЭРЭГ:</div>
                <div className="font-bold text-text text-sm">
                  {selectedCell.caseItem.title}
                </div>
                <div className="text-dim text-[11px]">
                  Ангилал: {selectedCell.caseItem.category || 'scandal'}
                </div>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-surface-2/40 border border-line">
                <span className="text-dim">Гүйцэтгэсэн үүрэг:</span>
                <span
                  className={`px-2 py-0.5 rounded border text-[11px] font-bold ${selectedCell.roleStyle.bg} ${selectedCell.roleStyle.border} ${selectedCell.roleStyle.text}`}
                >
                  {selectedCell.roleStyle.badge}
                </span>
              </div>

              {selectedCell.linkData.note && (
                <div className="p-3 rounded bg-surface-2/40 border border-line space-y-1">
                  <div className="text-[10px] text-dim">ХОЛБОГДСОН ҮНДЭСЛЭЛ / ТАЙЛБАР:</div>
                  <p className="text-text/90 leading-relaxed">
                    {selectedCell.linkData.note}
                  </p>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-line">
              <Link
                to={`/cases/${selectedCell.caseItem.slug}`}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-accent/15 border border-accent/40 rounded text-accent hover:bg-accent/25 text-xs font-mono transition"
              >
                <span>Хэргийн Canvas руу үсрэх</span>
                <ExternalLink size={13} />
              </Link>
              <button
                onClick={() => setSelectedCell(null)}
                className="px-3 py-1.5 bg-surface-2 text-dim hover:text-text rounded text-xs font-mono"
              >
                Хаах
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
