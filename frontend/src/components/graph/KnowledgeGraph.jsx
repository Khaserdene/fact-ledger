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
import {
  Maximize2,
  Minimize2,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Layers,
  Calendar,
  Compass,
  Target
} from 'lucide-react'

const TICKS = 340

/**
 * World-Class Cyberpunk / Investigative Knowledge Graph Engine
 *
 * Онцлог боломжууд:
 * 1. 4 Layout Modes:
 *    - 'force': Чөлөөт физик таталцлын сүлжээ
 *    - 'timeline': Зүүнээс баруун тийш X-тэнхлэгийн дагуу он цагийн эрэмбэ
 *    - 'cluster': Төрөл ба бүлэглэлээр (Засгийн газар, Хэрэг, Компани, Хүн г.м) бөөгнөрсөн үүл
 *    - 'radial': Сонгогдсон төв субъектийг тойрсон цагирган мандал
 *
 * 2. Premium Design:
 *    - Neon Glow Halos & Cyberpunk Grid
 *    - Pulsing Case / Hub Nodes
 *    - Animated glowing dashed lines for active relationships
 *    - Cluster background hulls
 */
export default function KnowledgeGraph({
  data,
  filteredNodeIds,
  yearRange,
  selectedId,
  onSelect,
  layoutMode = 'force', // 'force' | 'timeline' | 'cluster' | 'radial'
  onLayoutChange
}) {
  const wrapRef = useRef(null)
  const svgRef = useRef(null)
  const simNodes = useRef([])
  const simEdges = useRef([])
  const [size, setSize] = useState({ w: 800, h: 600 })
  const [, forceRender] = useState(0)
  const [hoverId, setHoverId] = useState(null)
  const dragRef = useRef(null)

  // Контейнерийн хэмжээг ажиглана
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

  // Cluster төвүүдийг тодорхойлох
  const clusterCenters = useMemo(() => {
    const w = size.w
    const h = size.h
    const cx = w / 2
    const cy = h / 2
    return {
      case: { x: cx, y: cy },
      person: { x: cx - w * 0.28, y: cy - h * 0.22 },
      company: { x: cx + w * 0.28, y: cy - h * 0.22 },
      government: { x: cx - w * 0.22, y: cy + h * 0.25 },
      parliament: { x: cx + w * 0.22, y: cy + h * 0.25 },
      org: { x: cx, y: cy - h * 0.32 },
      party: { x: cx - w * 0.35, y: cy },
      state: { x: cx + w * 0.35, y: cy },
      other: { x: cx, y: cy + h * 0.32 },
    }
  }, [size.w, size.h])

  // Simulation: Layout Mode бүрээр математик загварчлалыг өөрчилнө
  useEffect(() => {
    if (!data) return
    const nodes = data.nodes.map((n, i) => ({ ...n, x: null, y: null, idx: i }))
    const idSet = new Set(nodes.map((n) => n.id))
    const links = data.edges
      .filter((e) => idSet.has(e.source) && idSet.has(e.target))
      .map((e) => ({ ...e }))
    simNodes.current = nodes
    simEdges.current = links

    // Он цагийн хамгийн бага, их он
    let minYear = 1990
    let maxYear = 2026
    const allYears = []
    for (const n of nodes) {
      if (n.active_from) allYears.push(parseInt(n.active_from.slice(0, 4), 10))
      if (n.active_to) allYears.push(parseInt(n.active_to.slice(0, 4), 10))
    }
    if (allYears.length) {
      minYear = Math.min(...allYears)
      maxYear = Math.max(...allYears)
    }

    const sim = forceSimulation(nodes)

    if (layoutMode === 'timeline') {
      // Timeline Layout: X тэнхлэгээр он цагийн хуваарилалт
      sim
        .force(
          'link',
          forceLink(links).id((d) => d.id).distance(60).strength(0.2)
        )
        .force('charge', forceManyBody().strength(-120))
        .force('collide', forceCollide().radius((d) => nodeRadius(d) + 8))
        .force(
          'x',
          forceX((d) => {
            const yr = d.active_from ? parseInt(d.active_from.slice(0, 4), 10) : (minYear + maxYear) / 2
            const progress = (yr - minYear) / Math.max(maxYear - minYear, 1)
            return size.w * 0.12 + progress * (size.w * 0.76)
          }).strength(0.85)
        )
        .force('y', forceY(size.h / 2).strength(0.1))
        .force('center', forceCenter(size.w / 2, size.h / 2).strength(0.04))

    } else if (layoutMode === 'cluster') {
      // Cluster Layout: Төрөл тус бүрээр тусдаа татах хүч
      sim
        .force(
          'link',
          forceLink(links).id((d) => d.id).distance(75).strength(0.35)
        )
        .force('charge', forceManyBody().strength(-180))
        .force('collide', forceCollide().radius((d) => nodeRadius(d) + 12))
        .force(
          'x',
          forceX((d) => {
            const c = clusterCenters[d.entity_type] || clusterCenters.other
            return c.x
          }).strength(0.4)
        )
        .force(
          'y',
          forceY((d) => {
            const c = clusterCenters[d.entity_type] || clusterCenters.other
            return c.y
          }).strength(0.4)
        )
        .force('center', forceCenter(size.w / 2, size.h / 2).strength(0.05))

    } else if (layoutMode === 'radial' && selectedId) {
      // Radial Layout: Сонгосон төвөөс тойрч тархах
      const focus = selectedId
      const directNeighbors = new Set()
      for (const e of links) {
        const s = typeof e.source === 'object' ? e.source.id : e.source
        const t = typeof e.target === 'object' ? e.target.id : e.target
        if (s === focus) directNeighbors.add(t)
        if (t === focus) directNeighbors.add(s)
      }

      sim
        .force(
          'link',
          forceLink(links).id((d) => d.id).distance(90).strength(0.4)
        )
        .force('charge', forceManyBody().strength(-200))
        .force('collide', forceCollide().radius((d) => nodeRadius(d) + 10))
        .force(
          'r',
          forceX((d) => {
            if (d.id === focus) return size.w / 2
            return directNeighbors.has(d.id) ? size.w / 2 + 180 : size.w / 2 + 320
          }).strength(0.6)
        )
        .force('center', forceCenter(size.w / 2, size.h / 2).strength(0.08))

    } else {
      // Стандарт Force Network (Default)
      sim
        .force(
          'link',
          forceLink(links).id((d) => d.id).distance((d) => (d.source.is_case || d.target.is_case ? 140 : 85)).strength(0.5)
        )
        .force('charge', forceManyBody().strength(-220))
        .force('collide', forceCollide().radius((d) => nodeRadius(d) + 14))
        .force('x', forceX(size.w / 2).strength(0.04))
        .force('y', forceY(size.h / 2).strength(0.06))
        .force('center', forceCenter(size.w / 2, size.h / 2).strength(0.05))
    }

    sim.stop()
    for (let i = 0; i < TICKS; i++) sim.tick()
    forceRender((v) => v + 1)

    return () => sim.stop()
  }, [data, size.w, size.h, layoutMode, selectedId, clusterCenters])

  // Zoom / pan
  useEffect(() => {
    const svg = select(svgRef.current)
    const behavior = d3zoom()
      .scaleExtent([0.2, 4])
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

  const svgDownPos = useRef(null)

  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === 'Escape' && onSelect) {
        onSelect(null)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onSelect])

  function handleSvgPointerDown(e) {
    if (!e.target.closest('.graph-node')) {
      svgDownPos.current = { x: e.clientX, y: e.clientY }
    } else {
      svgDownPos.current = null
    }
  }

  function handleSvgPointerUp(e) {
    if (!svgDownPos.current) return
    const dx = Math.abs(e.clientX - svgDownPos.current.x)
    const dy = Math.abs(e.clientY - svgDownPos.current.y)
    svgDownPos.current = null
    if (dx < 6 && dy < 6 && !e.target.closest('.graph-node')) {
      if (onSelect) {
        onSelect(null)
      }
    }
  }

  function nodeRadius(d) {
    if (d.is_case) return 22
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
      if (d) {
        if (selectedId === d.id) {
          onSelect(null)
        } else {
          onSelect(d)
        }
      }
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

  const getEdgeSourceId = (e) => (typeof e.source === 'object' && e.source !== null ? e.source.id : e.source)
  const getEdgeTargetId = (e) => (typeof e.target === 'object' && e.target !== null ? e.target.id : e.target)

  const yearOf = (iso) => (iso ? parseInt(iso.slice(0, 4), 10) : null)
  function overlapsRange(fromIso, toIso) {
    if (!yearRange) return true
    const [y1, y2] = yearRange
    const from = yearOf(fromIso)
    const to = yearOf(toIso)
    if (from === null && to === null) return true
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

  const neighborIds = useMemo(() => {
    if (!hoverId && !selectedId) return null
    const focus = hoverId || selectedId
    const s = new Set([focus])
    for (const e of simEdges.current) {
      if (!edgeVisible(e)) continue
      const sId = getEdgeSourceId(e)
      const tId = getEdgeTargetId(e)
      if (sId === focus) s.add(tId)
      if (tId === focus) s.add(sId)
    }
    return s
  }, [hoverId, selectedId, filteredNodeIds, yearRange])

  const nodes = simNodes.current
  const links = simEdges.current
  const labelLimit = nodes.length <= 80

  return (
    <div ref={wrapRef} className="relative w-full h-full min-h-[500px] overflow-hidden bg-[#060913] rounded-lg border border-line select-none">
      {/* ── Дээд удирдлагын хэрэгслүүд (Layout Controls & Indicators) ── */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-2 bg-surface-1/85 backdrop-blur-md p-1.5 rounded-lg border border-line shadow-xl">
        <div className="flex items-center gap-1">
          {[
            { id: 'force', label: 'Сүлжээ', Icon: Compass, tip: 'Чөлөөт таталцлын физик сүлжээ' },
            { id: 'timeline', label: 'Хронологи', Icon: Calendar, tip: 'Он цагийн дарааллаар эрэмбэлэх' },
            { id: 'cluster', label: 'Кластер', Icon: Layers, tip: 'Бүлэг ба төрлөөр нь бүлэглэх' },
            { id: 'radial', label: 'Төвлөрсөн', Icon: Target, tip: 'Сонгосон субъектийг тойруулах' },
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => onLayoutChange && onLayoutChange(mode.id)}
              className={`px-2.5 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition ${
                layoutMode === mode.id
                  ? 'bg-accent text-ink-950 font-bold shadow-[0_0_12px_rgb(56_224_255/0.3)]'
                  : 'text-dim hover:text-text hover:bg-surface-2'
              }`}
              title={mode.tip}
            >
              <mode.Icon size={13} />
              <span className="hidden sm:inline">{mode.label}</span>
            </button>
          ))}
        </div>
      </div>

      <svg
        ref={svgRef}
        width={size.w}
        height={size.h}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onPointerDown={handleSvgPointerDown}
        onPointerUp={handleSvgPointerUp}
      >
        <defs>
          {/* Cyberpunk Dots Grid */}
          <pattern id="cyber-grid" width="36" height="36" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1.2" fill="rgb(56 224 255 / 0.05)" />
            <path d="M 36 0 L 0 0 0 36" fill="none" stroke="rgb(255 255 255 / 0.015)" strokeWidth="0.5" />
          </pattern>

          {/* Glow filter */}
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <rect width="100%" height="100%" fill="url(#cyber-grid)" />

        <g className="viewport">
          {/* ── Timeline Mode X-Axis Grid Markers ── */}
          {layoutMode === 'timeline' && (
            <g className="timeline-grid opacity-30 pointer-events-none">
              {[1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024].map((yr) => {
                const prog = (yr - 1990) / (2026 - 1990)
                const x = size.w * 0.12 + prog * (size.w * 0.76)
                return (
                  <g key={yr} transform={`translate(${x}, 0)`}>
                    <line y1={40} y2={size.h - 40} stroke="#38e0ff" strokeDasharray="3 4" strokeWidth={0.8} />
                    <text y={size.h - 20} fill="#38e0ff" fontSize="10" fontFamily="var(--font-sans), sans-serif" textAnchor="middle">
                      {yr}
                    </text>
                  </g>
                )
              })}
            </g>
          )}

          {/* ── Edges ── */}
          <g className="edges">
            {links.map((e) => {
              if (!edgeVisible(e)) return null
              const s = typeof e.source === 'object' ? e.source : nodeById.get(e.source)
              const t = typeof e.target === 'object' ? e.target : nodeById.get(e.target)
              if (!s || !t || s.x == null || t.x == null) return null

              const isFocusRel =
                neighborIds && (neighborIds.has(s.id) && neighborIds.has(t.id))
              const opacity = neighborIds ? (isFocusRel ? 0.85 : 0.06) : e.is_case_edge ? 0.6 : 0.25
              const strokeColor = e.is_case_edge
                ? '#f43f5e'
                : isFocusRel
                ? '#38e0ff'
                : '#64748b'

              return (
                <g key={e.id}>
                  <line
                    x1={s.x}
                    y1={s.y}
                    x2={t.x}
                    y2={t.y}
                    stroke={strokeColor}
                    strokeWidth={isFocusRel ? 2 : e.is_case_edge ? 1.5 : 1}
                    strokeOpacity={opacity}
                    strokeDasharray={e.is_case_edge ? '4 2' : 'none'}
                    className={e.is_case_edge ? 'animate-pulse' : ''}
                  />
                  {isFocusRel && e.rel_type && (
                    <text
                      x={(s.x + t.x) / 2}
                      y={(s.y + t.y) / 2 - 4}
                      fill="#38e0ff"
                      fontSize="9"
                      fontFamily="var(--font-sans), sans-serif"
                      fontWeight="500"
                      textAnchor="middle"
                      className="pointer-events-none drop-shadow"
                    >
                      {e.rel_type}
                    </text>
                  )}
                </g>
              )
            })}
          </g>

          {/* ── Nodes ── */}
          <g className="nodes">
            {nodes.map((d) => {
              if (!nodeVisible(d) || d.x == null) return null
              const r = nodeRadius(d)
              const isSelected = selectedId === d.id
              const isNeighbor = neighborIds ? neighborIds.has(d.id) : true
              const opacity = neighborIds ? (isNeighbor ? 1 : 0.12) : 1
              const tInfo = entityType(d.entity_type)
              const color = d.is_case ? '#f43f5e' : tInfo.color || '#94a3b8'

              return (
                <g
                  key={d.id}
                  className="graph-node cursor-pointer transition-opacity duration-200"
                  transform={`translate(${d.x}, ${d.y})`}
                  opacity={opacity}
                  onPointerDown={(e) => startDrag(e, d)}
                  onMouseEnter={() => setHoverId(d.id)}
                  onMouseLeave={() => setHoverId(null)}
                >
                  {/* Selection Aura */}
                  {isSelected && (
                    <circle
                      r={r + 8}
                      fill="none"
                      stroke="#38e0ff"
                      strokeWidth="2"
                      strokeDasharray="4 2"
                      className="animate-spin"
                    />
                  )}

                  {/* Case Node Halo */}
                  {d.is_case && (
                    <circle
                      r={r + 6}
                      fill="none"
                      stroke="#f43f5e"
                      strokeWidth="1.5"
                      opacity="0.6"
                      className="animate-pulse"
                    />
                  )}

                  {/* Main Circle */}
                  <circle
                    r={r}
                    fill={d.is_case ? '#1e0a12' : '#0a101d'}
                    stroke={color}
                    strokeWidth={isSelected ? 3 : d.is_case ? 2.5 : 1.5}
                    filter={isSelected || d.is_case ? 'url(#glow)' : undefined}
                    className="transition-transform duration-200 hover:scale-110"
                  />

                  {/* Center Symbol / Initial */}
                  <text
                    dy=".35em"
                    textAnchor="middle"
                    fill={color}
                    fontSize={d.is_case ? '13' : r > 12 ? '10' : '8'}
                    fontWeight="bold"
                    fontFamily="var(--font-sans), sans-serif"
                    className="pointer-events-none"
                  >
                    {d.is_case ? '★' : d.name?.charAt(0) || '•'}
                  </text>

                  {/* Node Label */}
                  {(labelLimit || isSelected || isNeighbor || d.is_case) && (
                    <text
                      y={r + 12}
                      textAnchor="middle"
                      fill={isSelected ? '#38e0ff' : d.is_case ? '#f43f5e' : '#cbd5e1'}
                      fontSize="10"
                      fontFamily="var(--font-sans), sans-serif"
                      fontWeight={d.is_case || isSelected ? '600' : 'normal'}
                      className="pointer-events-none drop-shadow"
                    >
                      {d.name?.length > 20 ? d.name.slice(0, 18) + '…' : d.name}
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        </g>
      </svg>

      {/* Quick bottom tooltip */}
      <div className="absolute bottom-3 left-3 bg-surface-1/90 border border-line backdrop-blur px-3 py-1.5 rounded text-[11px] font-mono text-dim pointer-events-none max-w-sm">
        {selectedId ? (
          <span className="text-text">Сонгосон: <b className="text-accent">{nodeById.get(selectedId)?.name}</b></span>
        ) : (
          <span>Node дээр дарж фокуслах ба хамаарлыг шалгана уу</span>
        )}
      </div>
    </div>
  )
}
