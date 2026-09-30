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
  Sparkles,
  Printer,
  FileDown,
  Quote,
  Coins,
  Crown,
  Scale,
  DollarSign,
  ChevronsLeft,
  ChevronsRight
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
  const [layoutMode, setLayoutMode] = useState('force') // 'force' | 'timeline' | 'cluster'
  const [dragMode, setDragMode] = useState('elastic') // 'elastic' | 'local' | 'rigid'

  // Timeline / Entity activity state
  const [entityActivity, setEntityActivity] = useState(null)
  const [activityLoading, setActivityLoading] = useState(false)

  // Цаг хугацааны шүүлтүүр (Chronological Timeline Filter & Playback)
  const [activeStage, setActiveStage] = useState('ALL') // 'ALL' | 'ORIGIN' | 'OFFTAKE' | 'EXPOSED' | 'HEARING' | 'VERDICT'
  const [timeIndex, setTimeIndex] = useState(null) // null = all time, or index in sortedFacts
  const [isPlaying, setIsPlaying] = useState(false)
  const playTimerRef = useRef(null)

  // Баруун талын Drawer өргөн, хэмжээ, хайлтын төлөв
  const [drawerWidth, setDrawerWidth] = useState(540)
  const [isDraggingDrawer, setIsDraggingDrawer] = useState(false)
  const [isFullscreenDrawer, setIsFullscreenDrawer] = useState(false)
  const [timelineSearch, setTimelineSearch] = useState('')
  const [timelineRoleFilter, setTimelineRoleFilter] = useState('ALL')
  const [timelineEntityFilter, setTimelineEntityFilter] = useState(null)
  const [timelineYearFilter, setTimelineYearFilter] = useState('ALL')
  const [groupByYear, setGroupByYear] = useState(true)

  // Subgraph nodes & edges layout
  const wrapRef = useRef(null)
  const svgRef = useRef(null)
  const simRef = useRef(null)
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

  // Цагийн хязгаар (Timeline Layout-д ашиглах жилийн хязгаар)
  const yearBounds = useMemo(() => {
    const years = []
    if (data?.facts) {
      for (const f of data.facts) {
        if (f.fact_date) {
          const yr = parseInt(f.fact_date.slice(0, 4), 10)
          if (!isNaN(yr)) years.push(yr)
        }
      }
    }
    if (data?.graph?.nodes) {
      for (const n of data.graph.nodes) {
        if (n.date) {
          const yr = parseInt(n.date.slice(0, 4), 10)
          if (!isNaN(yr)) years.push(yr)
        }
        if (n.first_date) {
          const yr = parseInt(n.first_date.slice(0, 4), 10)
          if (!isNaN(yr)) years.push(yr)
        }
      }
    }
    if (years.length > 0) {
      const minY = Math.min(...years)
      const maxY = Math.max(...years)
      return [minY, Math.max(maxY, minY + 1)]
    }
    return [2010, 2026]
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

  // Баруун самбарын өргөн чирж өөрчлөх
  const handleMouseDownResize = (e) => {
    e.preventDefault()
    setIsDraggingDrawer(true)
    const startX = e.clientX
    const startW = drawerWidth

    const onMouseMove = (ev) => {
      const deltaX = startX - ev.clientX
      const maxW = Math.max(360, Math.min(window.innerWidth - 260, startW + deltaX))
      setDrawerWidth(maxW)
    }

    const onMouseUp = () => {
      setIsDraggingDrawer(false)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
  }

  // Гол тоглогчид / Оролцооны бүлэглэл (Шийдвэр гаргагчид, Ашиг хүртэгчид, Яллагдагчид)
  const keyPlayers = useMemo(() => {
    if (!data?.links || !data?.entities) {
      return { suspects: [], beneficiaries: [], decisionMakers: [], all: [] }
    }
    const entMap = {}
    for (const e of data.entities) {
      entMap[e.id] = e
    }

    const suspects = []
    const beneficiaries = []
    const decisionMakers = []
    const others = []

    for (const l of data.links) {
      if (!l.entity_id || !entMap[l.entity_id]) continue
      const item = { ...entMap[l.entity_id], role: l.role, note: l.note, link_id: l.id }
      if (l.role === 'SUSPECT') suspects.push(item)
      else if (l.role === 'BENEFICIARY') beneficiaries.push(item)
      else if (l.role === 'DECISION_MAKER') decisionMakers.push(item)
      else others.push(item)
    }

    return { suspects, beneficiaries, decisionMakers, others }
  }, [data])

  // Боломжит он жилүүд
  const availableYears = useMemo(() => {
    const yrs = new Set()
    for (const f of sortedFacts) {
      if (f.fact_date) {
        const y = f.fact_date.slice(0, 4)
        if (y && !isNaN(parseInt(y, 10))) yrs.add(y)
      }
    }
    return Array.from(yrs).sort()
  }, [sortedFacts])

  // Шүүлтүүртэй фактууд
  const filteredTimelineFacts = useMemo(() => {
    return sortedFacts.filter((f) => {
      // 1. Cutoff date filter
      if (activeCutoffDate && f.fact_date && f.fact_date > activeCutoffDate) {
        return false
      }
      if (activeStartDate && f.fact_date && f.fact_date < activeStartDate) {
        return false
      }

      // 2. Text search
      if (timelineSearch.trim()) {
        const q = timelineSearch.toLowerCase().trim()
        const textMatch = f.fact_text?.toLowerCase().includes(q)
        const quoteMatch = f.source_quote?.toLowerCase().includes(q)
        const topicMatch = f.topic?.toLowerCase().includes(q)
        const entMatch = f.entity_name?.toLowerCase().includes(q)
        const sourceMatch = f.source_title?.toLowerCase().includes(q)
        const roleMatch = f.role_context?.toLowerCase().includes(q)
        if (!textMatch && !quoteMatch && !topicMatch && !entMatch && !sourceMatch && !roleMatch) {
          return false
        }
      }

      // 3. Year filter
      if (timelineYearFilter !== 'ALL') {
        if (!f.fact_date || !f.fact_date.startsWith(timelineYearFilter)) return false
      }

      // 4. Entity filter
      if (timelineEntityFilter !== null) {
        if (f.entity_id !== timelineEntityFilter) return false
      }

      // 5. Role filter
      if (timelineRoleFilter !== 'ALL') {
        const matchingLink = data?.links?.find((l) => l.entity_id === f.entity_id)
        if (!matchingLink || matchingLink.role !== timelineRoleFilter) return false
      }

      return true
    })
  }, [
    sortedFacts,
    activeCutoffDate,
    activeStartDate,
    timelineSearch,
    timelineYearFilter,
    timelineEntityFilter,
    timelineRoleFilter,
    data,
  ])

  // Жилээр бүлэглэх
  const factsGroupedByYear = useMemo(() => {
    const groups = {}
    for (const f of filteredTimelineFacts) {
      const yr = f.fact_date ? f.fact_date.slice(0, 4) : 'Он тодорхойгүй'
      if (!groups[yr]) groups[yr] = []
      groups[yr].push(f)
    }
    return Object.entries(groups).map(([year, list]) => ({ year, list }))
  }, [filteredTimelineFacts])

  // Мөнгөн дүн болон онцлох утгуудыг тодотгох туслах функц
  const formatFactText = (text) => {
    if (!text) return ''
    const regex = /(\b\d+(?:\.\d+)?\s*(?:их наяд|тэрбум|сая|сая тонн|хувь|%|\$|USD|₮)\b)/gi
    const parts = text.split(regex)
    return parts.map((part, i) => {
      if (regex.test(part)) {
        return (
          <span
            key={i}
            className="font-bold text-accent bg-accent/10 px-1 py-0.5 rounded border border-accent/20 mx-0.5"
          >
            {part}
          </span>
        )
      }
      return part
    })
  }

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

  // D3 force simulation ажиллуулах (Layout Mode-оор ялгана)
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

    if (layoutMode === 'timeline') {
      // 1. Хронологи / Он цагийн хуваарилалт (Timeline Swimlane Layout)
      const [minY, maxY] = yearBounds
      sim
        .force(
          'link',
          forceLink(links)
            .id((d) => d.id)
            .distance(90)
            .strength(0.3)
        )
        .force('charge', forceManyBody().strength(-280))
        .force('collide', forceCollide().radius((d) => (d.is_center ? 45 : d.entity_type === 'fact' ? 22 : 36)).iterations(2))
        .force(
          'x',
          forceX((d) => {
            if (d.is_center) return size.w * 0.12
            const dateStr = d.date || d.first_date
            const yr = dateStr ? parseInt(dateStr.slice(0, 4), 10) : (minY + maxY) / 2
            const progress = (yr - minY) / Math.max(maxY - minY, 1)
            return size.w * 0.22 + progress * (size.w * 0.70)
          }).strength(0.85)
        )
        .force(
          'y',
          forceY((d) => {
            if (d.is_center) return size.h * 0.5
            if (d.entity_type === 'person') return size.h * 0.28
            if (d.entity_type === 'company') return size.h * 0.50
            if (d.entity_type === 'org' || d.entity_type === 'government') return size.h * 0.72
            if (d.entity_type === 'fact') return size.h * 0.86
            return size.h * 0.5
          }).strength(0.65)
        )
    } else if (layoutMode === 'cluster') {
      // 2. Субъектийн төрлөөр баганачлах (Entity Types Cluster Layout)
      const cx = size.w / 2
      const cy = size.h / 2
      const centers = {
        case: { x: cx, y: cy },
        person: { x: cx - size.w * 0.28, y: cy - size.h * 0.22 },
        company: { x: cx + size.w * 0.28, y: cy - size.h * 0.22 },
        org: { x: cx - size.w * 0.25, y: cy + size.h * 0.25 },
        government: { x: cx - size.w * 0.25, y: cy + size.h * 0.25 },
        parliament: { x: cx - size.w * 0.25, y: cy + size.h * 0.25 },
        fact: { x: cx + size.w * 0.25, y: cy + size.h * 0.25 },
        other: { x: cx, y: cy + size.h * 0.32 },
      }

      sim
        .force(
          'link',
          forceLink(links)
            .id((d) => d.id)
            .distance(110)
            .strength(0.35)
        )
        .force('charge', forceManyBody().strength(-350))
        .force('collide', forceCollide().radius((d) => (d.is_center ? 45 : d.entity_type === 'fact' ? 22 : 36)).iterations(2))
        .force(
          'x',
          forceX((d) => {
            const c = centers[d.entity_type] || centers.other
            return c.x
          }).strength(0.65)
        )
        .force(
          'y',
          forceY((d) => {
            const c = centers[d.entity_type] || centers.other
            return c.y
          }).strength(0.65)
        )
        .force('center', forceCenter(cx, cy).strength(0.05))
    } else {
      // 3. Стандарт Force Network (Default Concentric/Organic)
      sim
        .force(
          'link',
          forceLink(links)
            .id((d) => d.id)
            .distance((d) => {
              if (d.source.is_center || d.target.is_center) return 180
              if (d.is_fact_edge || d.source.entity_type === 'fact' || d.target.entity_type === 'fact') return 80
              if (d.is_master_rel) return 120
              return 115
            })
            .strength(0.5)
        )
        .force('charge', forceManyBody().strength(-450))
        .force('collide', forceCollide().radius((d) => (d.is_center ? 45 : d.entity_type === 'fact' ? 24 : 38)).iterations(2))
        .force('center', forceCenter(size.w / 2, size.h / 2).strength(0.06))
    }

    sim.stop()
    for (let i = 0; i < TICKS; i++) sim.tick()
    simRef.current = sim
    forceRender((v) => v + 1)

    sim.on('tick', () => {
      forceRender((v) => v + 1)
    })

    return () => {
      sim.stop()
      simRef.current = null
    }
  }, [data, size.w, size.h, layoutMode, yearBounds])

  // Zoom / Pan (Middle mouse support added)
  useEffect(() => {
    if (!svgRef.current) return
    const svg = select(svgRef.current)
    const behavior = d3zoom()
      .scaleExtent([0.2, 4])
      .filter((event) => {
        if (event.type === 'mousedown' || event.type === 'touchstart') {
          if (event.button === 1) return true // Middle mouse button always pans
          if (event.target && event.target.closest && event.target.closest('.case-node')) return false
          return !event.button || event.button === 0
        }
        return true
      })
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

  function svgPoint(event) {
    const svg = svgRef.current
    if (!svg) return { x: event.clientX, y: event.clientY }
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

  // Drag handlers (3 selectable physics modes: Elastic, Local Spring, Rigid Cluster)
  function startDrag(event, d) {
    if (event.button !== 0) return
    event.stopPropagation()
    const pt = svgPoint(event)

    // Хөрш зангилаануудыг олох
    const neighbors = []
    for (const e of simEdges.current) {
      const sId = String(typeof e.source === 'object' ? e.source.id : e.source)
      const tId = String(typeof e.target === 'object' ? e.target.id : e.target)
      const myId = String(d.id)
      if (sId === myId) {
        const neighbor = simNodes.current.find((n) => String(n.id) === tId)
        if (neighbor && String(neighbor.id) !== myId && !neighbors.some((n) => String(n.node.id) === String(neighbor.id))) {
          neighbors.push({ node: neighbor, initX: neighbor.x, initY: neighbor.y, vx: 0, vy: 0 })
        }
      } else if (tId === myId) {
        const neighbor = simNodes.current.find((n) => String(n.id) === sId)
        if (neighbor && String(neighbor.id) !== myId && !neighbors.some((n) => String(n.node.id) === String(neighbor.id))) {
          neighbors.push({ node: neighbor, initX: neighbor.x, initY: neighbor.y, vx: 0, vy: 0 })
        }
      }
    }

    if (dragMode === 'elastic') {
      // 1. Уян пүрш (Live D3 Force): чирч буй node-ийг бэхлэн simulation-ийг асаана
      d.fx = pt.x
      d.fy = pt.y
      if (simRef.current) {
        simRef.current.alphaTarget(0.3).restart()
      }
    }

    dragRef.current = {
      id: d.id,
      node: d,
      initPtX: pt.x,
      initPtY: pt.y,
      initNodeX: d.x,
      initNodeY: d.y,
      currTargetX: pt.x,
      currTargetY: pt.y,
      neighbors,
      animFrame: null,
      moved: false,
    }

    // 2. Локал уян пүрш (Local Spring): инерцийн анимаци эхлүүлэх
    if (dragMode === 'local') {
      const runLocalSpring = () => {
        const st = dragRef.current
        if (!st) return

        const deltaX = st.currTargetX - st.initPtX
        const deltaY = st.currTargetY - st.initPtY
        const targetFollowFactor = 0.55
        const k = 0.18 // Spring stiffness
        const friction = 0.72 // Damping friction

        for (const item of st.neighbors) {
          const desiredX = item.initX + deltaX * targetFollowFactor
          const desiredY = item.initY + deltaY * targetFollowFactor

          const forceX = (desiredX - item.node.x) * k
          const forceY = (desiredY - item.node.y) * k

          item.vx = (item.vx + forceX) * friction
          item.vy = (item.vy + forceY) * friction

          item.node.x += item.vx
          item.node.y += item.vy
        }

        forceRender((v) => v + 1)
        st.animFrame = requestAnimationFrame(runLocalSpring)
      }
      dragRef.current.animFrame = requestAnimationFrame(runLocalSpring)
    }

    window.addEventListener('pointermove', onDragMove)
    window.addEventListener('pointerup', onDragEnd)
  }

  function onDragMove(event) {
    const st = dragRef.current
    if (!st) return
    const d = st.node
    if (!d) return
    const pt = svgPoint(event)
    const deltaX = pt.x - st.initPtX
    const deltaY = pt.y - st.initPtY

    if (Math.hypot(deltaX, deltaY) > 4) st.moved = true
    st.currTargetX = pt.x
    st.currTargetY = pt.y

    if (dragMode === 'elastic') {
      // 1. Уян пүрш (Live D3 Force)
      d.fx = pt.x
      d.fy = pt.y
    } else if (dragMode === 'rigid') {
      // 3. Бүлгээр зөөх (Rigid Cluster): 100% геометрийн хэлбэрээ яг тэр чигт нь хадгалж зөөнө
      d.x = st.initNodeX + deltaX
      d.y = st.initNodeY + deltaY
      for (const item of st.neighbors) {
        item.node.x = item.initX + deltaX
        item.node.y = item.initY + deltaY
      }
      forceRender((v) => v + 1)
    } else {
      // 2. Локал пүрш (Local Spring): үндсэн node-ийг шууд дагуулж, хөршүүд нь анимациар хэлбэлзэн дагана
      d.x = st.initNodeX + deltaX
      d.y = st.initNodeY + deltaY
      forceRender((v) => v + 1)
    }
  }

  function onDragEnd() {
    window.removeEventListener('pointermove', onDragMove)
    window.removeEventListener('pointerup', onDragEnd)

    const st = dragRef.current
    if (st) {
      if (st.animFrame) cancelAnimationFrame(st.animFrame)
      if (dragMode === 'elastic') {
        // Уян пүрш горим дуусах: simulation-ийг зөөлөн тайвшруулна
        if (st.node) {
          st.node.fx = null
          st.node.fy = null
        }
        if (simRef.current) {
          simRef.current.alphaTarget(0)
        }
      }
    }
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
            onClick={() => window.print()}
            title="Энэхүү хэргийн мөрдлөгийн тайлан, нотлох баримтуудыг хэвлэх эсвэл PDF болгон экспортлох"
            className="px-2.5 py-1.5 bg-surface-2 border border-line text-text font-mono text-xs rounded flex items-center gap-1.5 hover:border-accent hover:text-accent transition ml-auto"
          >
            <Printer size={13} />
            <span className="hidden sm:inline">ТАЙЛАН ХЭВЛЭХ / PDF</span>
          </button>

          <button
            onClick={() => setActiveTab('add')}
            className="px-3 py-1.5 bg-accent-dim border border-accent-line text-accent font-mono text-xs font-bold rounded flex items-center gap-1.5 hover:bg-accent hover:text-ink-950 transition"
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
          {/* Floating Layout & Navigation Bar */}
          <div className="absolute top-3 left-3 z-10 flex items-center gap-1.5 p-1 bg-surface-1/90 backdrop-blur border border-line rounded-lg shadow-lg">
            <span className="text-[10px] font-mono text-dim px-2 uppercase tracking-wider hidden sm:inline">Эрэмбэлэлт:</span>
            {[
              { id: 'force', label: '🕸️ Сүлжээ (Force)' },
              { id: 'timeline', label: '⏳ Он цаг (Timeline)' },
              { id: 'cluster', label: '👥 Төрлөөр (Types)' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setLayoutMode(m.id)}
                className={`px-2.5 py-1 text-xs font-mono rounded transition flex items-center gap-1 ${
                  layoutMode === m.id
                    ? 'bg-accent text-ink-950 font-bold shadow-[0_0_10px_rgb(56_224_255/0.25)]'
                    : 'text-dim hover:text-text hover:bg-surface-2'
                }`}
              >
                {m.label}
              </button>
            ))}
            {/* Drag Physics Mode Switcher */}
            <div className="w-[1px] h-4 bg-line mx-1" />
            <span className="text-[10px] font-mono text-dim px-1 uppercase tracking-wider hidden md:inline">Чирэлт:</span>
            {[
              { id: 'elastic', label: '🌊 Уян пүрш', desc: 'Байгалийн пүрш шиг сунаж татагдан, зангилаанууд мөргөлдөхгүй' },
              { id: 'local', label: '🎯 Локал', desc: 'Зөвхөн хөршүүд нь уян резин шиг гулсаж татагдана' },
              { id: 'rigid', label: '🧱 Бүлэг', desc: 'Холбоотой зангилаануудын бүтэц 100% хадгалагдаж нэгэн цул болж зөөгдөнө' },
            ].map((dm) => (
              <button
                key={dm.id}
                onClick={() => setDragMode(dm.id)}
                title={dm.desc}
                className={`px-2 py-1 text-xs font-mono rounded transition flex items-center gap-1 ${
                  dragMode === dm.id
                    ? 'bg-accent/20 border border-accent text-accent font-bold shadow-[0_0_8px_rgb(56_224_255/0.2)]'
                    : 'text-dim hover:text-text hover:bg-surface-2'
                }`}
              >
                {dm.label}
              </button>
            ))}

            <div className="w-[1px] h-4 bg-line mx-1" />
            <span className="text-[10px] font-mono text-faint px-1 hidden lg:inline" title="Хулганы голын дугуй дарж канвас дээр чөлөөтэй хөдөлнө">
              Хулганы хүрд (Pan)
            </span>
          </div>

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
              {/* Timeline Mode Grid & Labels */}
              {layoutMode === 'timeline' && (
                <g className="timeline-guides pointer-events-none opacity-40">
                  {/* Swimlane horizontal guides */}
                  <line x1={size.w * 0.18} y1={size.h * 0.28} x2={size.w * 0.96} y2={size.h * 0.28} stroke="#f59e0b" strokeDasharray="3 4" strokeWidth={0.8} />
                  <text x={size.w * 0.20} y={size.h * 0.28 - 6} fill="#f59e0b" fontSize="10" fontFamily="var(--font-mono)">Улс төрчид / Хувь хүмүүс (Persons)</text>

                  <line x1={size.w * 0.18} y1={size.h * 0.50} x2={size.w * 0.96} y2={size.h * 0.50} stroke="#10b981" strokeDasharray="3 4" strokeWidth={0.8} />
                  <text x={size.w * 0.20} y={size.h * 0.50 - 6} fill="#10b981" fontSize="10" fontFamily="var(--font-mono)">Компаниуд & Банкууд (Companies)</text>

                  <line x1={size.w * 0.18} y1={size.h * 0.72} x2={size.w * 0.96} y2={size.h * 0.72} stroke="#8b5cf6" strokeDasharray="3 4" strokeWidth={0.8} />
                  <text x={size.w * 0.20} y={size.h * 0.72 - 6} fill="#8b5cf6" fontSize="10" fontFamily="var(--font-mono)">Сан & Төрийн байгууллагууд (Institutions)</text>

                  {/* Vertical year lines */}
                  {Array.from({ length: Math.max(yearBounds[1] - yearBounds[0] + 1, 2) }, (_, i) => yearBounds[0] + i)
                    .filter((yr, i, arr) => arr.length <= 10 || yr % 2 === 0)
                    .map((yr) => {
                      const prog = (yr - yearBounds[0]) / Math.max(yearBounds[1] - yearBounds[0], 1)
                      const x = size.w * 0.22 + prog * (size.w * 0.70)
                      return (
                        <g key={yr} transform={`translate(${x}, 0)`}>
                          <line y1={40} y2={size.h - 30} stroke="#38e0ff" strokeDasharray="2 4" strokeWidth={0.6} />
                          <text y={size.h - 10} fill="#38e0ff" fontSize="10" fontFamily="var(--font-mono)" textAnchor="middle">
                            {yr}
                          </text>
                        </g>
                      )
                    })}
                </g>
              )}

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

              {/* Nodes (Circles and Icons) */}
              <g className="nodes">
                {simNodes.current.map((node) => {
                  if (!isNodeVisibleInTime(node)) return null

                  const isSelected = selectedNode && String(selectedNode.id) === String(node.id)
                  const isConnected = !connectedNodeIds || connectedNodeIds.has(String(node.id))
                  const opacity = isConnected ? 1 : 0.15
                  const color = TYPE_COLORS[node.entity_type] || TYPE_COLORS.other
                  const isCenter = !!node.is_center
                  const radius = isCenter ? 24 : node.entity_type === 'fact' ? 11 : 17

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
                    </g>
                  )
                })}
              </g>

              {/* Node Labels (Always rendered on top layer to prevent overlapping by other circles) */}
              <g className="node-labels pointer-events-none">
                {simNodes.current.map((node) => {
                  if (!isNodeVisibleInTime(node)) return null

                  const isSelected = selectedNode && String(selectedNode.id) === String(node.id)
                  const isConnected = !connectedNodeIds || connectedNodeIds.has(String(node.id))
                  const isHovered = hoverNodeId === node.id
                  const opacity = isConnected ? 1 : 0.15
                  const isCenter = !!node.is_center
                  const radius = isCenter ? 24 : node.entity_type === 'fact' ? 11 : 17
                  const label = node.name?.length > 22 ? node.name.slice(0, 20) + '…' : node.name

                  return (
                    <g
                      key={`lbl-${node.id}`}
                      transform={`translate(${node.x}, ${node.y + radius + 13})`}
                      opacity={opacity}
                      className="transition-opacity duration-200"
                    >
                      {/* Text halo stroke to prevent line/grid clutter under the text */}
                      <text
                        textAnchor="middle"
                        fill="none"
                        stroke="#04070a"
                        strokeWidth="3.5"
                        strokeLinejoin="round"
                        fontSize="10"
                        fontFamily="var(--font-sans), sans-serif"
                        fontWeight={isSelected || isHovered ? '600' : '500'}
                      >
                        {label}
                      </text>

                      {/* Foreground label */}
                      <text
                        textAnchor="middle"
                        fill={isSelected || isHovered ? '#38e0ff' : '#d7e7ee'}
                        fontSize="10"
                        fontFamily="var(--font-sans), sans-serif"
                        fontWeight={isSelected || isHovered ? '600' : 'normal'}
                      >
                        {label}
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

        {/* Баруун талын Drawer / Inspector & Case Timeline Panel (Өргөн тохируулгатай, томруулсан горимтой) */}
        <div
          style={{ width: isFullscreenDrawer ? '100%' : `${drawerWidth}px` }}
          className={`border-l border-line bg-surface-1 flex flex-col shrink-0 relative transition-all duration-75 ${
            isFullscreenDrawer ? 'absolute inset-0 z-50 bg-surface-1' : ''
          }`}
        >
          {/* Самбарын өргөн чирэх бариул (Interactive Drag Handle) */}
          {!isFullscreenDrawer && (
            <div
              onMouseDown={handleMouseDownResize}
              className="absolute -left-1.5 top-0 bottom-0 w-3 cursor-col-resize hover:bg-accent/40 active:bg-accent transition z-30 group flex items-center justify-center select-none"
              title="Самбарын өргөнийг чирж өөрчлөх"
            >
              <div className="w-0.5 h-12 rounded-full bg-line group-hover:bg-accent group-active:bg-accent transition" />
            </div>
          )}

          {/* Drawer Top Controls & Tabs */}
          <div className="flex items-center justify-between border-b border-line bg-surface-2/70 px-2 py-1.5 shrink-0 gap-1">
            {/* Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto min-w-0">
              <button
                onClick={() => setActiveTab('case_timeline')}
                className={`px-2.5 py-1.5 text-[11px] font-mono font-bold flex items-center gap-1.5 rounded transition shrink-0 ${
                  activeTab === 'case_timeline'
                    ? 'bg-accent/15 text-accent border border-accent/40 shadow-sm'
                    : 'text-dim hover:text-text hover:bg-surface-3'
                }`}
              >
                <Clock size={13} /> ХЭРГИЙН ТҮҮХ ({sortedFacts.length})
              </button>

              <button
                onClick={() => setActiveTab('inspector')}
                className={`px-2.5 py-1.5 text-[11px] font-mono font-bold flex items-center gap-1.5 rounded transition shrink-0 ${
                  activeTab === 'inspector'
                    ? 'bg-accent/15 text-accent border border-accent/40 shadow-sm'
                    : 'text-dim hover:text-text hover:bg-surface-3'
                }`}
              >
                <Info size={13} /> ИНСПЕКТОР
              </button>

              <button
                onClick={() => setActiveTab('entity_timeline')}
                disabled={!selectedNode || typeof selectedNode.id !== 'number'}
                className={`px-2.5 py-1.5 text-[11px] font-mono font-bold flex items-center gap-1.5 rounded transition disabled:opacity-30 shrink-0 ${
                  activeTab === 'entity_timeline'
                    ? 'bg-accent/15 text-accent border border-accent/40 shadow-sm'
                    : 'text-dim hover:text-text hover:bg-surface-3'
                }`}
              >
                <Activity size={13} /> СУБЪЕКТ
              </button>

              <button
                onClick={() => setActiveTab('add')}
                className={`px-2 py-1.5 text-[11px] font-mono font-bold flex items-center gap-1 rounded transition shrink-0 ${
                  activeTab === 'add'
                    ? 'bg-accent/15 text-accent border border-accent/40 shadow-sm'
                    : 'text-dim hover:text-text hover:bg-surface-3'
                }`}
                title="Шинэ субъект холбох"
              >
                <Plus size={13} />
              </button>
            </div>

            {/* Width Presets & Fullscreen toggle */}
            <div className="flex items-center gap-1 pl-2 border-l border-line/60 shrink-0">
              <button
                onClick={() => {
                  setIsFullscreenDrawer(false)
                  setDrawerWidth(380)
                }}
                className={`px-1.5 py-0.5 text-[10px] font-mono rounded border transition ${
                  !isFullscreenDrawer && drawerWidth <= 400
                    ? 'bg-accent text-ink-950 font-bold border-accent'
                    : 'text-dim hover:text-text border-line bg-surface-1'
                }`}
                title="Компакт өргөн (380px)"
              >
                380
              </button>
              <button
                onClick={() => {
                  setIsFullscreenDrawer(false)
                  setDrawerWidth(540)
                }}
                className={`px-1.5 py-0.5 text-[10px] font-mono rounded border transition ${
                  !isFullscreenDrawer && drawerWidth > 400 && drawerWidth < 680
                    ? 'bg-accent text-ink-950 font-bold border-accent'
                    : 'text-dim hover:text-text border-line bg-surface-1'
                }`}
                title="Өргөн горим (540px) - Тухтай унших"
              >
                540
              </button>
              <button
                onClick={() => {
                  setIsFullscreenDrawer(false)
                  setDrawerWidth(740)
                }}
                className={`px-1.5 py-0.5 text-[10px] font-mono rounded border transition ${
                  !isFullscreenDrawer && drawerWidth >= 680
                    ? 'bg-accent text-ink-950 font-bold border-accent'
                    : 'text-dim hover:text-text border-line bg-surface-1'
                }`}
                title="Хамгийн өргөн горим (740px)"
              >
                740
              </button>

              <button
                onClick={() => setIsFullscreenDrawer(!isFullscreenDrawer)}
                className={`p-1 border rounded transition ml-0.5 ${
                  isFullscreenDrawer
                    ? 'bg-accent text-ink-950 font-bold border-accent'
                    : 'text-dim hover:text-accent border-line bg-surface-1'
                }`}
                title={isFullscreenDrawer ? 'Энгийн горим руу буцах' : 'Бүрэн дэлгэцээр унших'}
              >
                {isFullscreenDrawer ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* 1. Хэргийн бүрэн цаг хугацааны хэлхээс (Case Timeline & Narrative) */}
            {activeTab === 'case_timeline' && (
              <div className="space-y-4">
                {/* 1.1 Хэргийн тойм & Оролцооны бүлэглэл */}
                <div className="p-3.5 bg-surface-2/90 border border-line rounded-lg space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-mono uppercase text-dim tracking-wider">
                        МӨРДЛӨГИЙН ХЭРГИЙН ТОЙМ
                      </div>
                      <h2 className="text-sm font-bold text-text font-display mt-0.5">
                        {caseObj.title}
                      </h2>
                    </div>
                    {caseObj.amount_billion && (
                      <div className="text-right shrink-0">
                        <div className="text-[9px] font-mono text-dim uppercase">Санхүүгийн хэмжээ</div>
                        <div className="text-xs font-mono font-bold text-warn flex items-center justify-end gap-1">
                          <Coins size={12} />
                          {caseObj.amount_billion >= 1000
                            ? `${(caseObj.amount_billion / 1000).toFixed(1)} их наяд ₮`
                            : `${caseObj.amount_billion} тэрбум ₮`}
                        </div>
                      </div>
                    )}
                  </div>

                  {caseObj.description && (
                    <p className="text-xs text-text/90 leading-relaxed border-t border-line/60 pt-2 font-sans">
                      {caseObj.description}
                    </p>
                  )}

                  {/* Гол тоглогчид / Оролцооны ангилал */}
                  <div className="pt-2 border-t border-line/60 space-y-2">
                    <div className="text-[10px] font-mono font-bold text-dim flex items-center justify-between">
                      <span>ХЭРГИЙН ГОЛ ОРОЛЦОО (Дарж фактыг шүүнэ үү):</span>
                      {(timelineRoleFilter !== 'ALL' || timelineEntityFilter !== null) && (
                        <button
                          onClick={() => {
                            setTimelineRoleFilter('ALL')
                            setTimelineEntityFilter(null)
                          }}
                          className="text-[10px] text-accent hover:underline flex items-center gap-0.5"
                        >
                          <RotateCcw size={10} /> Бүгдийг харах
                        </button>
                      )}
                    </div>

                    {/* 👑 Шийдвэр гаргагчид */}
                    {keyPlayers.decisionMakers.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap text-[11px]">
                        <span className="font-mono text-[10px] text-accent font-bold flex items-center gap-1 shrink-0">
                          <Crown size={11} /> Шийдвэр гаргагчид:
                        </span>
                        {keyPlayers.decisionMakers.map((p) => {
                          const isSelected = timelineEntityFilter === p.id
                          return (
                            <button
                              key={p.id}
                              onClick={() => setTimelineEntityFilter(isSelected ? null : p.id)}
                              className={`px-2 py-0.5 rounded text-[11px] font-mono border transition ${
                                isSelected
                                  ? 'bg-accent text-ink-950 font-bold border-accent'
                                  : 'bg-surface-3/80 hover:bg-surface-3 text-text border-line hover:border-accent-line'
                              }`}
                              title={p.note || ''}
                            >
                              {p.name}
                            </button>
                          )
                        })}
                      </div>
                    )}

                    {/* 💰 Хамгийн их ашиг хүртэгчид / Монопол гэрээтнүүд */}
                    {keyPlayers.beneficiaries.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap text-[11px]">
                        <span className="font-mono text-[10px] text-ok font-bold flex items-center gap-1 shrink-0">
                          <DollarSign size={11} /> Ашиг хүртэгчид:
                        </span>
                        {keyPlayers.beneficiaries.map((p) => {
                          const isSelected = timelineEntityFilter === p.id
                          return (
                            <button
                              key={p.id}
                              onClick={() => setTimelineEntityFilter(isSelected ? null : p.id)}
                              className={`px-2 py-0.5 rounded text-[11px] font-mono border transition ${
                                isSelected
                                  ? 'bg-ok text-ink-950 font-bold border-ok'
                                  : 'bg-surface-3/80 hover:bg-surface-3 text-text border-line hover:border-ok-line'
                              }`}
                              title={p.note || ''}
                            >
                              {p.name}
                            </button>
                          )
                        })}
                      </div>
                    )}

                    {/* ⚖️ Сэжигтэн, яллагдагчид */}
                    {keyPlayers.suspects.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap text-[11px]">
                        <span className="font-mono text-[10px] text-danger font-bold flex items-center gap-1 shrink-0">
                          <Scale size={11} /> Сэжигтэн/Яллагдагч:
                        </span>
                        {keyPlayers.suspects.map((p) => {
                          const isSelected = timelineEntityFilter === p.id
                          return (
                            <button
                              key={p.id}
                              onClick={() => setTimelineEntityFilter(isSelected ? null : p.id)}
                              className={`px-2 py-0.5 rounded text-[11px] font-mono border transition ${
                                isSelected
                                  ? 'bg-danger text-white font-bold border-danger'
                                  : 'bg-surface-3/80 hover:bg-surface-3 text-text border-line hover:border-danger/50'
                              }`}
                              title={p.note || ''}
                            >
                              {p.name}
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* 1.2 Хайлт ба шүүлтүүр */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-dim" />
                      <input
                        type="text"
                        placeholder="Фактуудаас хайх (оффтейк, тооцоолол, гэрээ, шүүх, нэр)..."
                        value={timelineSearch}
                        onChange={(e) => setTimelineSearch(e.target.value)}
                        className="w-full pl-8 pr-7 py-1.5 bg-surface-2 border border-line rounded text-xs text-text font-mono focus:border-accent focus:outline-none"
                      />
                      {timelineSearch && (
                        <button
                          onClick={() => setTimelineSearch('')}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-dim hover:text-text"
                        >
                          <X size={12} />
                        </button>
                      )}
                    </div>

                    <button
                      onClick={() => setGroupByYear(!groupByYear)}
                      className={`px-2.5 py-1.5 border rounded text-[11px] font-mono flex items-center gap-1 transition shrink-0 ${
                        groupByYear
                          ? 'bg-accent/15 text-accent border-accent/40'
                          : 'bg-surface-2 text-dim border-line hover:text-text'
                      }`}
                      title="Жилээр бүлэглэх"
                    >
                      <Layers size={12} />
                      <span className="hidden sm:inline">Жилээр</span>
                    </button>
                  </div>

                  {/* Он сонгох чипүүд */}
                  {availableYears.length > 1 && (
                    <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[11px] font-mono">
                      <span className="text-dim shrink-0 text-[10px]">Он:</span>
                      <button
                        onClick={() => setTimelineYearFilter('ALL')}
                        className={`px-2 py-0.5 rounded border transition shrink-0 ${
                          timelineYearFilter === 'ALL'
                            ? 'bg-accent text-ink-950 font-bold border-accent'
                            : 'bg-surface-2 text-dim border-line hover:text-text'
                        }`}
                      >
                        Бүгд ({sortedFacts.length})
                      </button>
                      {availableYears.map((yr) => (
                        <button
                          key={yr}
                          onClick={() => setTimelineYearFilter(yr)}
                          className={`px-2 py-0.5 rounded border transition shrink-0 ${
                            timelineYearFilter === yr
                              ? 'bg-accent text-ink-950 font-bold border-accent'
                              : 'bg-surface-2 text-dim border-line hover:text-text'
                          }`}
                        >
                          {yr}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Идэвхтэй шүүлтүүрийн мэдээлэл */}
                  <div className="flex items-center justify-between text-[11px] font-mono text-dim pt-1 border-t border-line/40">
                    <span>
                      Илэрц: <b className="text-text">{filteredTimelineFacts.length}</b> баримт
                    </span>
                    <span className="text-[10px]">
                      {firstCaseDate.slice(0, 4)} — {lastCaseDate.slice(0, 4)}
                    </span>
                  </div>
                </div>

                {/* 1.3 Баримтуудын жагсаалт (Rich cards with visual timeline spine) */}
                <div className="space-y-4">
                  {filteredTimelineFacts.length === 0 ? (
                    <div className="p-8 text-center bg-surface-2/40 border border-line rounded-lg text-dim text-xs font-mono">
                      Шүүлтүүрт тохирох баримт олдсонгүй.
                    </div>
                  ) : groupByYear ? (
                    factsGroupedByYear.map(({ year, list }) => (
                      <div key={year} className="space-y-2.5">
                        <div className="sticky top-0 z-10 py-1 px-2.5 bg-surface-1/95 backdrop-blur border-b border-line flex items-center justify-between text-xs font-mono font-bold text-accent">
                          <span className="flex items-center gap-1.5">
                            <Calendar size={13} /> {year} ОН
                          </span>
                          <span className="text-[10px] text-dim font-normal">
                            {list.length} үйл явдал
                          </span>
                        </div>

                        <div className="space-y-3 pl-2.5 border-l-2 border-line/60 ml-2">
                          {list.map((fact) => {
                            const isPassed = !activeCutoffDate || fact.fact_date <= activeCutoffDate
                            const isSelectedFact =
                              selectedNode?.entity_type === 'fact' &&
                              selectedNode?.fact_id === fact.id
                            const matchingLink = data?.links?.find(
                              (l) => l.entity_id === fact.entity_id
                            )
                            const role = matchingLink?.role

                            return (
                              <div
                                key={fact.id}
                                onClick={() => {
                                  const n = simNodes.current.find((sn) => sn.fact_id === fact.id)
                                  if (n) setSelectedNode(n)
                                }}
                                className={`relative p-3.5 rounded-lg border transition-all cursor-pointer group ${
                                  isSelectedFact
                                    ? 'bg-accent/15 border-accent shadow-[0_0_16px_rgb(56_224_255/0.2)] ring-1 ring-accent'
                                    : isPassed
                                    ? 'bg-surface-2/90 border-line hover:border-accent-line hover:bg-surface-2'
                                    : 'bg-surface-1/40 border-line/40 opacity-40'
                                }`}
                              >
                                <div
                                  className={`absolute -left-[15px] top-4 w-2.5 h-2.5 rounded-full border-2 transition ${
                                    isSelectedFact
                                      ? 'bg-accent border-accent shadow-[0_0_8px_#38e0ff]'
                                      : 'bg-surface-1 border-accent/60 group-hover:border-accent'
                                  }`}
                                />

                                <div className="flex items-center justify-between flex-wrap gap-1.5 mb-2 text-[11px] font-mono">
                                  <div className="flex items-center gap-1.5 flex-wrap">
                                    <span className="flex items-center gap-1 text-accent font-bold bg-accent/10 px-1.5 py-0.5 rounded border border-accent/20">
                                      <Calendar size={11} /> {fact.fact_date || 'Огноогүй'}
                                    </span>

                                    {fact.entity_name && (
                                      <span
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          const entNode = simNodes.current.find(
                                            (sn) => sn.id === fact.entity_id
                                          )
                                          if (entNode) setSelectedNode(entNode)
                                        }}
                                        className={`flex items-center gap-1 px-1.5 py-0.5 rounded border transition hover:underline ${
                                          role === 'SUSPECT'
                                            ? 'bg-danger/10 text-danger border-danger/30'
                                            : role === 'BENEFICIARY'
                                            ? 'bg-ok/10 text-ok border-ok/30'
                                            : role === 'DECISION_MAKER'
                                            ? 'bg-accent/10 text-accent border-accent/30'
                                            : 'bg-surface-3 text-text border-line'
                                        }`}
                                      >
                                        {fact.entity_type === 'company' ? (
                                          <Building size={11} />
                                        ) : (
                                          <User size={11} />
                                        )}
                                        <b>{fact.entity_name}</b>
                                        {role && <span className="text-[9px] opacity-75">({role})</span>}
                                      </span>
                                    )}
                                  </div>

                                  {fact.role_context && (
                                    <span className="text-[10px] font-mono text-dim bg-surface-3 px-1.5 py-0.5 rounded border border-line">
                                      {fact.role_context}
                                    </span>
                                  )}
                                </div>

                                <p className="text-[13px] text-text leading-[1.65] font-sans">
                                  {formatFactText(fact.fact_text)}
                                </p>

                                {fact.source_quote && (
                                  <blockquote className="mt-2.5 p-2 bg-surface-1/80 border-l-2 border-accent rounded-r text-[12px] text-dim italic leading-relaxed">
                                    <div className="flex items-start gap-1.5">
                                      <Quote size={12} className="text-accent shrink-0 mt-0.5 opacity-80" />
                                      <span>"{fact.source_quote}"</span>
                                    </div>
                                  </blockquote>
                                )}

                                {(fact.source_title || fact.source_url) && (
                                  <div className="mt-2.5 pt-2 border-t border-line/50 flex items-center justify-between text-[10px] font-mono text-dim flex-wrap gap-1">
                                    <div className="flex items-center gap-1.5 truncate max-w-[280px]">
                                      {fact.source_id ? (
                                        <Link
                                          to={`/sources/${fact.source_id}`}
                                          onClick={(e) => e.stopPropagation()}
                                          className="text-accent hover:underline truncate"
                                          title={fact.source_title || 'Эх сурвалж үзэх'}
                                        >
                                          ⎘ {fact.source_title || 'Эх сурвалж'}
                                        </Link>
                                      ) : (
                                        <span className="truncate">{fact.source_title}</span>
                                      )}
                                      {fact.source_author && (
                                        <span className="text-faint">• {fact.source_author}</span>
                                      )}
                                    </div>

                                    <div className="flex items-center gap-1.5 ml-auto">
                                      {fact.source_url && (
                                        <a
                                          href={fact.source_url}
                                          target="_blank"
                                          rel="noreferrer"
                                          onClick={(e) => e.stopPropagation()}
                                          className="text-dim hover:text-accent flex items-center gap-0.5 text-[9px] bg-surface-1 px-1.5 py-0.5 rounded border border-line"
                                          title="Анхдагч холбоос нээх"
                                        >
                                          Гадаад ↗
                                        </a>
                                      )}
                                      {fact.sha256 && (
                                        <span className="text-ok flex items-center gap-0.5 text-[9px]">
                                          <ShieldCheck size={10} /> SHA-256
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="space-y-3 pl-2.5 border-l-2 border-line/60 ml-2">
                      {filteredTimelineFacts.map((fact) => {
                        const isPassed = !activeCutoffDate || fact.fact_date <= activeCutoffDate
                        const isSelectedFact =
                          selectedNode?.entity_type === 'fact' &&
                          selectedNode?.fact_id === fact.id
                        const matchingLink = data?.links?.find(
                          (l) => l.entity_id === fact.entity_id
                        )
                        const role = matchingLink?.role

                        return (
                          <div
                            key={fact.id}
                            onClick={() => {
                              const n = simNodes.current.find((sn) => sn.fact_id === fact.id)
                              if (n) setSelectedNode(n)
                            }}
                            className={`relative p-3.5 rounded-lg border transition-all cursor-pointer group ${
                              isSelectedFact
                                ? 'bg-accent/15 border-accent shadow-[0_0_16px_rgb(56_224_255/0.2)] ring-1 ring-accent'
                                : isPassed
                                ? 'bg-surface-2/90 border-line hover:border-accent-line hover:bg-surface-2'
                                : 'bg-surface-1/40 border-line/40 opacity-40'
                            }`}
                          >
                            <div
                              className={`absolute -left-[15px] top-4 w-2.5 h-2.5 rounded-full border-2 transition ${
                                isSelectedFact
                                  ? 'bg-accent border-accent shadow-[0_0_8px_#38e0ff]'
                                  : 'bg-surface-1 border-accent/60 group-hover:border-accent'
                              }`}
                            />

                            <div className="flex items-center justify-between flex-wrap gap-1.5 mb-2 text-[11px] font-mono">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="flex items-center gap-1 text-accent font-bold bg-accent/10 px-1.5 py-0.5 rounded border border-accent/20">
                                  <Calendar size={11} /> {fact.fact_date || 'Огноогүй'}
                                </span>

                                {fact.entity_name && (
                                  <span
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      const entNode = simNodes.current.find(
                                        (sn) => sn.id === fact.entity_id
                                      )
                                      if (entNode) setSelectedNode(entNode)
                                    }}
                                    className={`flex items-center gap-1 px-1.5 py-0.5 rounded border transition hover:underline ${
                                      role === 'SUSPECT'
                                        ? 'bg-danger/10 text-danger border-danger/30'
                                        : role === 'BENEFICIARY'
                                        ? 'bg-ok/10 text-ok border-ok/30'
                                        : role === 'DECISION_MAKER'
                                        ? 'bg-accent/10 text-accent border-accent/30'
                                        : 'bg-surface-3 text-text border-line'
                                    }`}
                                  >
                                    {fact.entity_type === 'company' ? (
                                      <Building size={11} />
                                    ) : (
                                      <User size={11} />
                                    )}
                                    <b>{fact.entity_name}</b>
                                    {role && <span className="text-[9px] opacity-75">({role})</span>}
                                  </span>
                                )}
                              </div>

                              {fact.role_context && (
                                <span className="text-[10px] font-mono text-dim bg-surface-3 px-1.5 py-0.5 rounded border border-line">
                                  {fact.role_context}
                                </span>
                              )}
                            </div>

                            <p className="text-[13px] text-text leading-[1.65] font-sans">
                              {formatFactText(fact.fact_text)}
                            </p>

                            {fact.source_quote && (
                              <blockquote className="mt-2.5 p-2 bg-surface-1/80 border-l-2 border-accent rounded-r text-[12px] text-dim italic leading-relaxed">
                                <div className="flex items-start gap-1.5">
                                  <Quote size={12} className="text-accent shrink-0 mt-0.5 opacity-80" />
                                  <span>"{fact.source_quote}"</span>
                                </div>
                              </blockquote>
                            )}

                            {(fact.source_title || fact.source_url) && (
                              <div className="mt-2.5 pt-2 border-t border-line/50 flex items-center justify-between text-[10px] font-mono text-dim flex-wrap gap-1">
                                <div className="flex items-center gap-1.5 truncate max-w-[280px]">
                                  {fact.source_id ? (
                                    <Link
                                      to={`/sources/${fact.source_id}`}
                                      onClick={(e) => e.stopPropagation()}
                                      className="text-accent hover:underline truncate"
                                      title={fact.source_title || 'Эх сурвалж үзэх'}
                                    >
                                      ⎘ {fact.source_title || 'Эх сурвалж'}
                                    </Link>
                                  ) : (
                                    <span className="truncate">{fact.source_title}</span>
                                  )}
                                  {fact.source_author && (
                                    <span className="text-faint">• {fact.source_author}</span>
                                  )}
                                </div>

                                <div className="flex items-center gap-1.5 ml-auto">
                                  {fact.source_url && (
                                    <a
                                      href={fact.source_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      onClick={(e) => e.stopPropagation()}
                                      className="text-dim hover:text-accent flex items-center gap-0.5 text-[9px] bg-surface-1 px-1.5 py-0.5 rounded border border-line"
                                      title="Анхдагч холбоос нээх"
                                    >
                                      Гадаад ↗
                                    </a>
                                  )}
                                  {fact.sha256 && (
                                    <span className="text-ok flex items-center gap-0.5 text-[9px]">
                                      <ShieldCheck size={10} /> SHA-256
                                    </span>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
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
                                    <div className="pt-1.5 border-t border-line/50 flex flex-col gap-1.5 text-[10px] font-mono">
                                      <div className="flex items-center justify-between gap-2">
                                        {fact.source_id ? (
                                          <Link
                                            to={`/sources/${fact.source_id}`}
                                            className="text-accent hover:underline flex items-center gap-1 truncate font-semibold"
                                            title="Платформ дээрх эх сурвалж, нотлох эх текст рүү очих"
                                          >
                                            <span>⎘ {fact.source_title || 'Эх сурвалж'}</span>
                                          </Link>
                                        ) : fact.source_title ? (
                                          <span className="text-dim truncate">{fact.source_title}</span>
                                        ) : null}

                                        {fact.source_url && (
                                          <a
                                            href={fact.source_url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="text-dim hover:text-accent flex items-center gap-0.5 shrink-0 text-[9px] bg-surface-1 px-1.5 py-0.5 rounded border border-line"
                                            title="Анхдагч гадаад эх холбоос нээх"
                                          >
                                            Гадаад ↗
                                          </a>
                                        )}
                                      </div>

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

                              {(fact.source_id || fact.source_url) && (
                                <div className="p-2 bg-surface-2 border border-line rounded flex items-center justify-between gap-2">
                                  <div className="min-w-0 flex-1">
                                    {fact.source_id ? (
                                      <Link
                                        to={`/sources/${fact.source_id}`}
                                        className="text-xs font-mono font-bold text-accent hover:underline flex items-center gap-1 truncate"
                                        title="Манай платформ дээрх эх сурвалжийн дэлгэрэнгүй баталгаажсан хуудас руу очих"
                                      >
                                        <span>⎘ {fact.source_title || 'Эх сурвалж'}</span>
                                      </Link>
                                    ) : (
                                      <div className="text-[11px] font-mono text-dim truncate">
                                        {fact.source_title || 'Эх сурвалж'}
                                      </div>
                                    )}
                                  </div>

                                  {fact.source_url && (
                                    <a
                                      href={fact.source_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-xs text-dim hover:text-accent hover:underline flex items-center gap-1 shrink-0 font-mono bg-surface-1 px-2 py-0.5 rounded border border-line"
                                      title="Анхдагч гадаад эх линк нээх"
                                    >
                                      Гадаад ↗
                                    </a>
                                  )}
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
                        <div className="pt-1 border-t border-line/40 flex items-center justify-between gap-2 text-[10px] font-mono">
                          {item.source_id ? (
                            <Link
                              to={`/sources/${item.source_id}`}
                              className="text-accent hover:underline truncate max-w-[170px]"
                              title="Платформ дээрх эх сурвалж руу очих"
                            >
                              ⎘ {item.source_title || 'Эх сурвалж'}
                            </Link>
                          ) : item.source_title ? (
                            <span className="text-dim truncate max-w-[170px]">{item.source_title}</span>
                          ) : null}

                          {item.source_url && (
                            <a
                              href={item.source_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-dim hover:text-accent text-[9px] bg-surface-1 px-1.5 py-0.5 rounded border border-line shrink-0"
                            >
                              Гадаад ↗
                            </a>
                          )}
                        </div>

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
