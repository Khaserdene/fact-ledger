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
  CheckCircle2,
  Play,
  Pause,
  RotateCcw,
  Clock,
  Filter,
  Check,
  ArrowRight,
  Sparkles
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

const TICKS = 260

const TYPE_COLORS = {
  case: '#38e0ff',        // Accent cyan
  person: '#f59e0b',      // Amber
  company: '#10b981',     // Emerald
  institution: '#8b5cf6', // Purple
  media: '#ec4899',       // Pink
  fact: '#64748b',        // Slate
  other: '#94a3b8'
}

export default function CaseEditor() {
  const { slug } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Сонгогдсон node
  const [selectedNode, setSelectedNode] = useState(null)
  const [activeTab, setActiveTab] = useState('case_timeline') // 'case_timeline' | 'inspector' | 'entity_timeline' | 'add'

  // Timeline / Entity activity state
  const [entityActivity, setEntityActivity] = useState(null)
  const [activityLoading, setActivityLoading] = useState(false)

  // Цаг хугацааны шүүлтүүр (Chronological Timeline Filter & Playback)
  const [activeStage, setActiveStage] = useState('ALL') // 'ALL' | 'ORIGIN' | 'OFFTAKE' | 'EXPOSED' | 'HEARING' | 'VERDICT'
  const [timeIndex, setTimeIndex] = useState(null) // null = all time, or index in sortedFacts
  const [isPlaying, setIsPlaying] = useState(false)
  const playTimerRef = useRef(null)

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

  // Хэргийн бүх баримтуудыг он цагийн дарааллаар эрэмбэлэх
  const sortedFacts = useMemo(() => {
    if (!data?.facts) return []
    return [...data.facts].sort((a, b) => {
      const da = a.fact_date || '9999-99-99'
      const db = b.fact_date || '9999-99-99'
      return da.localeCompare(db)
    })
  }, [data])

  // Цагийн мөчлөгүүд (Chronological Stages) — хэрэг бүрд тохируулан динамикаар эсвэл тусгайлан бодно
  const STAGES = useMemo(() => {
    if (slug === 'dbm-scandal') {
      return [
        { id: 'ALL', label: 'Бүх цаг үе', desc: 'Бүх баримт ба холбоосууд' },
        { id: 'ORIGIN', label: '1. Үүсгэн байгуулалт (2011–2012)', from: '2011-01-01', to: '2012-12-31', desc: 'Хөгжлийн банк байгуулагдаж, Чингис бонд босов' },
        { id: 'LOANS', label: '2. Том зээлүүд (2013–2020)', from: '2013-01-01', to: '2020-12-31', desc: 'Кью Эс Си, Бэрэн, Хөтөл нарт зээл олгосон' },
        { id: 'EXPOSED', label: '3. Чанаргүй зээлийн дэлбэрэлт (2022)', from: '2022-01-01', to: '2022-12-31', desc: '1.8 их наядын чанаргүй зээлийг зарлаж шалгав' },
        { id: 'HEARING', label: '4. 3 шатны сонсгол (2023)', from: '2023-01-01', to: '2023-05-31', desc: 'УИХ-ын Түр хорооны 3 шатны нээлттэй сонсгол' },
        { id: 'VERDICT', label: '5. Шүүх хурал & Дээд шүүх (2023–2024)', from: '2023-06-01', to: '2026-12-31', desc: '80 шүүгдэгчийн анхан шат болон Дээд шүүх' },
      ]
    }
    if (slug === 'coal-theft') {
      return [
        { id: 'ALL', label: 'Бүх цаг үе', desc: 'Бүх баримт ба холбоосууд' },
        { id: 'ORIGIN', label: '1. Эхлэл (2018)', from: '2018-01-01', to: '2018-12-31', desc: 'ЭТТ удирдлагын томилгоо' },
        { id: 'OFFTAKE', label: '2. Нууц гэрээнүүд (2019–2021)', from: '2019-01-01', to: '2021-12-31', desc: 'Төмөр замын оффтейк гэрээнүүд' },
        { id: 'EXPOSED', label: '3. Илчлэлт & Тэмцэл (2022)', from: '2022-01-01', to: '2022-12-31', desc: 'Онцгой дэглэм, талбайн жагсаал, баривчилгаа' },
        { id: 'HEARING', label: '4. Нийтийн сонсгол (2023)', from: '2023-01-01', to: '2023-12-31', desc: 'УИХ-ын Түр хорооны нээлттэй сонсгол' },
        { id: 'VERDICT', label: '5. Шүүхийн шийдвэр (2024)', from: '2024-01-01', to: '2026-12-31', desc: 'Ял шийтгэл, хөрөнгө хураалт' },
      ]
    }
    // Бусад ерөнхий хэргүүдэд
    const years = sortedFacts.map((f) => f.fact_date?.slice(0, 4)).filter(Boolean)
    const uniqueYears = [...new Set(years)].sort()
    const yearStages = uniqueYears.map((yr) => ({
      id: `Y_${yr}`,
      label: `${yr} он`,
      from: `${yr}-01-01`,
      to: `${yr}-12-31`,
      desc: `${yr} оны үйл явдлууд`
    }))
    return [{ id: 'ALL', label: 'Бүх цаг үе', desc: 'Бүх баримт' }, ...yearStages]
  }, [slug, sortedFacts])

  // Идэвхтэй баримтын огнооны хязгаар
  const activeCutoffDate = useMemo(() => {
    if (timeIndex !== null && sortedFacts[timeIndex]) {
      return sortedFacts[timeIndex].fact_date
    }
    const currentStage = STAGES.find((s) => s.id === activeStage)
    if (currentStage && currentStage.to) {
      return currentStage.to
    }
    return null
  }, [timeIndex, sortedFacts, activeStage, STAGES])

  const activeStartDate = useMemo(() => {
    const currentStage = STAGES.find((s) => s.id === activeStage)
    if (currentStage && currentStage.from && timeIndex === null) {
      return currentStage.from
    }
    return null
  }, [activeStage, STAGES, timeIndex])

  // Автомат тоглуулагч (Timeline Auto Playback)
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        setTimeIndex((prev) => {
          if (prev === null) return 0
          if (prev >= sortedFacts.length - 1) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, 1600)
    } else {
      clearInterval(playTimerRef.current)
    }
    return () => clearInterval(playTimerRef.current)
  }, [isPlaying, sortedFacts.length])

  // D3 force simulation ажиллуулах
  useEffect(() => {
    if (!data?.graph) return

    const nodes = data.graph.nodes.map((n, i) => ({
      ...n,
      x: n.x ?? (size.w / 2 + (Math.random() - 0.5) * 160),
      y: n.y ?? (size.h / 2 + (Math.random() - 0.5) * 160),
      idx: i
    }))

    const idSet = new Set(nodes.map((n) => String(n.id)))
    const links = (data.graph.edges || [])
      .filter((e) => idSet.has(String(e.source)) && idSet.has(String(e.target)))
      .map((e) => ({ ...e }))

    simNodes.current = nodes
    simEdges.current = links

    const sim = forceSimulation(nodes)
      .force(
        'link',
        forceLink(links)
          .id((d) => d.id)
          .distance((d) => {
            if (d.source.is_center || d.target.is_center) return 150
            if (d.is_fact_edge || d.source.entity_type === 'fact' || d.target.entity_type === 'fact') return 65
            if (d.is_master_rel) return 90
            return 95
          })
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
          setActiveTab('entity_timeline')
        })
        .catch(() => setEntityActivity(null))
        .finally(() => setActivityLoading(false))
    } else {
      setEntityActivity(null)
      if (activeTab === 'entity_timeline') setActiveTab('case_timeline')
    }
  }, [selectedNode, slug])

  // Drag handlers
  function startDrag(event, d) {
    event.stopPropagation()
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

  // Цаг хугацааны шалгуураар Node болон Edge харагдах эсэх
  const isNodeVisibleInTime = (node) => {
    if (node.is_center) return true
    if (!activeCutoffDate && !activeStartDate) return true

    const nDate = node.date || node.first_date
    if (!nDate) return true // Огноогүй бол бүх цаг үед харуулна

    if (activeStartDate && nDate < activeStartDate) return false
    if (activeCutoffDate && nDate > activeCutoffDate) return false
    return true
  }

  // Сонгогдсон node-той холбоотой edge, node-уудыг тодорхойлох (Highlighting & Dimming)
  const connectedNodeIds = useMemo(() => {
    if (!selectedNode || !simEdges.current) return null
    const set = new Set([String(selectedNode.id)])
    for (const e of simEdges.current) {
      const sId = String(typeof e.source === 'object' ? e.source.id : e.source)
      const tId = String(typeof e.target === 'object' ? e.target.id : e.target)
      const selId = String(selectedNode.id)
      if (sId === selId) set.add(tId)
      if (tId === selId) set.add(sId)
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

  // Хэргийн хамгийн эхний ба сүүлчийн огноо
  const firstCaseDate = sortedFacts[0]?.fact_date || '2018'
  const lastCaseDate = sortedFacts[sortedFacts.length - 1]?.fact_date || '2024'

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)]">
      {/* 1. Дээд толгой: Case Header & Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 mb-2 border-b border-line shrink-0 gap-3">
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
            <h1 className="text-base md:text-lg font-bold font-display text-text truncate max-w-sm md:max-w-md">
              {caseObj.title}
            </h1>
            <Badge tone={caseObj.status === 'PUBLISHED' ? 'ok' : 'warn'}>
              {caseObj.status}
            </Badge>
          </div>
        </div>

        {/* Хугацааны ерөнхий мөчлөг & Тоо баримт */}
        <div className="flex items-center gap-2 md:gap-4 overflow-x-auto">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-surface-2 border border-line rounded text-[11px] font-mono text-dim">
            <Clock size={13} className="text-accent" />
            <span>Хугацаа: <b className="text-text">{firstCaseDate}</b> → <b className="text-text">{lastCaseDate}</b></span>
          </div>

          <div className="hidden sm:flex items-center gap-3 text-xs font-mono text-dim">
            <span>● {summary.entities_count} субъект</span>
            <span>● {summary.edges_count} хамаарал</span>
            <span>● {summary.facts_count} факт</span>
          </div>

          <button
            onClick={() => setActiveTab('add')}
            className="px-3 py-1.5 bg-accent-dim border border-accent-line text-accent font-mono text-xs font-bold rounded flex items-center gap-1.5 hover:bg-accent hover:text-ink-950 transition ml-auto"
          >
            <Plus size={14} /> НЭМЭХ
          </button>
        </div>
      </div>

      {/* 2. Цаг хугацааны удирдлагын хөндлөн самбар (Timeline Controller Bar) */}
      <div className="mb-2 p-2 bg-surface-1/90 border border-line rounded-lg flex flex-col md:flex-row items-center justify-between gap-3 shrink-0 backdrop-blur">
        {/* Stages (Хөгжлийн үе шатууд) */}
        <div className="flex items-center gap-1 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {STAGES.map((st) => (
            <button
              key={st.id}
              onClick={() => {
                setActiveStage(st.id)
                setTimeIndex(null)
                setIsPlaying(false)
              }}
              className={`px-2.5 py-1 text-[11px] font-mono rounded whitespace-nowrap transition flex items-center gap-1 ${
                activeStage === st.id && timeIndex === null
                  ? 'bg-accent text-ink-950 font-bold shadow-[0_0_12px_rgb(56_224_255/0.25)]'
                  : 'text-dim hover:text-text hover:bg-surface-2'
              }`}
              title={st.desc}
            >
              {st.label}
            </button>
          ))}
        </div>

        {/* Playback & Slider */}
        <div className="flex items-center gap-2 w-full md:w-auto justify-between md:justify-end">
          <button
            onClick={() => {
              if (timeIndex === null) setTimeIndex(0)
              setIsPlaying(!isPlaying)
            }}
            className="px-2.5 py-1 bg-surface-2 hover:bg-surface-3 border border-line text-text rounded font-mono text-xs flex items-center gap-1.5 transition"
            title="Он цагийн хэлхээсээр тоглуулах"
          >
            {isPlaying ? <Pause size={13} className="text-accent" /> : <Play size={13} className="text-accent" />}
            <span>{isPlaying ? 'ЗОГСООХ' : 'ХРОНОЛОГИ ҮЗЭХ'}</span>
          </button>

          {timeIndex !== null && (
            <button
              onClick={() => {
                setTimeIndex(null)
                setIsPlaying(false)
                setActiveStage('ALL')
              }}
              className="p-1 text-dim hover:text-text rounded hover:bg-surface-2 transition"
              title="Бүх цаг үеийг харах"
            >
              <RotateCcw size={14} />
            </button>
          )}

          {/* Slider for exact moment */}
          <div className="flex items-center gap-2 pl-2 border-l border-line">
            <span className="text-[10px] font-mono text-dim whitespace-nowrap">
              {activeCutoffDate ? `Хүртэл: ${activeCutoffDate}` : 'Бүх цаг'}
            </span>
            <input
              type="range"
              min={0}
              max={Math.max(sortedFacts.length - 1, 0)}
              value={timeIndex !== null ? timeIndex : sortedFacts.length - 1}
              onChange={(e) => {
                setTimeIndex(Number(e.target.value))
                setIsPlaying(false)
              }}
              className="w-24 md:w-32 accent-accent cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* 3. Үндсэн агуулга: Canvas (зүүн) + Drawer/Inspector (баруун) */}
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
                  const s = typeof e.source === 'object' ? e.source : simNodes.current.find((n) => String(n.id) === String(e.source))
                  const t = typeof e.target === 'object' ? e.target : simNodes.current.find((n) => String(n.id) === String(e.target))
                  if (!s || !t) return null

                  const sVisible = isNodeVisibleInTime(s)
                  const tVisible = isNodeVisibleInTime(t)
                  if (!sVisible || !tVisible) return null

                  const isConnected =
                    !connectedNodeIds || (connectedNodeIds.has(String(s.id)) && connectedNodeIds.has(String(t.id)))
                  const opacity = isConnected ? 0.85 : 0.06

                  const isCenterLink = s.is_center || t.is_center
                  const isMasterRel = e.is_master_rel || (!isCenterLink && !e.is_fact_edge && s.entity_type !== 'fact' && t.entity_type !== 'fact')
                  const isFactRel = e.is_fact_edge || s.entity_type === 'fact' || t.entity_type === 'fact'

                  const strokeColor = isCenterLink
                    ? '#38e0ff'
                    : isMasterRel
                    ? '#f59e0b'
                    : '#64748b'

                  const strokeWidth = isConnected
                    ? (isMasterRel ? 2 : isCenterLink ? 1.5 : 1.2)
                    : 1

                  return (
                    <g key={idx}>
                      <line
                        x1={s.x}
                        y1={s.y}
                        x2={t.x}
                        y2={t.y}
                        stroke={strokeColor}
                        strokeWidth={strokeWidth}
                        strokeDasharray={isCenterLink ? '4 2' : isFactRel ? '2 2' : 'none'}
                        strokeOpacity={opacity}
                      />
                      {e.rel_type && isConnected && (
                        <text
                          x={(s.x + t.x) / 2}
                          y={(s.y + t.y) / 2 - 4}
                          fill={isMasterRel ? '#fbbf24' : '#94a3b8'}
                          fontSize="9"
                          fontFamily="var(--font-sans), sans-serif"
                          fontWeight="500"
                          textAnchor="middle"
                          opacity={opacity}
                          className="pointer-events-none drop-shadow"
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
                  if (!isNodeVisibleInTime(node)) return null

                  const isSelected = selectedNode && String(selectedNode.id) === String(node.id)
                  const isConnected = !connectedNodeIds || connectedNodeIds.has(String(node.id))
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
                        fontFamily="var(--font-sans), sans-serif"
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
                        fontFamily="var(--font-sans), sans-serif"
                        fontWeight={isSelected ? '600' : 'normal'}
                        className="pointer-events-none drop-shadow"
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
          <div className="absolute bottom-3 left-3 bg-surface-1/90 border border-line backdrop-blur p-2 rounded text-[11px] font-mono text-dim pointer-events-none max-w-sm">
            {selectedNode ? (
              <span className="text-text">Сонгосон: <b className="text-accent">{selectedNode.name}</b></span>
            ) : (
              <span>Node дээр дарж фокуслах, баруун самбарт бүрэн түүх, нотолгоог үзнэ үү</span>
            )}
          </div>
        </div>

        {/* Баруун талын Drawer / Inspector & Case Timeline Panel */}
        <div className="w-80 md:w-96 border-l border-line bg-surface-1 flex flex-col shrink-0">
          {/* Tabs */}
          <div className="flex border-b border-line bg-surface-2/60">
            <button
              onClick={() => setActiveTab('case_timeline')}
              className={`flex-1 py-2.5 text-[11px] font-mono font-bold flex items-center justify-center gap-1 border-b-2 transition ${
                activeTab === 'case_timeline'
                  ? 'border-accent text-accent bg-surface-1'
                  : 'border-transparent text-dim hover:text-text'
              }`}
            >
              <Clock size={13} /> ХЭРГИЙН ТҮҮХ
            </button>
            <button
              onClick={() => setActiveTab('inspector')}
              className={`flex-1 py-2.5 text-[11px] font-mono font-bold flex items-center justify-center gap-1 border-b-2 transition ${
                activeTab === 'inspector'
                  ? 'border-accent text-accent bg-surface-1'
                  : 'border-transparent text-dim hover:text-text'
              }`}
            >
              <Info size={13} /> ИНСПЕКТОР
            </button>
            <button
              onClick={() => setActiveTab('entity_timeline')}
              disabled={!selectedNode || typeof selectedNode.id !== 'number'}
              className={`flex-1 py-2.5 text-[11px] font-mono font-bold flex items-center justify-center gap-1 border-b-2 transition disabled:opacity-30 ${
                activeTab === 'entity_timeline'
                  ? 'border-accent text-accent bg-surface-1'
                  : 'border-transparent text-dim hover:text-text'
              }`}
            >
              <Activity size={13} /> СУБЪЕКТ
            </button>
            <button
              onClick={() => setActiveTab('add')}
              className={`px-3 py-2.5 text-[11px] font-mono font-bold flex items-center justify-center gap-1 border-b-2 transition ${
                activeTab === 'add'
                  ? 'border-accent text-accent bg-surface-1'
                  : 'border-transparent text-dim hover:text-text'
              }`}
              title="Шинэ субъект холбох"
            >
              <Plus size={14} />
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* 1. Хэргийн бүрэн цаг хугацааны хэлхээс (Case Timeline) */}
            {activeTab === 'case_timeline' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-line">
                  <div className="text-xs font-mono font-bold text-text flex items-center gap-1.5">
                    <Clock size={13} className="text-accent" />
                    ОН ЦАГИЙН ДАРААЛАЛ ({sortedFacts.length})
                  </div>
                  <span className="text-[10px] font-mono text-dim">
                    {firstCaseDate.slice(0, 4)} — {lastCaseDate.slice(0, 4)}
                  </span>
                </div>

                <div className="space-y-2.5">
                  {sortedFacts.map((fact, idx) => {
                    const isPassed = !activeCutoffDate || fact.fact_date <= activeCutoffDate
                    const isSelectedFact = selectedNode?.entity_type === 'fact' && selectedNode?.fact_id === fact.id

                    return (
                      <div
                        key={fact.id}
                        onClick={() => {
                          const n = simNodes.current.find((sn) => sn.fact_id === fact.id)
                          if (n) setSelectedNode(n)
                        }}
                        className={`p-2.5 rounded border transition cursor-pointer ${
                          isSelectedFact
                            ? 'bg-accent-dim/40 border-accent shadow-[0_0_12px_rgb(56_224_255/0.15)]'
                            : isPassed
                            ? 'bg-surface-2 border-line hover:border-accent-line'
                            : 'bg-surface-1/40 border-line/40 opacity-40'
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] font-mono text-dim mb-1">
                          <span className="flex items-center gap-1 text-accent font-bold">
                            <Calendar size={11} /> {fact.fact_date || 'Огноогүй'}
                          </span>
                          <span className="text-faint">{fact.topic || fact.fact_type}</span>
                        </div>

                        <p className="text-xs text-text leading-relaxed">
                          {fact.fact_text}
                        </p>

                        {fact.source_title && (
                          <div className="mt-1.5 pt-1.5 border-t border-line/60 flex items-center justify-between text-[9px] font-mono text-dim">
                            <span className="truncate max-w-[200px]">{fact.source_title}</span>
                            {fact.sha256 && (
                              <span className="text-ok flex items-center gap-0.5">
                                <ShieldCheck size={10} /> SHA-256
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* 2. Inspector Tab (Node-ийн нарийвчилсан мэдээлэл) */}
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

                    {/* Хэрэв entity бол */}
                    {typeof selectedNode.id === 'number' && (
                      <div className="space-y-4 pt-3 border-t border-line">
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

                        {entities.find((e) => e.id === selectedNode.id)?.description && (
                          <p className="text-xs text-dim leading-relaxed bg-surface-2 p-2.5 rounded border border-line">
                            {entities.find((e) => e.id === selectedNode.id).description}
                          </p>
                        )}

                        {/* Холбогдох бусад субъектүүд (Direct Connected Entities with Jump) */}
                        {(() => {
                          const connected = []
                          const sId = selectedNode.id
                          for (const e of simEdges.current) {
                            const srcId = typeof e.source === 'object' ? e.source.id : e.source
                            const tgtId = typeof e.target === 'object' ? e.target.id : e.target
                            if (srcId === sId && typeof tgtId === 'number') {
                              const otherNode = simNodes.current.find((n) => n.id === tgtId)
                              if (otherNode) connected.push({ node: otherNode, role: e.rel_type, dir: 'out' })
                            } else if (tgtId === sId && typeof srcId === 'number') {
                              const otherNode = simNodes.current.find((n) => n.id === srcId)
                              if (otherNode) connected.push({ node: otherNode, role: e.rel_type, dir: 'in' })
                            }
                          }
                          if (!connected.length) return null

                          return (
                            <div className="space-y-2 pt-2 border-t border-line/60">
                              <div className="text-[11px] font-mono text-dim font-bold flex items-center justify-between">
                                <span>ХОЛБОГДОХ СУБЪЕКТҮҮД ({connected.length})</span>
                                <span className="text-[9px] text-faint">дарж үсрэх</span>
                              </div>
                              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                                {connected.map((item, idx) => (
                                  <button
                                    key={idx}
                                    type="button"
                                    onClick={() => {
                                      setSelectedNode(item.node)
                                      setActiveTab('inspector')
                                    }}
                                    className="w-full p-2 bg-surface-2 hover:bg-surface-3 hover:border-accent-line border border-line rounded flex items-center justify-between text-left transition group"
                                  >
                                    <div className="min-w-0 pr-2">
                                      <div className="text-xs font-bold text-text group-hover:text-accent truncate">
                                        {item.node.name}
                                      </div>
                                      <div className="text-[10px] font-mono text-dim flex items-center gap-1.5 mt-0.5">
                                        <span className="text-accent">{item.role || 'холбоотой'}</span>
                                        <span>• {item.node.entity_type}</span>
                                      </div>
                                    </div>
                                    <ArrowRight size={13} className="text-dim group-hover:text-accent group-hover:translate-x-0.5 transition shrink-0" />
                                  </button>
                                ))}
                              </div>
                            </div>
                          )
                        })()}

                        {/* Шууд баримтууд & Эх сурвалжийн жагсаалт */}
                        {(() => {
                          const entityFacts = facts.filter((f) => f.entity_id === selectedNode.id)
                          if (!entityFacts.length) return null

                          return (
                            <div className="space-y-2.5 pt-2 border-t border-line/60">
                              <div className="text-[11px] font-mono font-bold text-accent flex items-center justify-between">
                                <span>ЭНЭ СУБЪЕКТИЙН БАРИМТУУД ({entityFacts.length})</span>
                                <span className="text-[9px] text-dim font-normal">нотлох эх сурвалжтай</span>
                              </div>
                              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                                {entityFacts.map((fact) => (
                                  <div
                                    key={fact.id}
                                    className="p-2.5 bg-surface-2/90 border border-line rounded space-y-1.5 hover:border-accent-line/60 transition"
                                  >
                                    <div className="flex items-center justify-between text-[10px] font-mono text-dim">
                                      <span className="flex items-center gap-1 text-accent font-bold">
                                        <Calendar size={11} /> {fact.fact_date || 'Огноогүй'}
                                      </span>
                                      <span className="text-faint uppercase text-[9px]">
                                        {fact.topic || fact.fact_type}
                                      </span>
                                    </div>

                                    <p className="text-xs text-text leading-relaxed">
                                      {fact.fact_text}
                                    </p>

                                    {fact.source_quote && (
                                      <blockquote className="border-l-2 border-accent pl-2 text-[11px] text-dim italic">
                                        "{fact.source_quote}"
                                      </blockquote>
                                    )}

                                    {/* Source Link and SHA-256 */}
                                    <div className="pt-1.5 border-t border-line/50 flex flex-col gap-1 text-[10px] font-mono">
                                      {fact.source_url ? (
                                        <a
                                          href={fact.source_url}
                                          target="_blank"
                                          rel="noreferrer"
                                          className="text-accent hover:underline flex items-center gap-1 truncate"
                                        >
                                          <ExternalLink size={11} />
                                          <span className="truncate">{fact.source_title || fact.source_url}</span>
                                        </a>
                                      ) : fact.source_title ? (
                                        <span className="text-dim truncate">{fact.source_title}</span>
                                      ) : null}

                                      {fact.sha256 && (
                                        <div className="flex items-center gap-1 text-[9px] text-ok font-mono bg-ink-950/80 px-1.5 py-0.5 rounded border border-ok/20">
                                          <ShieldCheck size={11} className="shrink-0" />
                                          <span className="truncate select-all">SHA: {fact.sha256.slice(0, 20)}…</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        })()}

                        <button
                          onClick={() => setActiveTab('entity_timeline')}
                          className="w-full py-2 bg-surface-2 hover:bg-surface-3 border border-line text-xs font-mono text-text rounded flex items-center justify-center gap-2 transition"
                        >
                          <Activity size={14} className="text-accent" />
                          Субъектийн хэрэг дэх бүтэн түүхийг шүүх
                        </button>
                      </div>
                    )}

                    {/* Хэрэв Fact node бол */}
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
                                <div className="p-2 bg-surface-2 border border-line rounded flex items-center justify-between">
                                  <div className="text-[11px] font-mono text-dim truncate mr-2">
                                    {fact.source_title || 'Эх сурвалж'}
                                  </div>
                                  <a
                                    href={fact.source_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-xs text-accent hover:underline flex items-center gap-1 shrink-0 font-mono font-bold"
                                  >
                                    Линк нээх <ExternalLink size={12} />
                                  </a>
                                </div>
                              )}

                              {/* Харьяалагдах субъект рүү үсрэх */}
                              {fact.entity_id && (() => {
                                const parentEnt = entities.find((e) => e.id === fact.entity_id)
                                const parentNode = simNodes.current.find((n) => n.id === fact.entity_id)
                                if (!parentEnt) return null
                                return (
                                  <div className="pt-2 border-t border-line/60">
                                    <div className="text-[10px] font-mono text-dim mb-1">ХАРЬЯАЛАГДАХ СУБЪЕКТ:</div>
                                    <button
                                      type="button"
                                      onClick={() => {
                                        if (parentNode) {
                                          setSelectedNode(parentNode)
                                          setActiveTab('inspector')
                                        }
                                      }}
                                      className="w-full p-2 bg-surface-2 hover:bg-surface-3 hover:border-accent-line border border-line rounded flex items-center justify-between text-left transition group"
                                    >
                                      <span className="text-xs font-bold text-text group-hover:text-accent truncate">
                                        {parentEnt.name}
                                      </span>
                                      <ArrowRight size={13} className="text-dim group-hover:text-accent group-hover:translate-x-0.5 transition shrink-0" />
                                    </button>
                                  </div>
                                )
                              })()}
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

            {/* 3. Entity Timeline Tab */}
            {activeTab === 'entity_timeline' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-line">
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

            {/* 4. Add Link Tab */}
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
