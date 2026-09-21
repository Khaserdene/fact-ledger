import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api'
import {
  FolderGit2,
  Share2,
  Plus,
  Trash2,
  ExternalLink,
  ShieldCheck,
  Calendar,
  Layers,
  Search,
  User,
  Building,
  FileText,
  Activity,
  Maximize2,
  Minimize2,
  X,
  AlertCircle,
  Hash,
  ChevronRight,
  Info,
  CheckCircle2
} from 'lucide-react'
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
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'

const TICKS = 240

const TYPE_COLORS = {
  case: '#38e0ff',       // Accent cyan
  person: '#f59e0b',     // Amber
  company: '#10b981',    // Emerald
  institution: '#8b5cf6',// Purple
  media: '#ec4899',      // Pink
  fact: '#64748b',       // Slate
  other: '#94a3b8'
}

export default function CaseEditor() {
  const { slug } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Сонгогдсон node
  const [selectedNode, setSelectedNode] = useState(null)
  const [activeTab, setActiveTab] = useState('inspector') // 'inspector' | 'timeline' | 'add'

  // Timeline / Entity activity state
  const [entityActivity, setEntityActivity] = useState(null)
  const [activityLoading, setActivityLoading] = useState(false)

  // Subgraph nodes & edges layout
  const wrapRef = useRef(null)
  const svgRef = useRef(null)
  const simNodes = useRef([])
  const simEdges = useRef([])
  const [size, setSize] = useState({ w: 800, h: 600 })
  const [, forceRender] = useState(0)
  const [hoverNodeId, setHoverNodeId] = useState(null)
  const dragRef = useRef(null)

  // Шинээр холбох (Add Link) UI state
  const [searchTarget, setSearchTarget] = useState('')
  const [allEntities, setAllEntities] = useState([])
  const [selectedEntityToLink, setSelectedEntityToLink] = useState(null)
  const [linkRole, setLinkRole] = useState('INVOLVED_IN')
  const [linkNote, setLinkNote] = useState('')
  const [linking, setLinking] = useState(false)

  // Хэргийн өгөгдөл татах
  const loadCase = async () => {
    try {
      setLoading(true)
      const res = await api.getCase(slug)
      setData(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCase()
  }, [slug])

  // Бүх субъектийн жагсаалт хайлтад ашиглахаар бэлдэх
  useEffect(() => {
    api.listEntities({ limit: 100 }).then(setAllEntities).catch(() => {})
  }, [])

  // Хэмжээ өөрчлөгдөх ResizeObserver
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setSize({ w: Math.max(width, 200), h: Math.max(height, 200) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // D3 force simulation ажиллуулах
  useEffect(() => {
    if (!data?.graph) return

    const nodes = data.graph.nodes.map((n, i) => ({
      ...n,
      x: n.x ?? (size.w / 2 + (Math.random() - 0.5) * 150),
      y: n.y ?? (size.h / 2 + (Math.random() - 0.5) * 150),
      idx: i
    }))

    const idSet = new Set(nodes.map((n) => n.id))
    const links = (data.graph.edges || [])
      .filter((e) => idSet.has(e.source) && idSet.has(e.target))
      .map((e) => ({ ...e }))

    simNodes.current = nodes
    simEdges.current = links

    const sim = forceSimulation(nodes)
      .force(
        'link',
        forceLink(links)
          .id((d) => d.id)
          .distance((d) => (d.source.is_center || d.target.is_center ? 140 : 80))
          .strength(0.6)
      )
      .force('charge', forceManyBody().strength(-280))
      .force('collide', forceCollide().radius(28))
      .force('center', forceCenter(size.w / 2, size.h / 2).strength(0.08))
      .stop()

    for (let i = 0; i < TICKS; i++) sim.tick()
    forceRender((v) => v + 1)

    return () => sim.stop()
  }, [data, size.w, size.h])

  // Zoom / Pan
  useEffect(() => {
    if (!svgRef.current) return
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
    return () => svg.on('.zoom', null)
  }, [])

  // Сонгогдсон субъектийн activity timeline дуудах
  useEffect(() => {
    if (selectedNode && typeof selectedNode.id === 'number') {
      setActivityLoading(true)
      api
        .getCaseEntityActivity(slug, selectedNode.id)
        .then((res) => {
          setEntityActivity(res)
          setActiveTab('timeline')
        })
        .catch(() => setEntityActivity(null))
        .finally(() => setActivityLoading(false))
    } else {
      setEntityActivity(null)
      if (activeTab === 'timeline') setActiveTab('inspector')
    }
  }, [selectedNode, slug])

  // Drag handlers
  function startDrag(event, d) {
    event.stopPropagation()
    const svg = svgRef.current
    const rect = svg.getBoundingClientRect()
    dragRef.current = {
      id: d.id,
      startX: event.clientX,
      startY: event.clientY,
      nodeX: d.x,
      nodeY: d.y,
      moved: false,
    }
    window.addEventListener('pointermove', onDragMove)
    window.addEventListener('pointerup', onDragEnd)
  }

  function onDragMove(event) {
    if (!dragRef.current) return
    const dx = event.clientX - dragRef.current.startX
    const dy = event.clientY - dragRef.current.startY
    if (Math.hypot(dx, dy) > 4) dragRef.current.moved = true
    const target = simNodes.current.find((n) => n.id === dragRef.current.id)
    if (target) {
      target.x = dragRef.current.nodeX + dx
      target.y = dragRef.current.nodeY + dy
      forceRender((v) => v + 1)
    }
  }

  function onDragEnd() {
    window.removeEventListener('pointermove', onDragMove)
    window.removeEventListener('pointerup', onDragEnd)
    dragRef.current = null
  }

  // Node дарахад
  function handleNodeClick(e, node) {
    e.stopPropagation()
    if (selectedNode?.id === node.id) {
      setSelectedNode(null)
    } else {
      setSelectedNode(node)
    }
  }

  // Шинэ субъект холбох
  const handleAddLink = async (e) => {
    e.preventDefault()
    if (!selectedEntityToLink) return
    setLinking(true)
    try {
      await api.addCaseLink(slug, {
        entity_id: selectedEntityToLink.id,
        role: linkRole,
        note: linkNote || null,
      })
      setSelectedEntityToLink(null)
      setLinkNote('')
      setSearchTarget('')
      await loadCase()
    } catch (err) {
      alert('Холбоход алдаа гарлаа: ' + err.message)
    } finally {
      setLinking(false)
    }
  }

  // Холбоос устгах
  const handleRemoveLink = async (linkId) => {
    if (!confirm('Энэ субъектийг хэргээс салгах уу?')) return
    try {
      await api.removeCaseLink(slug, linkId)
      if (selectedNode) setSelectedNode(null)
      await loadCase()
    } catch (err) {
      alert('Салгахад алдаа: ' + err.message)
    }
  }

  // Сонгогдсон node-той холбоотой edge, node-уудыг тодорхойлох (Highlighting & Dimming)
  const connectedNodeIds = useMemo(() => {
    if (!selectedNode || !simEdges.current) return null
    const set = new Set([selectedNode.id])
    for (const e of simEdges.current) {
      const sId = typeof e.source === 'object' ? e.source.id : e.source
      const tId = typeof e.target === 'object' ? e.target.id : e.target
      if (sId === selectedNode.id) set.add(tId)
      if (tId === selectedNode.id) set.add(sId)
    }
    return set
  }, [selectedNode])

  if (loading) {
    return (
      <div className="py-32 flex justify-center">
        <Spinner />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-danger/10 border border-danger/30 rounded text-danger font-mono">
        <p className="font-bold flex items-center gap-2">
          <AlertCircle size={18} /> Хэргийг ачааллахад алдаа гарлаа:
        </p>
        <p className="mt-1 text-sm">{error || 'Хэрэг олдсонгүй'}</p>
        <Link to="/cases" className="mt-4 inline-block text-xs text-accent underline">
          ← Хэргүүдийн жагсаалт руу буцах
        </Link>
      </div>
    )
  }

  const { case: caseObj, summary, entities, facts, links } = data

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)]">
      {/* Дээд хэсэг: Case Header */}
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-line shrink-0">
        <div className="flex items-center gap-3">
          <Link
            to="/cases"
            className="text-xs font-mono text-dim hover:text-accent transition flex items-center gap-1"
          >
            ← ХЭРГҮҮД
          </Link>
          <span className="text-faint">/</span>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-accent animate-pulse" />
            <h1 className="text-lg font-bold font-display text-text truncate max-w-md">
              {caseObj.title}
            </h1>
            <Badge tone={caseObj.status === 'PUBLISHED' ? 'ok' : 'warn'}>
              {caseObj.status}
            </Badge>
          </div>
        </div>

        {/* Action controls */}
        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-3 text-xs font-mono text-dim mr-2">
            <span>● {summary.entities_count} субъект</span>
            <span>● {summary.edges_count} хамаарал</span>
            <span>● {summary.facts_count} факт</span>
          </div>

          <button
            onClick={() => setActiveTab('add')}
            className="px-3 py-1.5 bg-accent-dim border border-accent-line text-accent font-mono text-xs font-bold rounded flex items-center gap-1.5 hover:bg-accent hover:text-ink-950 transition"
          >
            <Plus size={14} /> НЭМЭХ
          </button>
        </div>
      </div>

      {/* Үндсэн агуулга: Canvas (зүүн) + Drawer/Inspector (баруун) */}
      <div className="flex-1 flex overflow-hidden border border-line rounded-lg bg-surface-1/40 relative">
        {/* Force Graph Canvas */}
        <div ref={wrapRef} className="flex-1 relative overflow-hidden bg-ink-950/60">
          <svg
            ref={svgRef}
            width={size.w}
            height={size.h}
            className="w-full h-full cursor-grab active:cursor-grabbing select-none"
            onClick={() => setSelectedNode(null)}
          >
            <defs>
              <pattern
                id="grid"
                width="30"
                height="30"
                patternUnits="userSpaceOnUse"
              >
                <circle cx="1.5" cy="1.5" r="1" fill="rgb(255 255 255 / 0.04)" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />

            <g className="viewport">
              {/* Edges */}
              <g className="edges">
                {simEdges.current.map((e, idx) => {
                  const s = typeof e.source === 'object' ? e.source : simNodes.current.find((n) => n.id === e.source)
                  const t = typeof e.target === 'object' ? e.target : simNodes.current.find((n) => n.id === e.target)
                  if (!s || !t) return null

                  const isConnected =
                    !connectedNodeIds || (connectedNodeIds.has(s.id) && connectedNodeIds.has(t.id))
                  const opacity = isConnected ? 0.75 : 0.08

                  return (
                    <g key={idx}>
                      <line
                        x1={s.x}
                        y1={s.y}
                        x2={t.x}
                        y2={t.y}
                        stroke={s.is_center || t.is_center ? '#38e0ff' : '#94a3b8'}
                        strokeWidth={s.is_center || t.is_center ? 1.5 : 1}
                        strokeDasharray={s.is_center || t.is_center ? '4 2' : 'none'}
                        strokeOpacity={opacity}
                      />
                      {e.rel_type && isConnected && (
                        <text
                          x={(s.x + t.x) / 2}
                          y={(s.y + t.y) / 2 - 4}
                          fill="#94a3b8"
                          fontSize="9"
                          fontFamily="monospace"
                          textAnchor="middle"
                          opacity={opacity}
                          className="pointer-events-none"
                        >
                          {e.rel_type}
                        </text>
                      )}
                    </g>
                  )
                })}
              </g>

              {/* Nodes */}
              <g className="nodes">
                {simNodes.current.map((node) => {
                  const isSelected = selectedNode?.id === node.id
                  const isConnected = !connectedNodeIds || connectedNodeIds.has(node.id)
                  const opacity = isConnected ? 1 : 0.15
                  const color = TYPE_COLORS[node.entity_type] || TYPE_COLORS.other
                  const isCenter = !!node.is_center
                  const radius = isCenter ? 22 : node.entity_type === 'fact' ? 10 : 16

                  return (
                    <g
                      key={node.id}
                      className="cursor-pointer transition-opacity duration-200"
                      transform={`translate(${node.x}, ${node.y})`}
                      opacity={opacity}
                      onPointerDown={(e) => startDrag(e, node)}
                      onClick={(e) => handleNodeClick(e, node)}
                      onMouseEnter={() => setHoverNodeId(node.id)}
                      onMouseLeave={() => setHoverNodeId(null)}
                    >
                      {/* Aura / Halo if selected */}
                      {isSelected && (
                        <circle
                          r={radius + 8}
                          fill="none"
                          stroke="#38e0ff"
                          strokeWidth="2"
                          strokeDasharray="4 2"
                          className="animate-spin"
                        />
                      )}

                      {/* Main Circle */}
                      <circle
                        r={radius}
                        fill={isCenter ? '#090d16' : '#111827'}
                        stroke={color}
                        strokeWidth={isSelected ? 3 : isCenter ? 2.5 : 1.5}
                        className="transition-all hover:scale-110"
                      />

                      {/* Center Node Icon / Letter */}
                      <text
                        dy=".3em"
                        textAnchor="middle"
                        fill={color}
                        fontSize={isCenter ? '14' : '10'}
                        fontWeight="bold"
                        fontFamily="monospace"
                        className="pointer-events-none"
                      >
                        {isCenter ? '★' : node.entity_type === 'fact' ? 'F' : node.name?.charAt(0) || '•'}
                      </text>

                      {/* Label below */}
                      <text
                        y={radius + 12}
                        textAnchor="middle"
                        fill={isSelected ? '#38e0ff' : '#cbd5e1'}
                        fontSize="10"
                        fontFamily="monospace"
                        className="pointer-events-none"
                      >
                        {node.name?.length > 20 ? node.name.slice(0, 18) + '…' : node.name}
                      </text>
                    </g>
                  )
                })}
              </g>
            </g>
          </svg>

          {/* Quick info chip in canvas */}
          <div className="absolute bottom-3 left-3 bg-surface-1/90 border border-line backdrop-blur p-2 rounded text-[11px] font-mono text-dim pointer-events-none">
            {selectedNode ? (
              <span className="text-text">Сонгосон: <b className="text-accent">{selectedNode.name}</b></span>
            ) : (
              <span>Node дээр дарж фокуслах ба баруун талын самбарт үзэх</span>
            )}
          </div>
        </div>

        {/* Баруун талын Drawer / Inspector Panel */}
        <div className="w-96 border-l border-line bg-surface-1 flex flex-col shrink-0">
          {/* Tabs */}
          <div className="flex border-b border-line bg-surface-2/60">
            <button
              onClick={() => setActiveTab('inspector')}
              className={`flex-1 py-2.5 text-xs font-mono font-bold flex items-center justify-center gap-1.5 border-b-2 transition ${
                activeTab === 'inspector'
                  ? 'border-accent text-accent bg-surface-1'
                  : 'border-transparent text-dim hover:text-text'
              }`}
            >
              <Info size={14} /> ИНСПЕКТОР
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              disabled={!selectedNode || typeof selectedNode.id !== 'number'}
              className={`flex-1 py-2.5 text-xs font-mono font-bold flex items-center justify-center gap-1.5 border-b-2 transition disabled:opacity-40 ${
                activeTab === 'timeline'
                  ? 'border-accent text-accent bg-surface-1'
                  : 'border-transparent text-dim hover:text-text'
              }`}
            >
              <Activity size={14} /> ТАЙМЛАЙН
            </button>
            <button
              onClick={() => setActiveTab('add')}
              className={`flex-1 py-2.5 text-xs font-mono font-bold flex items-center justify-center gap-1.5 border-b-2 transition ${
                activeTab === 'add'
                  ? 'border-accent text-accent bg-surface-1'
                  : 'border-transparent text-dim hover:text-text'
              }`}
            >
              <Plus size={14} /> НЭМЭХ
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {activeTab === 'inspector' && (
              <div>
                {selectedNode ? (
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-mono text-dim uppercase">
                          {selectedNode.entity_type} NODE
                        </span>
                        {selectedNode.role && (
                          <Badge tone="accent">{selectedNode.role}</Badge>
                        )}
                      </div>
                      <h2 className="text-base font-bold text-text font-display">
                        {selectedNode.name}
                      </h2>
                    </div>

                    {/* Хэрэв entity бол холбоосын тохиргоо */}
                    {typeof selectedNode.id === 'number' && (
                      <div className="space-y-3 pt-3 border-t border-line">
                        <div className="flex items-center justify-between text-xs font-mono">
                          <Link
                            to={`/entities/${selectedNode.id}`}
                            className="text-accent hover:underline flex items-center gap-1"
                          >
                            Субъектийн хуудас <ExternalLink size={12} />
                          </Link>

                          {links.find((l) => l.entity_id === selectedNode.id) && (
                            <button
                              onClick={() => {
                                const l = links.find((l) => l.entity_id === selectedNode.id)
                                if (l) handleRemoveLink(l.id)
                              }}
                              className="text-danger hover:underline text-[11px]"
                            >
                              Хэргээс салгах
                            </button>
                          )}
                        </div>

                        {/* Түргэн тойм */}
                        {entities.find((e) => e.id === selectedNode.id)?.description && (
                          <p className="text-xs text-dim leading-relaxed bg-surface-2 p-2.5 rounded border border-line">
                            {entities.find((e) => e.id === selectedNode.id).description}
                          </p>
                        )}

                        <button
                          onClick={() => setActiveTab('timeline')}
                          className="w-full py-2 bg-surface-2 hover:bg-surface-3 border border-line text-xs font-mono text-text rounded flex items-center justify-center gap-2 transition"
                        >
                          <Activity size={14} className="text-accent" />
                          Хэргийн хүрээн дэх үйл явдал харах
                        </button>
                      </div>
                    )}

                    {/* Хэрэв Fact node бол SHA256 болон цитат харуулах */}
                    {selectedNode.entity_type === 'fact' && (
                      <div className="space-y-3 pt-3 border-t border-line">
                        {(() => {
                          const fact = facts.find((f) => f.id === selectedNode.fact_id)
                          if (!fact) return null
                          return (
                            <>
                              <div className="bg-surface-2 p-3 rounded border border-line space-y-2">
                                <div className="text-[10px] font-mono text-dim flex items-center gap-1">
                                  <Calendar size={12} /> {fact.fact_date || 'Огноогүй'}
                                </div>
                                <p className="text-xs text-text leading-relaxed">
                                  {fact.fact_text}
                                </p>
                                {fact.source_quote && (
                                  <blockquote className="border-l-2 border-accent pl-2 text-[11px] text-dim italic">
                                    "{fact.source_quote}"
                                  </blockquote>
                                )}
                              </div>

                              {/* Proof Drawer / SHA-256 verification */}
                              {fact.sha256 && (
                                <div className="p-2.5 bg-ink-950 border border-line rounded space-y-1">
                                  <div className="flex items-center gap-1 text-[10px] font-mono text-ok">
                                    <ShieldCheck size={12} /> SHA-256 Баталгаажсан
                                  </div>
                                  <div className="text-[9px] font-mono text-dim break-all select-all">
                                    {fact.sha256}
                                  </div>
                                </div>
                              )}

                              {fact.source_url && (
                                <a
                                  href={fact.source_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-xs text-accent hover:underline flex items-center gap-1"
                                >
                                  Эх сурвалж үзэх <ExternalLink size={12} />
                                </a>
                              )}
                            </>
                          )
                        })()}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="py-16 text-center space-y-3">
                    <FolderGit2 className="mx-auto text-dim" size={32} />
                    <div className="text-xs font-mono text-dim">
                      Мөрдлөгийн ерөнхий мэдээлэл
                    </div>
                    <div className="p-3 bg-surface-2 border border-line rounded text-left space-y-2">
                      <div className="text-xs font-bold text-text">{caseObj.title}</div>
                      <p className="text-xs text-dim leading-relaxed">
                        {caseObj.description || 'Тодорхойлолт байхгүй'}
                      </p>
                      <div className="pt-2 border-t border-line/60 text-[10px] font-mono text-dim flex justify-between">
                        <span>Үүсгэсэн:</span>
                        <span>{new Date(caseObj.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Timeline Tab */}
            {activeTab === 'timeline' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-text">
                    {entityActivity?.entity?.name}
                  </span>
                  <span className="text-[10px] font-mono text-dim">
                    {entityActivity?.total_facts || 0} баримт
                  </span>
                </div>

                {activityLoading ? (
                  <div className="py-12 flex justify-center">
                    <Spinner />
                  </div>
                ) : !entityActivity?.timeline?.length ? (
                  <p className="text-xs font-mono text-dim py-8 text-center">
                    Үйл явдлын түүх олдсонгүй
                  </p>
                ) : (
                  <div className="space-y-2.5">
                    {entityActivity.timeline.map((item) => (
                      <div
                        key={item.id}
                        className="p-2.5 bg-surface-2 border border-line rounded space-y-1.5"
                      >
                        <div className="flex items-center justify-between text-[10px] font-mono text-dim">
                          <span className="flex items-center gap-1">
                            <Calendar size={10} /> {item.date || 'Огноогүй'}
                          </span>
                          <span className="text-accent">{item.fact_type}</span>
                        </div>
                        <p className="text-xs text-text leading-relaxed">
                          {item.text}
                        </p>
                        {item.sha256 && (
                          <div className="text-[9px] font-mono text-faint truncate">
                            SHA: {item.sha256.slice(0, 16)}…
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Add Link Tab */}
            {activeTab === 'add' && (
              <form onSubmit={handleAddLink} className="space-y-4">
                <div className="text-xs font-mono font-bold text-text">
                  СУБЪЕКТ ХОЛБОХ
                </div>

                {/* Search existing entities */}
                <div>
                  <label className="block text-[11px] font-mono text-dim mb-1">
                    СУБЪЕКТ ХАЙХ
                  </label>
                  <input
                    type="text"
                    placeholder="Нэрээр хайх..."
                    value={searchTarget}
                    onChange={(e) => setSearchTarget(e.target.value)}
                    className="w-full px-3 py-1.5 bg-surface-2 border border-line rounded text-xs text-text font-mono focus:border-accent focus:outline-none"
                  />
                  {searchTarget && (
                    <div className="mt-1 max-h-36 overflow-y-auto bg-surface-2 border border-line rounded divide-y divide-line">
                      {allEntities
                        .filter((e) =>
                          e.name.toLowerCase().includes(searchTarget.toLowerCase())
                        )
                        .slice(0, 6)
                        .map((ent) => (
                          <div
                            key={ent.id}
                            onClick={() => {
                              setSelectedEntityToLink(ent)
                              setSearchTarget('')
                            }}
                            className="p-2 text-xs font-mono hover:bg-surface-3 cursor-pointer flex items-center justify-between"
                          >
                            <span className="text-text">{ent.name}</span>
                            <span className="text-[10px] text-dim">{ent.entity_type}</span>
                          </div>
                        ))}
                    </div>
                  )}
                </div>

                {selectedEntityToLink && (
                  <div className="p-2.5 bg-accent-dim/30 border border-accent-line rounded flex items-center justify-between text-xs font-mono">
                    <div>
                      <div className="font-bold text-text">{selectedEntityToLink.name}</div>
                      <div className="text-[10px] text-dim">{selectedEntityToLink.entity_type}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedEntityToLink(null)}
                      className="text-dim hover:text-danger"
                    >
                      ✕
                    </button>
                  </div>
                )}

                <div>
                  <label className="block text-[11px] font-mono text-dim mb-1">
                    ҮҮРЭГ / ХАМААРАЛ (ROLE)
                  </label>
                  <select
                    value={linkRole}
                    onChange={(e) => setLinkRole(e.target.value)}
                    className="w-full px-3 py-1.5 bg-surface-2 border border-line rounded text-xs text-text font-mono focus:border-accent focus:outline-none"
                  >
                    <option value="INVOLVED_IN">INVOLVED_IN (Холбогдогч)</option>
                    <option value="PART_OF_CASE">PART_OF_CASE (Хэргийн хэсэг)</option>
                    <option value="SUSPECT">SUSPECT (Сэжигтэн)</option>
                    <option value="WITNESS">WITNESS (Гэрч)</option>
                    <option value="VICTIM">VICTIM (Хохирогч)</option>
                    <option value="INVESTIGATOR">INVESTIGATOR (Мөрдөгч)</option>
                    <option value="BENEFICIARY">BENEFICIARY (Ашиг хүртэгч)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-dim mb-1">
                    ТЭМДЭГЛЭЛ
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Хэрэгт холбогдох шалтгаан..."
                    value={linkNote}
                    onChange={(e) => setLinkNote(e.target.value)}
                    className="w-full px-3 py-1.5 bg-surface-2 border border-line rounded text-xs text-text font-mono focus:border-accent focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={!selectedEntityToLink || linking}
                  className="w-full py-2 bg-accent text-ink-950 font-mono text-xs font-bold rounded hover:bg-accent/90 disabled:opacity-40 transition"
                >
                  {linking ? 'ХОЛБОЖ БАЙНА...' : 'ХЭРЭГТ ХОЛБОХ'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
