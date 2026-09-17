import { useEffect, useMemo, useRef, useState } from 'react'
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
} from 'd3-force'
import { select } from 'd3-selection'
import { zoom as d3zoom } from 'd3-zoom'
import { entityType } from '../entity/EntityBadge'

const TICKS = 320

/**
 * d3-force + SVG knowledge graph.
 * Статик layout: simulation-ийг sync ажиллуулаад дараа нь zoom/pan/drag хийнэ.
 * Шүүлт (filteredNodeIds, yearRange) зөвхөн render түвшинд хийгдэнэ —
 * node-ийн байрлал хадгалагдаж, slider шүүрэхэд график хөдөлөхгүй.
 */
export default function KnowledgeGraph({ data, filteredNodeIds, yearRange, selectedId, onSelect }) {
  const wrapRef = useRef(null)
  const svgRef = useRef(null)
  const simNodes = useRef([])
  const simEdges = useRef([])
  const [size, setSize] = useState({ w: 800, h: 600 })
  const [, forceRender] = useState(0)
  const [hoverId, setHoverId] = useState(null)
  const dragRef = useRef(null)

  // Контейнерийн хэмжээг ажиглана (responsive)
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setSize({ w: Math.max(width, 100), h: Math.max(height, 100) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const nodeById = useMemo(() => {
    const m = new Map()
    for (const n of simNodes.current) m.set(n.id, n)
    return m
  }, [data])

  // Simulation: өгөгдөл өөрчлөгдөх бүрд дахин бүтээнэ (шүүлтөөс үл хамааран БҮХ node)
  useEffect(() => {
    if (!data) return
    const nodes = data.nodes.map((n, i) => ({ ...n, x: null, y: null, idx: i }))
    const idSet = new Set(nodes.map((n) => n.id))
    const links = data.edges
      .filter((e) => idSet.has(e.source) && idSet.has(e.target))
      .map((e) => ({ ...e }))
    simNodes.current = nodes
    simEdges.current = links

    const sim = forceSimulation(nodes)
      .force(
        'link',
        forceLink(links).id((d) => d.id).distance(90).strength(0.5)
      )
      .force('charge', forceManyBody().strength(-220))
      .force('collide', forceCollide().radius((d) => nodeRadius(d) + 14))
      .force('x', forceX(size.w / 2).strength(0.04))
      .force('y', forceY(size.h / 2).strength(0.06))
      .force('center', forceCenter(size.w / 2, size.h / 2).strength(0.05))
      .stop()
    for (let i = 0; i < TICKS; i++) sim.tick()
    forceRender((v) => v + 1)

    return () => sim.stop()
  }, [data, size.w, size.h])

  // Zoom / pan
  useEffect(() => {
    const svg = select(svgRef.current)
    const behavior = d3zoom()
      .scaleExtent([0.25, 4])
      .on('zoom', (event) => {
        select(svgRef.current.querySelector('g.viewport')).attr(
          'transform',
          event.transform.toString()
        )
      })
    svg.call(behavior).on('dblclick.zoom', null)
    return () => {
      svg.on('.zoom', null)
    }
  }, [])

  function nodeRadius(d) {
    if (d.ghost) return 5
    return 7 + Math.sqrt(d.fact_count || 0) * 2.2
  }

  function startDrag(event, d) {
    event.stopPropagation()
    const pt = svgPoint(event)
    dragRef.current = { id: d.id, dx: d.x - pt.x, dy: d.y - pt.y, moved: false }
    window.addEventListener('pointermove', onDragMove)
    window.addEventListener('pointerup', onDragEnd)
  }
  function onDragMove(event) {
    const st = dragRef.current
    if (!st) return
    const d = simNodes.current.find((n) => n.id === st.id)
    if (!d) return
    const pt = svgPoint(event)
    d.x = pt.x + st.dx
    d.y = pt.y + st.dy
    st.moved = true
    forceRender((v) => v + 1)
  }
  function onDragEnd(event) {
    const st = dragRef.current
    dragRef.current = null
    window.removeEventListener('pointermove', onDragMove)
    window.removeEventListener('pointerup', onDragEnd)
    if (st && !st.moved && onSelect) {
      const d = simNodes.current.find((n) => n.id === st.id)
      if (d) onSelect(d)
    }
  }
  function svgPoint(event) {
    const svg = svgRef.current
    const rect = svg.getBoundingClientRect()
    const viewport = svg.querySelector('g.viewport')
    const ctm = viewport && viewport.getCTM()
    const px = event.clientX - rect.left
    const py = event.clientY - rect.top
    if (ctm) {
      const inv = ctm.inverse()
      return {
        x: inv.a * px + inv.c * py + inv.e,
        y: inv.b * px + inv.d * py + inv.f,
      }
    }
    return { x: px, y: py }
  }

  const neighborIds = useMemo(() => {
    if (!hoverId && !selectedId) return null
    const focus = hoverId || selectedId
    const s = new Set([focus])
    for (const e of simEdges.current) {
      if (e.source === focus) s.add(typeof e.target === 'object' ? e.target.id : e.target)
      if ((typeof e.target === 'object' ? e.target.id : e.target) === focus) s.add(e.source)
    }
    return s
  }, [hoverId, selectedId])

  const nodes = simNodes.current
  const links = simEdges.current
  const labelLimit = nodes.length <= 60 || hoverId || selectedId

  const yearOf = (iso) => (iso ? parseInt(iso.slice(0, 4), 10) : null)
  function overlapsRange(fromIso, toIso) {
    if (!yearRange) return true
    const [y1, y2] = yearRange
    const from = yearOf(fromIso)
    const to = yearOf(toIso)
    if (from === null && to === null) return true // хугацаагүй = үргэлж идэвхтэй
    return (from === null || from <= y2) && (to === null || to >= y1)
  }
  const nodeVisible = (d) =>
    (!filteredNodeIds || filteredNodeIds.includes(d.id)) && overlapsRange(d.active_from, d.active_to)
  const edgeVisible = (e) => {
    const s = typeof e.source === 'object' ? e.source : nodeById.get(e.source)
    const t = typeof e.target === 'object' ? e.target : nodeById.get(e.target)
    if (!s || !t) return false
    if (!nodeVisible(s) || !nodeVisible(t)) return false
    return overlapsRange(e.start_date, e.end_date)
  }

  // Hover хийсэн node болон түүний шууд холбоостой хөршүүдийн мэдээллийг бэлтгэнэ
  const hoverInfo = useMemo(() => {
    if (!hoverId) return null
    const targetNode = nodeById.get(hoverId)
    if (!targetNode) return null

    const connections = []
    for (const e of links) {
      if (!edgeVisible(e)) continue
      const s = typeof e.source === 'object' ? e.source : nodeById.get(e.source)
      const t = typeof e.target === 'object' ? e.target : nodeById.get(e.target)
      if (!s || !t) continue

      if (s.id === hoverId) {
        connections.push({
          id: e.id,
          other: t,
          rel: e.label || 'холбоотой',
          direction: 'out',
          period: [e.start_date, e.end_date].filter(Boolean).map((d) => d.slice(0, 4)).join(' ~ ')
        })
      } else if (t.id === hoverId) {
        connections.push({
          id: e.id,
          other: s,
          rel: e.label || 'холбоотой',
          direction: 'in',
          period: [e.start_date, e.end_date].filter(Boolean).map((d) => d.slice(0, 4)).join(' ~ ')
        })
      }
    }

    return {
      node: targetNode,
      connections
    }
  }, [hoverId, links, nodeById, filteredNodeIds, yearRange])

  return (
    <div ref={wrapRef} className="w-full h-full overflow-hidden relative">
      {/* ── Hover хийх үед гарах Холбоосын Товч Карточка (Hover Tooltip Card) ── */}
      {hoverInfo && (
        <div className="absolute top-4 left-4 z-10 max-w-sm pointer-events-none transition-all duration-200">
          <div className="glass-strong p-3.5 rounded-xl border border-accent/30 shadow-2xl backdrop-blur-md bg-ink-950/85">
            <div className="flex items-center gap-2 mb-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{
                  background: entityType(hoverInfo.node.entity_type).color,
                  boxShadow: `0 0 8px ${entityType(hoverInfo.node.entity_type).color}`
                }}
              />
              <span className="font-display font-bold text-sm text-text truncate">
                {hoverInfo.node.name}
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-surface-2 text-faint ml-auto">
                {entityType(hoverInfo.node.entity_type).label}
              </span>
            </div>

            <div className="text-xs text-accent font-medium mb-2 border-b border-line/50 pb-1 flex items-center justify-between">
              <span>Холбоотой субъектууд ({hoverInfo.connections.length})</span>
              {hoverInfo.node.fact_count > 0 && (
                <span className="text-faint font-normal">{hoverInfo.node.fact_count} факт</span>
              )}
            </div>

            {hoverInfo.connections.length === 0 ? (
              <div className="text-xs text-faint italic py-1">Шууд холбоотой субъект одоогоор алга</div>
            ) : (
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {hoverInfo.connections.slice(0, 8).map((c) => (
                  <div key={c.id} className="flex items-center justify-between gap-2 text-xs bg-ink-900/60 px-2 py-1 rounded border border-line/30">
                    <div className="flex items-center gap-1.5 truncate">
                      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: entityType(c.other.entity_type).color }} />
                      <span className="font-medium text-text truncate">{c.other.name}</span>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <span className="text-[10px] text-accent bg-accent/10 px-1.5 py-0.5 rounded border border-accent/20">
                        {c.rel}
                      </span>
                      {c.period && <span className="text-[10px] text-faint font-mono">{c.period}</span>}
                    </div>
                  </div>
                ))}
                {hoverInfo.connections.length > 8 && (
                  <div className="text-[10px] text-center text-faint pt-1">
                    + цаана нь {hoverInfo.connections.length - 8} холбоос байна
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <svg ref={svgRef} width="100%" height="100%" className="touch-none select-none">
        <defs>
          <radialGradient id="nodeGlow">
            <stop offset="0%" stopColor="rgb(56 224 255 / 0.35)" />
            <stop offset="100%" stopColor="rgb(56 224 255 / 0)" />
          </radialGradient>
        </defs>
        <g className="viewport">
          {links.filter(edgeVisible).map((e) => {
            const s = typeof e.source === 'object' ? e.source : nodeById.get(e.source)
            const t = typeof e.target === 'object' ? e.target : nodeById.get(e.target)
            if (!s || !t) return null
            const focus = !neighborIds || (neighborIds.has(s.id) && neighborIds.has(t.id))
            const isHoverEdge = hoverId && (s.id === hoverId || t.id === hoverId)
            const isSelEdge = selectedId && (s.id === selectedId || t.id === selectedId)
            const hot = isHoverEdge || isSelEdge
            
            // Сонгосон эсвэл hover хийсэн субъектийн эсрэг талын субъектийн өнгийг эжид олгоно
            const focusNode = hoverId ? nodeById.get(hoverId) : (selectedId ? nodeById.get(selectedId) : null)
            const otherNode = focusNode ? (s.id === focusNode.id ? t : s) : t
            const targetColor = entityType(otherNode.entity_type).color

            const midX = (s.x + t.x) / 2
            const midY = (s.y + t.y) / 2

            return (
              <g key={e.id}>
                {/* Арын зөөлөн гэрэлтэлт (glow effect for active edges) */}
                {hot && (
                  <line
                    x1={s.x}
                    y1={s.y}
                    x2={t.x}
                    y2={t.y}
                    stroke={targetColor}
                    strokeWidth={6}
                    opacity={0.3}
                  />
                )}
                <line
                  className={`graph-edge ${t.ghost ? 'ghost' : ''}`}
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke={hot ? targetColor : (t.ghost ? 'var(--color-ink-700)' : entityType(t.entity_type).color)}
                  strokeWidth={hot ? 2.5 : 1.2}
                  strokeDasharray={hot ? '5 4' : undefined}
                  opacity={focus ? (hot ? 1 : 0.45) : 0.04}
                />
                {/* Hover эсвэл Select хийсэн үед edge дээрх харилцааны нэрийг тухайн холбогдсон субъектийн өнгөөр ялгаж харуулах */}
                {hot && e.label && (
                  <g transform={`translate(${midX}, ${midY})`}>
                    <rect
                      x="-38"
                      y="-11"
                      width="76"
                      height="20"
                      rx="6"
                      fill="var(--color-ink-950)"
                      stroke={targetColor}
                      strokeWidth="1.2"
                      opacity="0.95"
                    />
                    <text
                      textAnchor="middle"
                      y="3"
                      fill={targetColor}
                      fontSize="10"
                      fontWeight="bold"
                      fontFamily="var(--font-mono)"
                    >
                      {e.label.length > 10 ? e.label.slice(0, 9) + '…' : e.label}
                    </text>
                  </g>
                )}
              </g>
            )
          })}
          {nodes.filter(nodeVisible).map((d) => {
            const t = entityType(d.entity_type)
            const r = nodeRadius(d)
            const dimmed = neighborIds && !neighborIds.has(d.id)
            const isSel = selectedId === d.id
            const isHover = hoverId === d.id
            return (
              <g
                key={d.id}
                transform={`translate(${d.x},${d.y})`}
                className={`graph-node ${dimmed ? 'dimmed' : ''}`}
                style={{ cursor: dragRef.current?.id === d.id ? 'grabbing' : 'grab' }}
                onPointerDown={(ev) => startDrag(ev, d)}
                onPointerEnter={() => setHoverId(d.id)}
                onPointerLeave={() => setHoverId((h) => (h === d.id ? null : h))}
              >
                {(isSel || isHover) && <circle r={r + 12} fill="url(#nodeGlow)" />}
                {/* hover үед холбогдсон node-уудыг гэрэлтүүлэх цагираг */}
                {neighborIds && neighborIds.has(d.id) && (hoverId || selectedId) && !isSel && (
                    <circle r={r + 5} fill="none" stroke="var(--color-accent)" strokeWidth={1} opacity={0.7} />
                )}
                {/* томруулсан товч талбар — жижиг node-ийг ч мөр дарж чирахад хялбар */}
                <circle r={Math.max(r + 8, 14)} fill="transparent" />
                <circle
                  r={r}
                  fill={d.ghost ? 'var(--color-ink-900)' : t.color}
                  fillOpacity={d.ghost ? 0.4 : 0.18}
                  stroke={isSel ? 'var(--color-accent-bright)' : t.color}
                  strokeWidth={isSel ? 2.5 : 1.5}
                  strokeDasharray={d.ghost ? '3 3' : undefined}
                />
                {d.has_contradiction && (
                  <circle r={3} cx={r * 0.7} cy={-r * 0.7} fill="var(--color-warn)" stroke="var(--color-ink-950)" strokeWidth="1" />
                )}
                {(labelLimit || isHover || isSel) && (
                  <text
                    className={`graph-node-label ${isSel || isHover ? 'active' : ''}`}
                    y={r + 13}
                    textAnchor="middle"
                    style={d.ghost ? { fontStyle: 'italic' } : undefined}
                  >
                    {d.name.length > 22 ? d.name.slice(0, 20) + '…' : d.name}
                  </text>
                )}
              </g>
            )
          })}
        </g>
      </svg>
    </div>
  )
}

