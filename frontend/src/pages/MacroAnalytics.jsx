import React, { useState, useEffect, useMemo, useRef } from 'react'
import {
  TrendingUp,
  BarChart3,
  Layers,
  Calendar,
  Download,
  Search,
  ExternalLink,
  Info,
  Check,
  ShieldCheck,
  Zap,
  ArrowUpRight,
  Filter,
  RefreshCw,
  Activity,
  SlidersHorizontal,
  ChevronRight,
  Flame,
  Scale,
  Coins,
  Building2,
  Eye,
  EyeOff,
  Award,
  Sparkles,
  History,
} from 'lucide-react'

// Бүх 10 макро үзүүлэлтийн тохиргоо ба дизайн систем
const INDICATOR_CONFIGS = {
  budget_expenditure: {
    code: 'budget_expenditure',
    name: 'Улсын төсвийн зарлага',
    shortName: 'Төсөв',
    unit: 'их наяд ₮',
    color: '#F59E0B', // Amber
    axis: 'left',
    category: 'fiscal',
    icon: '🏛️',
    description: 'Улсын нэгдсэн төсвийн нийт зарлагын хэмжээ (Сангийн яам, ҮСХ)',
  },
  usd_rate: {
    code: 'usd_rate',
    name: 'Ам.долларын албан ханш (USD)',
    shortName: 'USD ($)',
    unit: '₮',
    color: '#10B981', // Emerald
    axis: 'right',
    category: 'fx',
    icon: '💵',
    description: 'Монголбанкны оны эцсийн албан хаалтын ханш',
  },
  cny_rate: {
    code: 'cny_rate',
    name: 'БНХАУ-ын юанийн ханш (CNY)',
    shortName: 'CNY (¥)',
    unit: '₮',
    color: '#EF4444', // Red
    axis: 'right',
    category: 'fx',
    icon: '💴',
    description: 'Монголбанкны оны эцсийн албан хаалтын ханш',
  },
  eur_rate: {
    code: 'eur_rate',
    name: 'Европын еврогийн ханш (EUR)',
    shortName: 'EUR (€)',
    unit: '₮',
    color: '#38BDF8', // Sky blue
    axis: 'right',
    category: 'fx',
    icon: '💶',
    description: 'Монголбанкны оны эцсийн еврогийн ханш',
  },
  population: {
    code: 'population',
    name: 'Монгол Улсын хүн ам',
    shortName: 'Хүн ам',
    unit: 'сая хүн',
    color: '#A855F7', // Purple
    axis: 'pop',
    category: 'demography',
    icon: '👥',
    description: 'ҮСХ-ны тооллого ба жилийн эцсийн суурин хүн ам',
  },
  cpi_inflation: {
    code: 'cpi_inflation',
    name: 'Инфляцийн түвшин (ХҮИ %)',
    shortName: 'Инфляц',
    unit: '%',
    color: '#EC4899', // Pink
    axis: 'right',
    category: 'macro',
    icon: '📊',
    description: 'ҮСХ: Хэрэглээний үнийн улсын индекс (жилийн өөрчлөлт)',
  },
  meat_price_kg: {
    code: 'meat_price_kg',
    name: 'Махны дундаж үнэ (₮/кг)',
    shortName: 'Мах (₮/кг)',
    unit: '₮/кг',
    color: '#F43F5E', // Rose
    axis: 'right',
    category: 'consumption',
    icon: '🥩',
    description: 'ҮСХ: Хонь, үхрийн махны 1 кг дундаж үнэ',
  },
  housing_price_sqm: {
    code: 'housing_price_sqm',
    name: 'Орон сууцны үнэ (₮/м²)',
    shortName: 'Орон сууц (₮/м²)',
    unit: '₮/м²',
    color: '#06B6D4', // Cyan
    axis: 'right',
    category: 'asset',
    icon: '🏢',
    description: 'ҮСХ, Монголбанк, Тэнхлэг зууч: 1м² дундаж үнэ',
  },
  gold_price_mnt_gram: {
    code: 'gold_price_mnt_gram',
    name: 'Алтны ханш (₮/грамм)',
    shortName: 'Алт (₮/г)',
    unit: '₮/г',
    color: '#EAB308', // Gold yellow
    axis: 'right',
    category: 'commodity',
    icon: '🪙',
    description: 'Монголбанкны алт худалдан авах оны эцсийн ханш',
  },
  bitcoin_usd: {
    code: 'bitcoin_usd',
    name: 'Биткойны ханш (BTC/USD)',
    shortName: 'Биткойн ($)',
    unit: '$',
    color: '#FB923C', // Orange
    axis: 'right',
    category: 'crypto',
    icon: '₿',
    description: 'CoinMarketCap & Glassnode: Оны эцсийн хаалтын ханш',
  },
}

const CATEGORIES = [
  { id: 'all', label: 'Бүх үзүүлэлт', icon: '🌐' },
  { id: 'fiscal', label: 'Төсөв', icon: '🏛️' },
  { id: 'fx', label: 'Валют', icon: '💵' },
  { id: 'commodity', label: 'Алт & Крипто', icon: '🪙' },
  { id: 'consumption', label: 'Мах & Хүнс', icon: '🥩' },
  { id: 'asset', label: 'Орон сууц', icon: '🏢' },
  { id: 'macro', label: 'Инфляц & Хүн ам', icon: '📊' },
]

const PRESET_BASKETS = [
  {
    id: 'core_macro',
    name: 'Үндсэн макро',
    icon: '⚡',
    desc: 'Төсөв, Доллар, Хүн ам, Инфляц',
    codes: ['budget_expenditure', 'usd_rate', 'population', 'cpi_inflation'],
  },
  {
    id: 'purchasing_power',
    name: 'Худалдан авах чадвар',
    icon: '🛒',
    desc: 'Мах, Орон сууц, Инфляц, USD',
    codes: ['meat_price_kg', 'housing_price_sqm', 'cpi_inflation', 'usd_rate'],
  },
  {
    id: 'store_of_value',
    name: 'Инфляцийн эсрэг хөрөнгө',
    icon: '🛡️',
    desc: 'Алт, Биткойн, Орон сууц, USD',
    codes: ['gold_price_mnt_gram', 'bitcoin_usd', 'housing_price_sqm', 'usd_rate'],
  },
  {
    id: 'price_expansion',
    name: 'Үнийн тэлэлт',
    icon: '📈',
    desc: 'Төсөв, Махны үнэ, Орон сууц, Инфляц',
    codes: ['budget_expenditure', 'meat_price_kg', 'housing_price_sqm', 'cpi_inflation'],
  },
  {
    id: 'all_indicators',
    name: 'Бүх 10 үзүүлэлт',
    icon: '🌐',
    desc: 'Бүх түүхэн цувааг зэрэгцүүлэх',
    codes: Object.keys(INDICATOR_CONFIGS),
  },
]

const ALL_YEARS = Array.from({ length: 2026 - 1990 + 1 }, (_, i) => 1990 + i)

export default function MacroAnalytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Идэвхтэй үзүүлэлтүүд (Чартад сонгогдсон)
  const [activeCodes, setActiveCodes] = useState([
    'budget_expenditure',
    'usd_rate',
    'meat_price_kg',
    'gold_price_mnt_gram',
    'housing_price_sqm',
  ])

  // Ангиллын шүүлтүүр (Indicator Filter)
  const [selectedCategory, setSelectedCategory] = useState('all')

  // Хугацааны тохиргоо (1990–2026)
  const [startYear, setStartYear] = useState(1990)
  const [endYear, setEndYear] = useState(2026)
  const [rangePreset, setRangePreset] = useState('all')

  // Чартын хэлбэрүүд:
  // 'combo': Багана + Зураас
  // 'area': Талбайт зураас
  // 'panels': Салгасан панелууд (Bloomberg Multiples)
  // 'yoy': Жилийн өсөлтийн хурд (% YoY)
  const [chartType, setChartType] = useState('combo')
  const [viewMode, setViewMode] = useState('actual') // 'actual' | 'indexed'

  const [hoveredYear, setHoveredYear] = useState(2024)
  const [searchTable, setSearchTable] = useState('')
  const [selectedSource, setSelectedSource] = useState(null)

  // Том хүснэгтийн багана харагдах байдлын тохиргоо (Column Visibility)
  const [showColumnSelector, setShowColumnSelector] = useState(false)
  const [visibleColumns, setVisibleColumns] = useState(() => {
    try {
      const saved = localStorage.getItem('macro_visible_columns')
      if (saved) return JSON.parse(saved)
    } catch {
      // fallback
    }
    return [
      'budget_expenditure',
      'usd_rate',
      'meat_price_kg',
      'housing_price_sqm',
      'gold_price_mnt_gram',
      'cpi_inflation',
    ]
  })

  // Шинжилгээний лаборатори (Macro Analytics Lab) төлөвүүд
  const [activeLabTab, setActiveLabTab] = useState('correlation') // 'correlation' | 'ppp' | 'cagr' | 'cabinet'
  const [analyticsData, setAnalyticsData] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [selectedPair, setSelectedPair] = useState(null)
  const [pppBaseYear, setPppBaseYear] = useState(2000)
  const [pppAmount, setPppAmount] = useState(1000000)

  const svgRef = useRef(null)

  // Баганын сонголтыг localStorage-д хадгалах
  const updateVisibleColumns = (newCols) => {
    setVisibleColumns(newCols)
    try {
      localStorage.setItem('macro_visible_columns', JSON.stringify(newCols))
    } catch (err) {
      console.warn('Failed to save visible columns:', err)
    }
  }

  // Хугацааны шуурхай пресет
  const applyPreset = (preset) => {
    setRangePreset(preset)
    switch (preset) {
      case 'post2000':
        setStartYear(2000)
        setEndYear(2026)
        break
      case 'last10':
        setStartYear(2016)
        setEndYear(2026)
        break
      case 'transition':
        setStartYear(1990)
        setEndYear(2000)
        break
      case 'all':
      default:
        setStartYear(1990)
        setEndYear(2026)
        break
    }
  }

  // Сэдэвчилсэн шуурхай багцыг сонгох
  const applyBasket = (basket) => {
    setActiveCodes(basket.codes)
  }

  // API 1: Түүхэн цуваа татах
  const fetchSeries = async () => {
    setLoading(true)
    setError(null)
    try {
      const codeList = Object.keys(INDICATOR_CONFIGS).join(',')
      const res = await fetch(
        `/api/analytics/macro-series?indicators=${codeList}&start_year=${startYear}&end_year=${endYear}&normalize=${viewMode === 'indexed'}`
      )
      if (!res.ok) throw new Error(`Алдаа гарлаа: ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (err) {
      console.error(err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // API 2: Шинжилгээний лабораторийн өгөгдөл татах (Корреляци, CAGR, PPP, Cabinet)
  const fetchAnalytics = async () => {
    setAnalyticsLoading(true)
    try {
      const res = await fetch(
        `/api/analytics/macro-analytics?start_year=${startYear}&end_year=${endYear}&base_year=${pppBaseYear}&amount_mnt=${pppAmount}`
      )
      if (res.ok) {
        const json = await res.json()
        setAnalyticsData(json)
        if (json.correlation?.pairs?.length > 0 && !selectedPair) {
          setSelectedPair(json.correlation.pairs[0])
        }
      }
    } catch (err) {
      console.error('Failed to fetch macro analytics lab data:', err)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  useEffect(() => {
    fetchSeries()
  }, [startYear, endYear, viewMode])

  useEffect(() => {
    fetchAnalytics()
  }, [startYear, endYear, pppBaseYear, pppAmount])

  // Үзүүлэлтийн асаах/унтраах toggle
  const toggleCode = (code) => {
    setActiveCodes((prev) => {
      if (prev.includes(code)) {
        if (prev.length === 1) return prev // Хамгийн багадаа 1 үзүүлэлт үлдээх
        return prev.filter((c) => c !== code)
      }
      return [...prev, code]
    })
  }

  // Ангиллаар шүүгдсэн үзүүлэлтүүд
  const filteredConfigs = useMemo(() => {
    if (selectedCategory === 'all') return Object.entries(INDICATOR_CONFIGS)
    return Object.entries(INDICATOR_CONFIGS).filter(
      ([_, conf]) =>
        conf.category === selectedCategory ||
        (selectedCategory === 'macro' && conf.category === 'demography')
    )
  }, [selectedCategory])

  // ── Вектор графикийн динамик координат, масштаб тооцоолох ────────────────────
  const chartLayout = useMemo(() => {
    if (!data?.timeline || data.timeline.length === 0) return null

    const width = 1060
    const height = chartType === 'panels' ? 520 : 440
    const padding = { top: 42, right: 65, bottom: 44, left: 70 }
    const plotWidth = width - padding.left - padding.right
    const plotHeight = height - padding.top - padding.bottom

    const timeline = data.timeline
    const minYr = timeline[0]?.year || startYear
    const maxYr = timeline[timeline.length - 1]?.year || endYear
    const yearSpan = Math.max(1, maxYr - minYr)

    const getX = (year) => {
      const ratio = (year - minYr) / yearSpan
      return padding.left + ratio * plotWidth
    }

    // 1. САЛГАСАН ПАНЕЛУУДЫН ТОХИРГОО (Multiples)
    if (chartType === 'panels') {
      // Идэвхтэй цуваануудын бүлгүүд
      const panelConfigs = [
        {
          key: 'fiscal',
          name: 'Улсын төсвийн зарлага',
          unit: 'их наяд ₮',
          color: '#F59E0B',
          codes: ['budget_expenditure'],
        },
        {
          key: 'fx',
          name: 'Гадаад валютын албан ханш',
          unit: '₮',
          color: '#10B981',
          codes: ['usd_rate', 'cny_rate', 'eur_rate'],
        },
        {
          key: 'assets',
          name: 'Хөрөнгө, Хэрэглээ & Алт',
          unit: '₮',
          color: '#EAB308',
          codes: ['meat_price_kg', 'housing_price_sqm', 'gold_price_mnt_gram', 'bitcoin_usd'],
        },
        {
          key: 'macro',
          name: 'Инфляц ба Хүн ам',
          unit: '% / сая хүн',
          color: '#EC4899',
          codes: ['cpi_inflation', 'population'],
        },
      ]

      const activePanels = panelConfigs.filter((p) =>
        p.codes.some((c) => activeCodes.includes(c))
      )
      const pCount = Math.max(1, activePanels.length)
      const pGap = 16
      const pHeight = (plotHeight - (pCount - 1) * pGap) / pCount

      const panels = {}
      activePanels.forEach((p, idx) => {
        const top = padding.top + idx * (pHeight + pGap)
        // Тухайн самбар дахь үзүүлэлтүүдийн min/max
        let minV = Infinity
        let maxV = -Infinity
        timeline.forEach((pt) => {
          p.codes.forEach((c) => {
            if (activeCodes.includes(c)) {
              const val = pt.values?.[c]
              if (val !== undefined && val !== null) {
                if (val < minV) minV = val
                if (val > maxV) maxV = val
              }
            }
          })
        })

        if (minV === Infinity) {
          minV = 0
          maxV = 100
        }
        if (p.key === 'macro' && activeCodes.includes('cpi_inflation')) {
          minV = Math.min(0, minV)
        } else if (p.key !== 'macro') {
          minV = Math.max(0, minV * 0.9)
        }
        maxV = maxV * 1.08

        const getPanelY = (val) => {
          if (val === undefined || val === null) return null
          const r = (val - minV) / (maxV - minV || 1)
          return top + pHeight - r * pHeight
        }

        panels[p.key] = {
          top,
          height: pHeight,
          min: minV,
          max: maxV,
          name: p.name,
          unit: p.unit,
          color: p.color,
          codes: p.codes,
          getY: getPanelY,
        }
      })

      return {
        width,
        height,
        padding,
        plotWidth,
        plotHeight,
        minYr,
        maxYr,
        getX,
        isPanels: true,
        panels,
      }
    }

    // 2. ЖИЛИЙН ӨСӨЛТИЙН ХУВЬ (YoY Growth %)
    if (chartType === 'yoy') {
      let minYoY = -15
      let maxYoY = 50
      timeline.forEach((pt) => {
        activeCodes.forEach((c) => {
          const yoy = pt.yoy_growth?.[c]
          if (yoy !== undefined && yoy !== null) {
            if (yoy < minYoY) minYoY = yoy
            if (yoy > maxYoY) maxYoY = yoy
          }
        })
      })
      minYoY = Math.floor(Math.min(-10, minYoY) / 10) * 10
      maxYoY = Math.ceil(Math.max(20, maxYoY) / 10) * 10
      const span = maxYoY - minYoY || 1

      const getYYoY = (val) => {
        if (val === undefined || val === null) return null
        return padding.top + plotHeight - ((val - minYoY) / span) * plotHeight
      }

      return {
        width,
        height,
        padding,
        plotWidth,
        plotHeight,
        minYr,
        maxYr,
        getX,
        isYoY: true,
        minY: minYoY,
        maxY: maxYoY,
        zeroY: getYYoY(0),
        getY: getYYoY,
      }
    }

    // 3. СУУРЬ ИНДЕКС (100% Normalized Growth)
    if (viewMode === 'indexed') {
      let maxIdx = 100
      timeline.forEach((pt) => {
        activeCodes.forEach((c) => {
          const val = pt.indexed_values?.[c]
          if (val && val > maxIdx) maxIdx = val
        })
      })
      maxIdx *= 1.1

      const getYIndexed = (val) => {
        if (val === undefined || val === null) return null
        return padding.top + plotHeight - (val / maxIdx) * plotHeight
      }

      return {
        width,
        height,
        padding,
        plotWidth,
        plotHeight,
        minYr,
        maxYr,
        getX,
        mode: 'indexed',
        maxIdx,
        getYLeft: getYIndexed,
        getYRight: getYIndexed,
      }
    }

    // 4. БОДИТ УТГЫН ГОРИМ (Smart Multi-Scale Normalization)
    // Үзүүлэлт бүр өөрийн масштабаар тод харагдах ба зүүн талд Төсөв, баруун талд Валютын хэмжүүрүүд орно
    let maxBudget = 1.0
    timeline.forEach((pt) => {
      const b = pt.values?.budget_expenditure
      if (b && b > maxBudget) maxBudget = b
    })
    maxBudget *= 1.08

    const getYBudget = (val) => {
      if (val === undefined || val === null) return null
      return padding.top + plotHeight - (val / maxBudget) * plotHeight
    }

    // Бусад үзүүлэлтүүдийн тусгай тохируулга (Auto-Scale Map)
    const codeScales = {}
    Object.keys(INDICATOR_CONFIGS).forEach((code) => {
      const vals = timeline
        .map((t) => t.values?.[code])
        .filter((v) => v !== undefined && v !== null)
      if (vals.length > 0) {
        let mn = Math.min(...vals)
        let mx = Math.max(...vals)
        if (code === 'budget_expenditure') {
          mn = 0
          mx = mx * 1.08
        } else if (code === 'cpi_inflation') {
          mn = Math.min(-5, mn - 2)
          mx = mx * 1.08
        } else if (code === 'population') {
          mn = Math.max(1.8, mn - 0.2)
          mx = mx + 0.2
        } else {
          const sp = mx - mn || 1
          mn = Math.max(0, mn - sp * 0.05)
          mx = mx + sp * 0.08
        }
        codeScales[code] = { min: mn, max: mx }
      }
    })

    const getYAuto = (code, val) => {
      if (val === undefined || val === null) return null
      if (code === 'budget_expenditure') return getYBudget(val)
      const scale = codeScales[code]
      if (!scale) return null
      const ratio = Math.max(0, Math.min(1, (val - scale.min) / (scale.max - scale.min || 1)))
      // 10% дээд ба доод зайтай
      return padding.top + plotHeight - ratio * (plotHeight * 0.82) - plotHeight * 0.06
    }

    return {
      width,
      height,
      padding,
      plotWidth,
      plotHeight,
      minYr,
      maxYr,
      getX,
      mode: 'actual',
      maxBudget,
      codeScales,
      getYBudget,
      getYAuto,
    }
  }, [data, activeCodes, viewMode, chartType, startYear, endYear])

  // Цэгүүдийн SVG замыг үүсгэх
  const generateSeriesPaths = (code) => {
    if (!chartLayout || !data?.timeline)
      return { linePath: '', areaPath: '', points: [] }

    const { getX, padding, plotHeight } = chartLayout
    const conf = INDICATOR_CONFIGS[code]

    let getYFunc = null
    if (chartLayout.isPanels) {
      // Самбарын түлхүүр олох
      const pKey = Object.keys(chartLayout.panels).find((k) =>
        chartLayout.panels[k].codes.includes(code)
      )
      if (pKey && chartLayout.panels[pKey]) {
        getYFunc = chartLayout.panels[pKey].getY
      }
    } else if (chartLayout.isYoY) {
      getYFunc = chartLayout.getY
    } else if (viewMode === 'indexed') {
      getYFunc = chartLayout.getYLeft
    } else {
      getYFunc = (val) => chartLayout.getYAuto(code, val)
    }

    if (!getYFunc) return { linePath: '', areaPath: '', points: [] }

    const points = []
    data.timeline.forEach((pt) => {
      let val = null
      if (chartLayout.isYoY) {
        val = pt.yoy_growth?.[code]
      } else if (viewMode === 'indexed') {
        val = pt.indexed_values?.[code]
      } else {
        val = pt.values?.[code]
      }

      if (val !== undefined && val !== null) {
        const x = getX(pt.year)
        const y = getYFunc(val)
        if (y !== null && !isNaN(y)) {
          points.push({ x, y, year: pt.year, val, rawPt: pt })
        }
      }
    })

    if (points.length === 0) return { linePath: '', areaPath: '', points: [] }

    const linePath = points.reduce((acc, p, i) => {
      return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`
    }, '')

    // Area fill-ийн ёроол
    let bottomY = padding.top + plotHeight
    if (chartLayout.isPanels) {
      const pKey = Object.keys(chartLayout.panels).find((k) =>
        chartLayout.panels[k].codes.includes(code)
      )
      if (pKey && chartLayout.panels[pKey]) {
        bottomY = chartLayout.panels[pKey].top + chartLayout.panels[pKey].height
      }
    } else if (chartLayout.isYoY) {
      bottomY = chartLayout.zeroY || bottomY
    }

    const areaPath = `${linePath} L ${points[points.length - 1].x} ${bottomY} L ${points[0].x} ${bottomY} Z`

    return { linePath, areaPath, points }
  }

  // Hover дээрх жилийн дата
  const hoveredPoint = useMemo(() => {
    if (!hoveredYear || !data?.timeline) return null
    return data.timeline.find((t) => t.year === hoveredYear) || null
  }, [hoveredYear, data])

  // CSV татаж авах
  const exportCSV = () => {
    if (!data?.timeline) return
    const cols = Object.keys(INDICATOR_CONFIGS)
    const headers = ['Year', 'Cabinet', ...cols.map((c) => INDICATOR_CONFIGS[c].name), 'Milestone']
    const rows = data.timeline.map((t) => [
      t.year,
      `"${t.cabinet || ''}"`,
      ...cols.map((c) => t.values?.[c] ?? ''),
      `"${t.milestone || ''}"`,
    ])

    const csvContent =
      'data:text/csv;charset=utf-8,\uFEFF' +
      [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.href = encodedUri
    link.setAttribute('download', `mongolia_macro_expanded_${startYear}_${endYear}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Хүснэгтийн шүүлтүүр
  const filteredTimeline = useMemo(() => {
    if (!data?.timeline) return []
    if (!searchTable.trim()) return [...data.timeline].reverse()
    const q = searchTable.toLowerCase()
    return [...data.timeline]
      .filter(
        (t) =>
          String(t.year).includes(q) ||
          (t.cabinet && t.cabinet.toLowerCase().includes(q)) ||
          (t.milestone && t.milestone.toLowerCase().includes(q))
      )
      .reverse()
  }, [data, searchTable])

  return (
    <div className="space-y-6 animate-fadeIn max-w-[1440px] mx-auto pb-20">
      {/* ── Титэм гарчиг ────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-line pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-accent uppercase tracking-widest mb-1.5">
            <TrendingUp size={15} />
            <span>Time-Series Macro Analytics & Quantitative Ledger</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-display font-bold text-text tracking-tight flex items-center gap-3">
            <span>Монгол Улсын Макро Динамик</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-normal bg-accent-dim text-accent border border-accent-line">
              {startYear}–{endYear} он
            </span>
          </h1>
          <p className="text-dim text-sm mt-1 max-w-2xl">
            Төсөв, валютын ханш, орон сууц, махны үнэ, алт, биткойн болон инфляцийн 35 жилийн нэгдсэн архив, аналитик шинжилгээ.
          </p>
        </div>

        {/* Экспорт & Сэргээх товчнууд */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => {
              fetchSeries()
              fetchAnalytics()
            }}
            disabled={loading}
            className="px-3 py-2 rounded-lg text-xs font-mono bg-surface-2 hover:bg-surface-3 text-text border border-line flex items-center gap-1.5 transition-all"
            title="Дахин шинэчлэх"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Шинэчлэх</span>
          </button>
          <button
            onClick={exportCSV}
            className="px-3.5 py-2 rounded-lg text-xs font-mono bg-accent-dim hover:bg-accent-line text-accent border border-accent-line flex items-center gap-1.5 transition-all shadow-[0_0_12px_rgb(56_224_255/0.1)]"
          >
            <Download size={14} />
            <span>CSV Татах</span>
          </button>
        </div>
      </div>

      {/* ── Статистик хураангуй картууд (Top 5 Гол үзүүлэлт) ─────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* 1. Төсвийн зарлага */}
        <div
          onClick={() => toggleCode('budget_expenditure')}
          className={`glass p-3.5 rounded-xl cursor-pointer transition-all border ${
            activeCodes.includes('budget_expenditure')
              ? 'border-amber-500/40 bg-amber-500/5 shadow-[0_0_16px_rgba(245,158,11,0.1)]'
              : 'opacity-50 border-line hover:opacity-80'
          }`}
        >
          <div className="flex items-center justify-between text-[11px] font-mono text-dim mb-1">
            <span className="flex items-center gap-1.5 truncate">
              <span className="w-2 h-2 rounded-full bg-amber-500 inline-block shrink-0" />
              Төсвийн зарлага
            </span>
            <span className="text-[9px] px-1 rounded bg-amber-500/20 text-amber-300 font-mono">
              +7,955x
            </span>
          </div>
          <div className="text-xl font-display font-bold text-text mt-0.5">
            35.80 <span className="text-xs font-sans font-normal text-dim">их наяд ₮</span>
          </div>
          <div className="text-[10px] text-dim mt-2 flex items-center justify-between pt-1.5 border-t border-line/40">
            <span>1990 онд: 4.5 тэрбум</span>
            <span className="text-ok font-mono font-medium">+795k%</span>
          </div>
        </div>

        {/* 2. Ам.долларын ханш */}
        <div
          onClick={() => toggleCode('usd_rate')}
          className={`glass p-3.5 rounded-xl cursor-pointer transition-all border ${
            activeCodes.includes('usd_rate')
              ? 'border-emerald-500/40 bg-emerald-500/5 shadow-[0_0_16px_rgba(16,185,129,0.1)]'
              : 'opacity-50 border-line hover:opacity-80'
          }`}
        >
          <div className="flex items-center justify-between text-[11px] font-mono text-dim mb-1">
            <span className="flex items-center gap-1.5 truncate">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block shrink-0" />
              USD / Төгрөг
            </span>
            <span className="text-[9px] px-1 rounded bg-emerald-500/20 text-emerald-300 font-mono">
              +615x
            </span>
          </div>
          <div className="text-xl font-display font-bold text-text mt-0.5">
            3,465 <span className="text-xs font-sans font-normal text-dim">₮</span>
          </div>
          <div className="text-[10px] text-dim mt-2 flex items-center justify-between pt-1.5 border-t border-line/40">
            <span>1990 онд: 5.63 ₮</span>
            <span className="text-danger font-mono font-medium">+61k%</span>
          </div>
        </div>

        {/* 3. Махны үнэ */}
        <div
          onClick={() => toggleCode('meat_price_kg')}
          className={`glass p-3.5 rounded-xl cursor-pointer transition-all border ${
            activeCodes.includes('meat_price_kg')
              ? 'border-rose-500/40 bg-rose-500/5 shadow-[0_0_16px_rgba(244,63,94,0.1)]'
              : 'opacity-50 border-line hover:opacity-80'
          }`}
        >
          <div className="flex items-center justify-between text-[11px] font-mono text-dim mb-1">
            <span className="flex items-center gap-1.5 truncate">
              <span className="w-2 h-2 rounded-full bg-rose-500 inline-block shrink-0" />
              Мах (₮/кг)
            </span>
            <span className="text-[9px] px-1 rounded bg-rose-500/20 text-rose-300 font-mono">
              +2,475x
            </span>
          </div>
          <div className="text-xl font-display font-bold text-text mt-0.5">
            19,800 <span className="text-xs font-sans font-normal text-dim">₮/кг</span>
          </div>
          <div className="text-[10px] text-dim mt-2 flex items-center justify-between pt-1.5 border-t border-line/40">
            <span>1990 онд: 8 ₮</span>
            <span className="text-danger font-mono font-medium">+247k%</span>
          </div>
        </div>

        {/* 4. Орон сууцны үнэ */}
        <div
          onClick={() => toggleCode('housing_price_sqm')}
          className={`glass p-3.5 rounded-xl cursor-pointer transition-all border ${
            activeCodes.includes('housing_price_sqm')
              ? 'border-cyan-500/40 bg-cyan-500/5 shadow-[0_0_16px_rgba(6,182,212,0.1)]'
              : 'opacity-50 border-line hover:opacity-80'
          }`}
        >
          <div className="flex items-center justify-between text-[11px] font-mono text-dim mb-1">
            <span className="flex items-center gap-1.5 truncate">
              <span className="w-2 h-2 rounded-full bg-cyan-500 inline-block shrink-0" />
              Орон сууц 1м²
            </span>
            <span className="text-[9px] px-1 rounded bg-cyan-500/20 text-cyan-300 font-mono">
              +58.7x
            </span>
          </div>
          <div className="text-xl font-display font-bold text-text mt-0.5">
            4.40 <span className="text-xs font-sans font-normal text-dim">сая ₮</span>
          </div>
          <div className="text-[10px] text-dim mt-2 flex items-center justify-between pt-1.5 border-t border-line/40">
            <span>1995 онд: 75,000 ₮</span>
            <span className="text-danger font-mono font-medium">+5,767%</span>
          </div>
        </div>

        {/* 5. Алтны ханш */}
        <div
          onClick={() => toggleCode('gold_price_mnt_gram')}
          className={`glass p-3.5 rounded-xl cursor-pointer transition-all border ${
            activeCodes.includes('gold_price_mnt_gram')
              ? 'border-yellow-500/40 bg-yellow-500/5 shadow-[0_0_16px_rgba(234,179,8,0.1)]'
              : 'opacity-50 border-line hover:opacity-80'
          }`}
        >
          <div className="flex items-center justify-between text-[11px] font-mono text-dim mb-1">
            <span className="flex items-center gap-1.5 truncate">
              <span className="w-2 h-2 rounded-full bg-yellow-500 inline-block shrink-0" />
              Алт (₮/грамм)
            </span>
            <span className="text-[9px] px-1 rounded bg-yellow-500/20 text-yellow-300 font-mono">
              +175x
            </span>
          </div>
          <div className="text-xl font-display font-bold text-text mt-0.5">
            318,000 <span className="text-xs font-sans font-normal text-dim">₮/г</span>
          </div>
          <div className="text-[10px] text-dim mt-2 flex items-center justify-between pt-1.5 border-t border-line/40">
            <span>1990 онд: 1,820 ₮</span>
            <span className="text-ok font-mono font-medium">+17,370%</span>
          </div>
        </div>
      </div>

      {/* ── Удирдлагын хэсэг: Пресетүүд, Чартын горим, Хугацааны сонгогч ──────── */}
      <div className="glass p-4 rounded-xl border border-line space-y-4">
        {/* Мөр 1: Шуурхай сэдэвчилсэн багцууд (Preset Baskets) */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-line/50 pb-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-mono text-dim mr-1 flex items-center gap-1">
              <Sparkles size={13} className="text-accent" />
              <span>Шуурхай багц:</span>
            </span>
            {PRESET_BASKETS.map((b) => {
              const isSelected =
                b.codes.length === activeCodes.length &&
                b.codes.every((c) => activeCodes.includes(c))
              return (
                <button
                  key={b.id}
                  onClick={() => applyBasket(b)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all border ${
                    isSelected
                      ? 'bg-accent-dim text-accent border-accent-line font-medium shadow-sm'
                      : 'bg-surface-2 text-dim hover:text-text border-line'
                  }`}
                  title={b.desc}
                >
                  <span>{b.icon}</span>
                  <span>{b.name}</span>
                </button>
              )
            })}
          </div>

          {/* Чартын хэлбэр сонгогч */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-dim hidden sm:inline">Хэлбэр:</span>
            <div className="flex items-center bg-surface-2 p-0.5 rounded-lg border border-line text-xs font-mono">
              {[
                { id: 'combo', label: 'Хосолсон', icon: BarChart3 },
                { id: 'area', label: 'Талбайт', icon: TrendingUp },
                { id: 'panels', label: 'Панелууд', icon: Layers },
                { id: 'yoy', label: 'YoY %', icon: Activity },
              ].map((t) => {
                const Icon = t.icon
                const active = chartType === t.id
                return (
                  <button
                    key={t.id}
                    onClick={() => setChartType(t.id)}
                    className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition-all ${
                      active
                        ? 'bg-accent-dim text-accent border border-accent-line font-medium'
                        : 'text-dim hover:text-text'
                    }`}
                  >
                    <Icon size={12} />
                    <span>{t.label}</span>
                  </button>
                )
              })}
            </div>

            {/* Хуваарь: Бодит / 100% Индекс */}
            <div className="flex items-center bg-surface-2 p-0.5 rounded-lg border border-line text-xs font-mono">
              <button
                onClick={() => setViewMode('actual')}
                className={`px-2 py-1 rounded-md transition-all ${
                  viewMode === 'actual'
                    ? 'bg-accent-dim text-accent border border-accent-line font-medium'
                    : 'text-dim hover:text-text'
                }`}
              >
                Бодит
              </button>
              <button
                onClick={() => setViewMode('indexed')}
                className={`px-2 py-1 rounded-md transition-all ${
                  viewMode === 'indexed'
                    ? 'bg-accent-dim text-accent border border-accent-line font-medium'
                    : 'text-dim hover:text-text'
                }`}
                title="Эхний жилийг 100% суурь болгон харьцуулах"
              >
                100% Индекс
              </button>
            </div>
          </div>
        </div>

        {/* Мөр 2: Хугацааны нарийвчилсан Range сонгогч */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-line/50 pb-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5 bg-surface-2 px-3 py-1 rounded-lg border border-line text-xs font-mono">
              <Calendar size={13} className="text-accent" />
              <span className="text-dim">Эхлэх он:</span>
              <select
                value={startYear}
                onChange={(e) => {
                  const val = Number(e.target.value)
                  if (val < endYear) {
                    setStartYear(val)
                    setRangePreset('custom')
                  }
                }}
                className="bg-transparent text-accent font-bold outline-none cursor-pointer"
              >
                {ALL_YEARS.filter((y) => y < endYear).map((y) => (
                  <option key={y} value={y} className="bg-ink-900 text-text">
                    {y}
                  </option>
                ))}
              </select>

              <span className="text-dim mx-1">—</span>

              <span className="text-dim">Дуусах он:</span>
              <select
                value={endYear}
                onChange={(e) => {
                  const val = Number(e.target.value)
                  if (val > startYear) {
                    setEndYear(val)
                    setRangePreset('custom')
                  }
                }}
                className="bg-transparent text-accent font-bold outline-none cursor-pointer"
              >
                {ALL_YEARS.filter((y) => y > startYear).map((y) => (
                  <option key={y} value={y} className="bg-ink-900 text-text">
                    {y}
                  </option>
                ))}
              </select>

              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-surface-3 text-dim ml-1">
                {endYear - startYear + 1} жил
              </span>
            </div>

            {/* Хугацааны шуурхай пресетүүд */}
            <div className="flex items-center gap-1 text-xs font-mono">
              {[
                { id: 'all', label: 'Бүх үе (1990–2026)' },
                { id: 'post2000', label: '2000 оноос хойш' },
                { id: 'last10', label: 'Сүүлийн 10 жил' },
                { id: 'transition', label: 'Шилжилт (1990–2000)' },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => applyPreset(p.id)}
                  className={`px-2 py-1 rounded text-[11px] transition-all ${
                    rangePreset === p.id
                      ? 'bg-surface-3 text-accent font-medium border border-line'
                      : 'text-dim hover:text-text'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Мөр 3: Ангиллын таб болон Үзүүлэлтүүдийн сонгогч чипсүүд */}
        <div className="space-y-2">
          {/* Ангиллын таб */}
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-xs font-mono text-dim mr-1 flex items-center gap-1">
              <Filter size={12} />
              <span>Ангилал:</span>
            </span>
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition-all ${
                  selectedCategory === cat.id
                    ? 'bg-accent-dim text-accent border border-accent-line font-medium'
                    : 'text-dim hover:text-text bg-surface-2 border border-transparent'
                }`}
              >
                <span>{cat.icon}</span> <span className="ml-0.5">{cat.label}</span>
              </button>
            ))}
          </div>

          {/* Үзүүлэлтүүдийн чипсүүд */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {filteredConfigs.map(([code, conf]) => {
              const active = activeCodes.includes(code)
              return (
                <button
                  key={code}
                  onClick={() => toggleCode(code)}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all border ${
                    active
                      ? 'bg-surface-2 text-text border-line-strong shadow-sm'
                      : 'bg-transparent text-faint border-line/30 hover:border-line'
                  }`}
                >
                  <span
                    className="w-2 h-2 rounded-full transition-transform"
                    style={{
                      backgroundColor: conf.color,
                      transform: active ? 'scale(1.2)' : 'scale(0.8)',
                      opacity: active ? 1 : 0.4,
                    }}
                  />
                  <span className={active ? 'font-medium' : ''}>{conf.name}</span>
                  {active && <Check size={12} className="text-accent" />}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* ── Интерактив вектор SVG График самбар ───────────────────────────────── */}
      <div className="glass-strong p-6 rounded-2xl border border-line-strong relative overflow-hidden shadow-[0_4px_32px_rgba(0,0,0,0.4)]">
        {loading && (
          <div className="absolute inset-0 bg-ink-950/75 backdrop-blur-sm z-30 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3 font-mono text-xs text-accent">
              <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              <span>Түүхэн тоон цувааг боловсруулж байна...</span>
            </div>
          </div>
        )}

        {/* Графикийн тайлбар толгой */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span className="text-dim">Тэнхлэгийн хуваарь:</span>
            {chartType === 'panels' ? (
              <span className="text-accent font-medium">
                Салгасан Панелууд (Бүлэг тус бүр өөрийн масштабаар зэрэгцэн синхрончлогдоно)
              </span>
            ) : chartType === 'yoy' ? (
              <span className="text-ok font-medium">
                Жилийн өсөлтийн хурд (% YoY - 0% суурь шугамтай)
              </span>
            ) : viewMode === 'indexed' ? (
              <span className="text-accent font-medium">
                Суурь индекс 100% (Бүх өгөгдөл гараанаас хэрхэн тэлснийг харьцуулах)
              </span>
            ) : (
              <>
                <span className="text-amber-400 font-medium">Зүүн: Төсөв (их наяд ₮)</span>
                <span className="text-dim">|</span>
                <span className="text-accent font-medium">
                  Бусад үзүүлэлтүүд: Өөр өөрийн бодит үнийн мужаар авто-масштабтай
                </span>
              </>
            )}
          </div>

          <div className="text-[11px] font-mono text-dim flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            <span>Хулганаар чиглүүлж харна уу</span>
          </div>
        </div>

        {/* Үндсэн SVG График */}
        <div className="w-full overflow-x-auto relative">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${chartLayout?.width || 1060} ${chartLayout?.height || 440}`}
            className="w-full h-auto min-w-[780px] select-none cursor-crosshair"
            onMouseMove={(e) => {
              if (!chartLayout || !svgRef.current) return
              const rect = svgRef.current.getBoundingClientRect()
              const svgX = ((e.clientX - rect.left) / rect.width) * chartLayout.width
              const { minYr, maxYr, padding, plotWidth } = chartLayout
              const relX = svgX - padding.left
              if (relX >= 0 && relX <= plotWidth) {
                const yr = Math.round(minYr + (relX / plotWidth) * (maxYr - minYr))
                setHoveredYear(yr)
              }
            }}
          >
            <defs>
              {/* Gradient Area Fills */}
              {Object.entries(INDICATOR_CONFIGS).map(([code, conf]) => (
                <linearGradient
                  key={code}
                  id={`area-grad-${code}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="0%" stopColor={conf.color} stopOpacity="0.25" />
                  <stop offset="90%" stopColor={conf.color} stopOpacity="0.02" />
                </linearGradient>
              ))}

              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {chartLayout && (
              <>
                {/* ═══════════════════════════════════════════════════════════ */}
                {/* А. САЛГАСАН ПАНЕЛУУДЫН ГОРИМ (Small Multiples)             */}
                {/* ═══════════════════════════════════════════════════════════ */}
                {chartLayout.isPanels ? (
                  <>
                    {Object.entries(chartLayout.panels).map(([pKey, pInfo]) => (
                      <g key={pKey}>
                        {/* Панелийн гарчиг */}
                        <text
                          x={chartLayout.padding.left}
                          y={pInfo.top - 8}
                          className="text-[11px] font-mono font-bold"
                          fill={pInfo.color}
                        >
                          ▸ {pInfo.name} ({pInfo.unit})
                        </text>

                        {/* Панелийн торон шугамууд */}
                        {[0, 0.5, 1.0].map((r, ri) => {
                          const py = pInfo.top + pInfo.height * (1 - r)
                          const tickVal = pInfo.min + (pInfo.max - pInfo.min) * r
                          return (
                            <g key={ri}>
                              <line
                                x1={chartLayout.padding.left}
                                y1={py}
                                x2={chartLayout.padding.left + chartLayout.plotWidth}
                                y2={py}
                                stroke="rgba(56, 224, 255, 0.08)"
                                strokeDasharray="3 3"
                              />
                              <text
                                x={chartLayout.padding.left - 8}
                                y={py + 3}
                                textAnchor="end"
                                className="text-[10px] font-mono fill-dim"
                              >
                                {pKey === 'fiscal'
                                  ? `${tickVal.toFixed(1)} т`
                                  : pKey === 'macro'
                                  ? `${tickVal.toFixed(1)}`
                                  : `${Math.round(tickVal).toLocaleString()}`}
                              </text>
                            </g>
                          )
                        })}

                        {/* Панел доторх цуваанууд */}
                        {activeCodes.map((code) => {
                          if (!pInfo.codes.includes(code)) return null
                          const { linePath, areaPath, points } = generateSeriesPaths(code)
                          const conf = INDICATOR_CONFIGS[code]
                          return (
                            <g key={code}>
                              <path d={areaPath} fill={`url(#area-grad-${code})`} pointerEvents="none" />
                              <path
                                d={linePath}
                                fill="none"
                                stroke={conf.color}
                                strokeWidth={2.4}
                                strokeLinecap="round"
                                filter="url(#glow)"
                              />
                              {points.map((pt) => {
                                const isHov = hoveredYear === pt.year
                                return (
                                  <circle
                                    key={pt.year}
                                    cx={pt.x}
                                    cy={pt.y}
                                    r={isHov ? 5.5 : 2}
                                    fill={isHov ? '#FFFFFF' : conf.color}
                                    stroke={conf.color}
                                    strokeWidth={isHov ? 2 : 1}
                                  />
                                )
                              })}
                            </g>
                          )
                        })}
                      </g>
                    ))}
                  </>
                ) : chartLayout.isYoY ? (
                  /* ═══════════════════════════════════════════════════════════ */
                  /* Б. ЖИЛИЙН ӨСӨЛТИЙН ХУВЬ ГОРИМ (YoY Growth %)               */
                  /* ═══════════════════════════════════════════════════════════ */
                  <>
                    {/* Тэг (0%) суурь шугам */}
                    <line
                      x1={chartLayout.padding.left}
                      y1={chartLayout.zeroY}
                      x2={chartLayout.padding.left + chartLayout.plotWidth}
                      y2={chartLayout.zeroY}
                      stroke="rgba(56, 224, 255, 0.4)"
                      strokeWidth={1.5}
                    />
                    <text
                      x={chartLayout.padding.left - 10}
                      y={chartLayout.zeroY + 4}
                      textAnchor="end"
                      className="text-[10px] font-mono fill-accent font-bold"
                    >
                      0%
                    </text>

                    {[chartLayout.minY, chartLayout.maxY * 0.5, chartLayout.maxY].map(
                      (val, idx) => {
                        const y = chartLayout.getY(val)
                        if (!y) return null
                        return (
                          <g key={idx}>
                            <line
                              x1={chartLayout.padding.left}
                              y1={y}
                              x2={chartLayout.padding.left + chartLayout.plotWidth}
                              y2={y}
                              stroke="rgba(56, 224, 255, 0.08)"
                              strokeDasharray="3 3"
                            />
                            <text
                              x={chartLayout.padding.left - 10}
                              y={y + 3}
                              textAnchor="end"
                              className="text-[10px] font-mono fill-dim"
                            >
                              {val > 0 ? `+${val}%` : `${val}%`}
                            </text>
                          </g>
                        )
                      }
                    )}

                    {activeCodes.map((code) => {
                      const { linePath, points } = generateSeriesPaths(code)
                      const conf = INDICATOR_CONFIGS[code]
                      return (
                        <g key={code}>
                          <path
                            d={linePath}
                            fill="none"
                            stroke={conf.color}
                            strokeWidth={2.2}
                            strokeLinecap="round"
                          />
                          {points.map((pt) => {
                            const isHov = hoveredYear === pt.year
                            return (
                              <circle
                                key={pt.year}
                                cx={pt.x}
                                cy={pt.y}
                                r={isHov ? 5 : 2}
                                fill={isHov ? '#FFFFFF' : conf.color}
                                stroke={conf.color}
                              />
                            )
                          })}
                        </g>
                      )
                    })}
                  </>
                ) : (
                  /* ═══════════════════════════════════════════════════════════ */
                  /* В. ХОСОЛСОН (COMBO) & ТАЛБАЙТ (AREA) & СУУРЬ ИНДЕКС         */
                  /* ═══════════════════════════════════════════════════════════ */
                  <>
                    {/* Хэвтээ туслах тор шугамууд */}
                    {[0, 0.25, 0.5, 0.75, 1.0].map((ratio, idx) => {
                      const y = chartLayout.padding.top + chartLayout.plotHeight * (1 - ratio)
                      return (
                        <g key={idx}>
                          <line
                            x1={chartLayout.padding.left}
                            y1={y}
                            x2={chartLayout.padding.left + chartLayout.plotWidth}
                            y2={y}
                            stroke="rgba(56, 224, 255, 0.08)"
                            strokeDasharray="3 3"
                          />
                          {viewMode === 'indexed' ? (
                            <text
                              x={chartLayout.padding.left - 8}
                              y={y + 3}
                              textAnchor="end"
                              className="text-[10px] font-mono fill-dim"
                            >
                              {Math.round(chartLayout.maxIdx * ratio)}%
                            </text>
                          ) : (
                            <text
                              x={chartLayout.padding.left - 8}
                              y={y + 3}
                              textAnchor="end"
                              className="text-[10px] font-mono fill-amber-400"
                            >
                              {(chartLayout.maxBudget * ratio).toFixed(1)} т
                            </text>
                          )}
                        </g>
                      )
                    })}

                    {/* Combo горим: Төсвийг баганаар (Bars) зурах */}
                    {chartType === 'combo' &&
                      activeCodes.includes('budget_expenditure') &&
                      viewMode === 'actual' &&
                      data?.timeline?.map((pt) => {
                        const bVal = pt.values?.budget_expenditure
                        if (bVal === undefined || bVal === null) return null
                        const x = chartLayout.getX(pt.year)
                        const barW = Math.max(
                          5,
                          Math.min(20, (chartLayout.plotWidth / data.timeline.length) * 0.55)
                        )
                        const y = chartLayout.getYBudget(bVal)
                        const bH = chartLayout.padding.top + chartLayout.plotHeight - y
                        const isHov = hoveredYear === pt.year
                        return (
                          <rect
                            key={`bar-${pt.year}`}
                            x={x - barW / 2}
                            y={y}
                            width={barW}
                            height={bH}
                            rx={2}
                            fill="#F59E0B"
                            fillOpacity={isHov ? 0.85 : 0.35}
                            stroke="#F59E0B"
                            strokeWidth={isHov ? 1.5 : 0.8}
                            className="transition-all duration-150"
                          />
                        )
                      })}

                    {/* Бусад үзүүлэлтүүдийн Line & Area дүрслэл */}
                    {activeCodes.map((code) => {
                      if (chartType === 'combo' && code === 'budget_expenditure' && viewMode === 'actual')
                        return null

                      const { linePath, areaPath, points } = generateSeriesPaths(code)
                      const conf = INDICATOR_CONFIGS[code]
                      return (
                        <g key={code}>
                          <path d={areaPath} fill={`url(#area-grad-${code})`} pointerEvents="none" />
                          <path
                            d={linePath}
                            fill="none"
                            stroke={conf.color}
                            strokeWidth={2.4}
                            strokeLinecap="round"
                            filter="url(#glow)"
                          />
                          {points.map((pt) => {
                            const isHov = hoveredYear === pt.year
                            return (
                              <circle
                                key={pt.year}
                                cx={pt.x}
                                cy={pt.y}
                                r={isHov ? 5.5 : 2}
                                fill={isHov ? '#FFFFFF' : conf.color}
                                stroke={conf.color}
                                strokeWidth={isHov ? 2 : 1}
                              />
                            )
                          })}
                        </g>
                      )
                    })}
                  </>
                )}

                {/* ═══════════════════════════════════════════════════════════ */}
                {/* НИЙТЛЭГ ЭЛЕМЕНТҮҮД (X тэнхлэг, Crosshair, Milestone pins)     */}
                {/* ═══════════════════════════════════════════════════════════ */}
                {/* X Тэнхлэгийн жилүүд */}
                {data.timeline.map((pt) => {
                  const x = chartLayout.getX(pt.year)
                  const isDecade = pt.year % 5 === 0
                  const isHov = hoveredYear === pt.year
                  return (
                    <g key={`x-${pt.year}`}>
                      <line
                        x1={x}
                        y1={chartLayout.padding.top + chartLayout.plotHeight}
                        x2={x}
                        y2={chartLayout.padding.top + chartLayout.plotHeight + (isDecade ? 7 : 3)}
                        stroke={isHov ? '#38e0ff' : 'rgba(56, 224, 255, 0.25)'}
                        strokeWidth={isHov ? 1.5 : 1}
                      />
                      {(isDecade || isHov) && (
                        <text
                          x={x}
                          y={chartLayout.padding.top + chartLayout.plotHeight + 18}
                          textAnchor="middle"
                          className={`text-[10px] font-mono select-none ${
                            isHov ? 'fill-accent font-bold' : 'fill-dim'
                          }`}
                        >
                          {pt.year}
                        </text>
                      )}
                    </g>
                  )
                })}

                {/* Идэвхтэй оны босоо Crosshair шугам */}
                {hoveredYear && (
                  <line
                    x1={chartLayout.getX(hoveredYear)}
                    y1={chartLayout.padding.top}
                    x2={chartLayout.getX(hoveredYear)}
                    y2={chartLayout.padding.top + chartLayout.plotHeight}
                    stroke="rgba(56, 224, 255, 0.75)"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    pointerEvents="none"
                  />
                )}
              </>
            )}
          </svg>
        </div>

        {/* ── Идэвхтэй оны Дэлгэрэнгүй Card (Hover Tooltip) ────────────────────── */}
        {hoveredPoint && (
          <div className="mt-4 p-4 rounded-xl glass border border-accent-line/60 bg-ink-900/90 shadow-[0_8px_24px_rgba(0,0,0,0.6)] animate-fadeIn">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-line pb-2.5 mb-3">
              <div className="flex items-center gap-3">
                <span className="text-lg font-display font-bold text-accent">
                  {hoveredPoint.year} он
                </span>
                {hoveredPoint.cabinet && (
                  <span className="text-xs font-mono text-text bg-surface-2 px-2.5 py-1 rounded-md border border-line">
                    Ерөнхий сайд: <span className="text-accent font-medium">{hoveredPoint.cabinet}</span>
                  </span>
                )}
              </div>

              {hoveredPoint.milestone && (
                <div className="text-xs font-sans text-warn flex items-center gap-1.5 bg-warn-dim px-2.5 py-1 rounded-md border border-warn/30">
                  <Zap size={13} className="shrink-0" />
                  <span>{hoveredPoint.milestone}</span>
                </div>
              )}
            </div>

            {/* Үзүүлэлтүүдийн утгууд */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
              {activeCodes.map((code) => {
                const conf = INDICATOR_CONFIGS[code]
                const val = hoveredPoint.values?.[code]
                const yoy = hoveredPoint.yoy_growth?.[code]
                const src = hoveredPoint.sources?.[code]
                if (val === undefined || val === null) return null

                let dispVal = `${val} ${conf.unit}`
                if (code === 'budget_expenditure') {
                  dispVal =
                    val >= 1.0
                      ? `${val.toFixed(2)} их наяд ₮`
                      : `${(val * 1000).toFixed(1)} тэрбум ₮`
                } else if (
                  code.includes('rate') ||
                  code === 'meat_price_kg' ||
                  code === 'gold_price_mnt_gram' ||
                  code === 'housing_price_sqm'
                ) {
                  dispVal = `${Math.round(val).toLocaleString()} ${conf.unit}`
                } else if (code === 'population') {
                  dispVal = `${val} сая хүн`
                } else if (code === 'cpi_inflation') {
                  dispVal = `${val}%`
                } else if (code === 'bitcoin_usd') {
                  dispVal = `$${val.toLocaleString()}`
                }

                return (
                  <div
                    key={code}
                    className="p-2.5 rounded-lg bg-surface-2 border border-line/60 flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between text-[11px] font-mono text-dim mb-1">
                      <span className="flex items-center gap-1.5 truncate">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: conf.color }}
                        />
                        <span className="truncate">{conf.shortName}</span>
                      </span>
                      {yoy !== null && yoy !== undefined && (
                        <span
                          className={`font-mono text-[10px] px-1 rounded ${
                            yoy > 0
                              ? 'text-ok bg-ok-dim'
                              : yoy < 0
                              ? 'text-danger bg-danger-dim'
                              : 'text-dim bg-surface'
                          }`}
                        >
                          {yoy > 0 ? `+${yoy}%` : `${yoy}%`}
                        </span>
                      )}
                    </div>

                    <div className="text-sm font-display font-bold text-text truncate">
                      {dispVal}
                    </div>

                    {src && (
                      <button
                        onClick={() => setSelectedSource(src)}
                        className="mt-1.5 text-[10px] font-mono text-accent hover:underline flex items-center gap-1 truncate text-left"
                      >
                        <ShieldCheck size={11} className="shrink-0 text-ok" />
                        <span className="truncate">{src.title}</span>
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* ── 🔬 ШИНЖИЛГЭЭНИЙ ЛАБОРАТОРИ (Macro Analytics Lab) ──────────────────── */}
      <div className="glass-strong p-6 rounded-2xl border border-accent-line/60 space-y-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-line pb-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-accent uppercase tracking-widest">
              <Sparkles size={14} className="text-accent" />
              <span>Macro Analytics Toolkit & Quantitative Insights</span>
            </div>
            <h2 className="text-xl font-display font-bold text-text mt-1 flex items-center gap-2">
              <span>Шинжилгээний Лаборатори</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-3 text-accent border border-accent-line">
                4 Шинжлэх ухааны арга
              </span>
            </h2>
            <p className="text-xs text-dim mt-0.5">
              Өгөгдлүүдийн харилцан хамаарал, худалдан авах чадвар, өсөлтийн хурд ба Засгийн газруудын үеийн гүйцэтгэл
            </p>
          </div>

          {/* 4 Лабораторийн таб сонгогч */}
          <div className="flex flex-wrap items-center bg-surface-2 p-1 rounded-xl border border-line text-xs font-mono">
            {[
              { id: 'correlation', label: 'Корреляцийн матриц', icon: Flame },
              { id: 'ppp', label: 'Худалдан авах чадвар', icon: Scale },
              { id: 'cagr', label: 'CAGR ба Эрсдэл', icon: Award },
              { id: 'cabinet', label: 'Засгийн газруудын дүн', icon: History },
            ].map((tab) => {
              const Icon = tab.icon
              const active = activeLabTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveLabTab(tab.id)}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                    active
                      ? 'bg-accent-dim text-accent border border-accent-line font-bold shadow-sm'
                      : 'text-dim hover:text-text'
                  }`}
                >
                  <Icon size={14} />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* ── ТАБ 1: ПИРСОНЫ КОРРЕЛЯЦИЙН МАТРИЦ (Correlation Matrix & Heatmap) ── */}
        {activeLabTab === 'correlation' && (
          <div className="space-y-5 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Зүүн багана: 2D Heatmap Matrix */}
              <div className="lg:col-span-2 space-y-3">
                <div className="flex items-center justify-between text-xs font-mono text-dim">
                  <span>Пирсоны корреляцийн торлол (-1.0-аас +1.0)</span>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="flex items-center gap-1">
                      <span className="w-2.5 h-2.5 rounded bg-emerald-500 inline-block" /> Шууд өндөр (+1)
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2.5 h-2.5 rounded bg-rose-500 inline-block" /> Урвуу сөрөг (-1)
                    </span>
                  </div>
                </div>

                {analyticsData?.correlation ? (
                  <div className="overflow-x-auto rounded-xl border border-line bg-surface p-3">
                    <table className="w-full text-center text-xs font-mono border-collapse select-none">
                      <thead>
                        <tr>
                          <th className="p-2 text-left text-dim text-[10px] w-24">Үзүүлэлт</th>
                          {analyticsData.correlation.indicators.map((ind) => (
                            <th
                              key={ind.code}
                              className="p-1.5 text-[10px] font-mono truncate max-w-[70px]"
                              style={{ color: ind.color }}
                              title={ind.name}
                            >
                              {INDICATOR_CONFIGS[ind.code]?.shortName || ind.code}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {analyticsData.correlation.matrix.map((row, i) => {
                          const ind1 = analyticsData.correlation.indicators[i]
                          return (
                            <tr key={ind1.code} className="hover:bg-surface-2/40 transition-colors">
                              <td
                                className="p-2 text-left text-[11px] font-bold truncate max-w-[120px]"
                                style={{ color: ind1.color }}
                              >
                                {INDICATOR_CONFIGS[ind1.code]?.shortName || ind1.code}
                              </td>
                              {row.map((rVal, j) => {
                                const ind2 = analyticsData.correlation.indicators[j]
                                const isSelected =
                                  selectedPair &&
                                  ((selectedPair.ind1 === ind1.code && selectedPair.ind2 === ind2.code) ||
                                    (selectedPair.ind1 === ind2.code && selectedPair.ind2 === ind1.code))

                                let bgStyle = 'rgba(255, 255, 255, 0.02)'
                                let textCol = '#7c93a3'
                                if (rVal !== null && rVal !== undefined) {
                                  if (i === j) {
                                    bgStyle = 'rgba(56, 224, 255, 0.15)'
                                    textCol = '#38e0ff'
                                  } else if (rVal > 0) {
                                    bgStyle = `rgba(16, 185, 129, ${Math.min(0.85, rVal * 0.75 + 0.1)})`
                                    textCol = '#ffffff'
                                  } else if (rVal < 0) {
                                    bgStyle = `rgba(244, 63, 94, ${Math.min(0.85, Math.abs(rVal) * 0.75 + 0.1)})`
                                    textCol = '#ffffff'
                                  }
                                }

                                return (
                                  <td
                                    key={j}
                                    onClick={() => {
                                      if (i !== j && rVal !== null) {
                                        const p = analyticsData.correlation.pairs.find(
                                          (pair) =>
                                            (pair.ind1 === ind1.code && pair.ind2 === ind2.code) ||
                                            (pair.ind1 === ind2.code && pair.ind2 === ind1.code)
                                        )
                                        if (p) setSelectedPair(p)
                                      }
                                    }}
                                    className={`p-1.5 cursor-pointer text-[10px] font-mono transition-all rounded ${
                                      isSelected ? 'ring-2 ring-accent scale-105 z-10 font-bold' : ''
                                    }`}
                                    style={{ backgroundColor: bgStyle, color: textCol }}
                                    title={`${ind1.name} ↔ ${ind2.name}: ${rVal !== null ? rVal : 'N/A'}`}
                                  >
                                    {rVal !== null ? rVal.toFixed(2) : '—'}
                                  </td>
                                )
                              })}
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs font-mono text-dim">Корреляцийг тооцоолж байна...</div>
                )}
              </div>

              {/* Баруун багана: Сонгогдсон хосын нарийвчилсан тайлбар Card */}
              <div className="space-y-4">
                <div className="glass p-5 rounded-xl border border-accent-line space-y-3 bg-ink-900/60">
                  <div className="flex items-center gap-1.5 text-xs font-mono text-accent">
                    <Flame size={14} />
                    <span>Сонгосон хамаарлын дүгнэлт:</span>
                  </div>

                  {selectedPair ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-b border-line pb-2.5">
                        <div className="space-y-1">
                          <div className="text-sm font-display font-bold text-text">
                            {selectedPair.name1}
                          </div>
                          <div className="text-xs text-dim">болон</div>
                          <div className="text-sm font-display font-bold text-text">
                            {selectedPair.name2}
                          </div>
                        </div>
                        <div className="text-right">
                          <div
                            className={`text-2xl font-mono font-bold ${
                              selectedPair.r > 0 ? 'text-ok' : 'text-danger'
                            }`}
                          >
                            {selectedPair.r > 0 ? `+${selectedPair.r}` : selectedPair.r}
                          </div>
                          <span className="text-[10px] font-mono text-dim">
                            N = {selectedPair.n} жил
                          </span>
                        </div>
                      </div>

                      <p className="text-xs font-sans text-text/90 leading-relaxed bg-surface-2 p-3 rounded-lg border border-line">
                        {selectedPair.description}
                      </p>

                      <div className="text-[11px] font-mono text-dim space-y-1 pt-1">
                        <div>
                          ▸ <span className="text-accent font-medium">Шинжлэх ухааны утга:</span> $r$ коэффициент +1 руу тэмүүлэх тусам төсөв/үнийн тэлэлт нэг чиглэлд явагдсаныг нотолно.
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs font-mono text-dim py-4 text-center">
                      Зүүн талын торон дээр дарж хоёр үзүүлэлтийн хамаарлыг харна уу.
                    </div>
                  )}
                </div>

                {/* Топ өндөр хамаарлууд */}
                <div className="glass p-4 rounded-xl border border-line space-y-2.5">
                  <div className="text-xs font-mono font-bold text-text flex items-center justify-between">
                    <span>🔥 Хамгийн өндөр шууд хамаарлууд:</span>
                  </div>
                  <div className="space-y-1.5 max-h-[190px] overflow-y-auto pr-1">
                    {analyticsData?.correlation?.pairs?.slice(0, 5).map((p, idx) => (
                      <div
                        key={idx}
                        onClick={() => setSelectedPair(p)}
                        className="p-2 rounded-lg bg-surface hover:bg-surface-3 cursor-pointer text-xs font-mono flex items-center justify-between border border-line/40 transition-colors"
                      >
                        <span className="truncate max-w-[200px] text-dim">
                          {INDICATOR_CONFIGS[p.ind1]?.shortName} ↔ {INDICATOR_CONFIGS[p.ind2]?.shortName}
                        </span>
                        <span className="text-ok font-bold">+{p.r}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── ТАБ 2: ТӨГРӨГИЙН ХУДАЛДАН АВАХ ЧАДВАР (Purchasing Power Parity) ── */}
        {activeLabTab === 'ppp' && (
          <div className="space-y-6 animate-fadeIn">
            {/* Тооцоолуурын удирдлага */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl glass border border-line">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-dim">Суурь он:</span>
                  <select
                    value={pppBaseYear}
                    onChange={(e) => setPppBaseYear(Number(e.target.value))}
                    className="px-3 py-1.5 rounded-lg bg-surface-2 border border-line text-xs font-mono font-bold text-accent outline-none cursor-pointer"
                  >
                    {[1990, 1995, 2000, 2005, 2010, 2015, 2020].map((y) => (
                      <option key={y} value={y} className="bg-ink-900 text-text">
                        {y} он
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-dim">Төгрөгийн дүн:</span>
                  <input
                    type="number"
                    value={pppAmount}
                    onChange={(e) => setPppAmount(Math.max(1000, Number(e.target.value)))}
                    className="w-36 px-3 py-1.5 rounded-lg bg-surface-2 border border-line text-xs font-mono font-bold text-text outline-none focus:border-accent"
                  />
                  <span className="text-xs font-mono text-dim">₮</span>
                </div>

                {/* Шуурхай дүнгийн товчнууд */}
                <div className="flex items-center gap-1.5">
                  {[500000, 1000000, 5000000, 10000000].map((amt) => (
                    <button
                      key={amt}
                      onClick={() => setPppAmount(amt)}
                      className={`px-2 py-1 rounded text-[11px] font-mono transition-all ${
                        pppAmount === amt
                          ? 'bg-accent-dim text-accent border border-accent-line font-bold'
                          : 'bg-surface-2 text-dim hover:text-text border border-line'
                      }`}
                    >
                      {(amt / 1000000).toFixed(amt >= 1000000 ? 1 : 1)} сая ₮
                    </button>
                  ))}
                </div>
              </div>

              <div className="text-xs font-mono text-dim">
                Харгалзах одоогийн жишиг он: <span className="text-accent font-bold">2025/2026 он</span>
              </div>
            </div>

            {/* Зэрэгцүүлсэн харьцуулалт (Base Year vs Today) */}
            {analyticsData?.purchasing_power && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* 1. Мах (кг) */}
                <div className="glass p-4 rounded-xl border border-line space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-dim">
                    <span className="flex items-center gap-1.5 text-text font-bold">
                      <span>🥩</span> Мах (хонь, үхэр)
                    </span>
                    <span className="text-danger font-bold text-[11px]">
                      -{100 - (analyticsData.purchasing_power.retention_pct?.meat_kg || 0)}% уналт
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-1 border-t border-line/40">
                    <div>
                      <div className="text-[10px] font-mono text-dim">{pppBaseYear} онд:</div>
                      <div className="text-lg font-display font-bold text-accent">
                        {analyticsData.purchasing_power.base_purchases?.meat_kg?.toLocaleString()} <span className="text-xs font-sans text-dim">кг</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-dim">Өнөөдөр:</div>
                      <div className="text-lg font-display font-bold text-rose-400">
                        {analyticsData.purchasing_power.current_purchases?.meat_kg?.toLocaleString()} <span className="text-xs font-sans text-dim">кг</span>
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-surface-3 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-rose-500 h-full rounded-full transition-all"
                      style={{
                        width: `${Math.max(3, analyticsData.purchasing_power.retention_pct?.meat_kg || 0)}%`,
                      }}
                    />
                  </div>
                  <div className="text-[10px] font-mono text-dim flex justify-between">
                    <span>Үнэ цэнийн үлдэгдэл:</span>
                    <span className="text-text font-bold">{analyticsData.purchasing_power.retention_pct?.meat_kg}%</span>
                  </div>
                </div>

                {/* 2. Орон сууц (м²) */}
                <div className="glass p-4 rounded-xl border border-line space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-dim">
                    <span className="flex items-center gap-1.5 text-text font-bold">
                      <span>🏢</span> Орон сууцны талбай
                    </span>
                    <span className="text-danger font-bold text-[11px]">
                      -{100 - (analyticsData.purchasing_power.retention_pct?.housing_sqm || 0)}% уналт
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-1 border-t border-line/40">
                    <div>
                      <div className="text-[10px] font-mono text-dim">{pppBaseYear} онд:</div>
                      <div className="text-lg font-display font-bold text-accent">
                        {analyticsData.purchasing_power.base_purchases?.housing_sqm} <span className="text-xs font-sans text-dim">м²</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-dim">Өнөөдөр:</div>
                      <div className="text-lg font-display font-bold text-cyan-400">
                        {analyticsData.purchasing_power.current_purchases?.housing_sqm} <span className="text-xs font-sans text-dim">м²</span>
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-surface-3 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-cyan-500 h-full rounded-full transition-all"
                      style={{
                        width: `${Math.max(3, analyticsData.purchasing_power.retention_pct?.housing_sqm || 0)}%`,
                      }}
                    />
                  </div>
                  <div className="text-[10px] font-mono text-dim flex justify-between">
                    <span>Үнэ цэнийн үлдэгдэл:</span>
                    <span className="text-text font-bold">{analyticsData.purchasing_power.retention_pct?.housing_sqm}%</span>
                  </div>
                </div>

                {/* 3. Алт (грамм) */}
                <div className="glass p-4 rounded-xl border border-line space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-dim">
                    <span className="flex items-center gap-1.5 text-text font-bold">
                      <span>🪙</span> Цэвэр алт
                    </span>
                    <span className="text-danger font-bold text-[11px]">
                      -{100 - (analyticsData.purchasing_power.retention_pct?.gold_gram || 0)}% уналт
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-1 border-t border-line/40">
                    <div>
                      <div className="text-[10px] font-mono text-dim">{pppBaseYear} онд:</div>
                      <div className="text-lg font-display font-bold text-accent">
                        {analyticsData.purchasing_power.base_purchases?.gold_gram} <span className="text-xs font-sans text-dim">гр</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-dim">Өнөөдөр:</div>
                      <div className="text-lg font-display font-bold text-yellow-400">
                        {analyticsData.purchasing_power.current_purchases?.gold_gram} <span className="text-xs font-sans text-dim">гр</span>
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-surface-3 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-yellow-500 h-full rounded-full transition-all"
                      style={{
                        width: `${Math.max(3, analyticsData.purchasing_power.retention_pct?.gold_gram || 0)}%`,
                      }}
                    />
                  </div>
                  <div className="text-[10px] font-mono text-dim flex justify-between">
                    <span>Үнэ цэнийн үлдэгдэл:</span>
                    <span className="text-text font-bold">{analyticsData.purchasing_power.retention_pct?.gold_gram}%</span>
                  </div>
                </div>

                {/* 4. Ам.доллар ($) */}
                <div className="glass p-4 rounded-xl border border-line space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-dim">
                    <span className="flex items-center gap-1.5 text-text font-bold">
                      <span>💵</span> Ам.доллар (USD)
                    </span>
                    <span className="text-danger font-bold text-[11px]">
                      -{100 - (analyticsData.purchasing_power.retention_pct?.usd || 0)}% уналт
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-1 border-t border-line/40">
                    <div>
                      <div className="text-[10px] font-mono text-dim">{pppBaseYear} онд:</div>
                      <div className="text-lg font-display font-bold text-accent">
                        ${analyticsData.purchasing_power.base_purchases?.usd?.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-dim">Өнөөдөр:</div>
                      <div className="text-lg font-display font-bold text-emerald-400">
                        ${analyticsData.purchasing_power.current_purchases?.usd?.toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-surface-3 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all"
                      style={{
                        width: `${Math.max(3, analyticsData.purchasing_power.retention_pct?.usd || 0)}%`,
                      }}
                    />
                  </div>
                  <div className="text-[10px] font-mono text-dim flex justify-between">
                    <span>Үнэ цэнийн үлдэгдэл:</span>
                    <span className="text-text font-bold">{analyticsData.purchasing_power.retention_pct?.usd}%</span>
                  </div>
                </div>
              </div>
            )}

            {/* 1 сая төгрөгийн худалдан авах чадварын түүхэн уналтын лавлах хүснэгт */}
            {analyticsData?.purchasing_power?.benchmarks && (
              <div className="glass p-4 rounded-xl border border-line space-y-3">
                <div className="text-xs font-mono font-bold text-text flex items-center justify-between">
                  <span>📉 1 сая төгрөгөөр түүхэндээ юу авч болдог байсан бэ? (Benchmark Timeline)</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead>
                      <tr className="border-b border-line text-dim text-[11px]">
                        <th className="py-2 px-3">Он</th>
                        <th className="py-2 px-3 text-right text-rose-400">Мах (кг)</th>
                        <th className="py-2 px-3 text-right text-cyan-400">Орон сууц (м²)</th>
                        <th className="py-2 px-3 text-right text-yellow-400">Алт (грамм)</th>
                        <th className="py-2 px-3 text-right text-emerald-400">USD ($)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/30">
                      {analyticsData.purchasing_power.benchmarks.map((b) => (
                        <tr key={b.year} className="hover:bg-surface-2 transition-colors">
                          <td className="py-2 px-3 font-bold text-accent">{b.year} он</td>
                          <td className="py-2 px-3 text-right font-medium">
                            {b.meat_kg ? `${b.meat_kg.toLocaleString()} кг` : '—'}
                          </td>
                          <td className="py-2 px-3 text-right font-medium">
                            {b.housing_sqm ? `${b.housing_sqm} м²` : '—'}
                          </td>
                          <td className="py-2 px-3 text-right font-medium">
                            {b.gold_gram ? `${b.gold_gram} гр` : '—'}
                          </td>
                          <td className="py-2 px-3 text-right font-medium">
                            {b.usd ? `$${b.usd.toLocaleString()}` : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── ТАБ 3: CAGR БА САВАЛГАА / ЭРСДЭЛ (Growth vs Volatility Ranking) ── */}
        {activeLabTab === 'cagr' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono text-dim pb-2">
              <div>
                Нийлмэл жилийн дундаж өсөлт (CAGR %) болон Жилийн савалгаа (Volatility $\sigma$ %)
              </div>
              <div className="text-accent">
                Тухайн үеийн жилийн дундаж инфляц: <span className="font-bold text-pink-400">{analyticsData?.cagr_risk?.average_inflation_cagr}%</span>
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl border border-line">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="bg-ink-900 text-dim border-b border-line text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-3 w-12 text-center">Эрэмбэ</th>
                    <th className="py-3 px-3">Үзүүлэлт</th>
                    <th className="py-3 px-3 text-right">Эхлэх утга</th>
                    <th className="py-3 px-3 text-right">Сүүлийн утга</th>
                    <th className="py-3 px-3 text-right">Нийт өсөлт</th>
                    <th className="py-3 px-3 text-right text-accent font-bold">CAGR (%/жил)</th>
                    <th className="py-3 px-3 text-right">Савалгаа (σ)</th>
                    <th className="py-3 px-3 text-center">Инфляцийг давсан эсэх</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/30">
                  {analyticsData?.cagr_risk?.ranking?.map((item) => (
                    <tr key={item.code} className="hover:bg-surface-2 transition-colors">
                      <td className="py-2.5 px-3 text-center font-bold text-dim">
                        #{item.rank}
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: item.color }}
                          />
                          <span className="font-bold text-text">{item.name}</span>
                          <span className="text-[10px] text-dim font-normal">({item.unit})</span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-right text-dim">
                        {item.start_val?.toLocaleString()} ({item.start_year})
                      </td>
                      <td className="py-2.5 px-3 text-right text-text font-medium">
                        {item.end_val?.toLocaleString()} ({item.end_year})
                      </td>
                      <td className="py-2.5 px-3 text-right font-medium">
                        <span className="text-amber-400">+{item.total_multiplier}x</span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-accent text-sm">
                        {item.cagr_pct !== null ? `+${item.cagr_pct}%` : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-dim font-mono">
                        ±{item.volatility_pct}%
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {item.beats_inflation ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-ok-dim text-ok border border-ok/30">
                            <Check size={11} />
                            <span>Инфляцийг давсан</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-danger-dim text-danger border border-danger/30">
                            <span>Гүйцэгдсэн</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── ТАБ 4: ЗАСГИЙН ГАЗРУУДЫН ҮЕИЙН ДҮН (Cabinet Impact Scorecard) ── */}
        {activeLabTab === 'cabinet' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="text-xs font-mono text-dim pb-1">
              Үе үеийн Засгийн газар, танхимуудын бүрэн эрхийн хугацаанд гарсан гол макро үзүүлэлтүүдийн өөрчлөлт
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {analyticsData?.cabinet_scorecard?.map((cab) => (
                <div
                  key={cab.id}
                  className="glass p-4 rounded-xl border border-line hover:border-line-strong transition-all space-y-3"
                >
                  <div className="flex items-start justify-between gap-2 border-b border-line/40 pb-2.5">
                    <div>
                      <div className="text-sm font-display font-bold text-text">
                        {cab.name}
                      </div>
                      <div className="text-xs text-accent font-mono mt-0.5">
                        {cab.pm}
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-3 text-dim shrink-0">
                      {cab.start_year}–{cab.end_year} ({cab.duration_months} сар)
                    </span>
                  </div>

                  {/* Гол тоон өсөлтүүд */}
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="p-2 rounded bg-surface-2 border border-line/40">
                      <div className="text-[10px] text-dim">🏛️ Төсвийн зарлага:</div>
                      <div className={`font-bold ${cab.budget_growth_pct > 0 ? 'text-warn' : 'text-ok'}`}>
                        {cab.budget_growth_pct !== null ? `+${cab.budget_growth_pct}%` : '—'}
                      </div>
                    </div>
                    <div className="p-2 rounded bg-surface-2 border border-line/40">
                      <div className="text-[10px] text-dim">💵 USD ханш:</div>
                      <div className={`font-bold ${cab.usd_growth_pct > 0 ? 'text-danger' : 'text-ok'}`}>
                        {cab.usd_growth_pct !== null ? `+${cab.usd_growth_pct}%` : '—'}
                      </div>
                    </div>
                    <div className="p-2 rounded bg-surface-2 border border-line/40">
                      <div className="text-[10px] text-dim">🥩 Махны үнэ:</div>
                      <div className={`font-bold ${cab.meat_growth_pct > 0 ? 'text-danger' : 'text-ok'}`}>
                        {cab.meat_growth_pct !== null ? `+${cab.meat_growth_pct}%` : '—'}
                      </div>
                    </div>
                    <div className="p-2 rounded bg-surface-2 border border-line/40">
                      <div className="text-[10px] text-dim">📊 Дундаж инфляц:</div>
                      <div className="font-bold text-pink-400">
                        {cab.avg_inflation_pct !== null ? `${cab.avg_inflation_pct}%` : '—'}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Түүхэн өгөгдлийн том архив хүснэгт + Баганын тохиргоо ──────────────── */}
      <div className="glass p-6 rounded-2xl border border-line space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-line pb-4">
          <div>
            <h2 className="text-lg font-display font-bold text-text flex items-center gap-2">
              <Layers size={18} className="text-accent" />
              <span>Он оноорх нарийвчилсан тоон архив</span>
            </h2>
            <p className="text-xs text-dim mt-0.5">
              Холбогдох албан эх сурвалж, хууль тогтоомж, Засгийн газрын бүртгэлтэй хамт
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Баганын сонголт Popover товч */}
            <div className="relative">
              <button
                onClick={() => setShowColumnSelector(!showColumnSelector)}
                className="px-3 py-1.5 rounded-lg text-xs font-mono bg-surface-2 hover:bg-surface-3 text-text border border-line flex items-center gap-1.5 transition-all"
              >
                <SlidersHorizontal size={13} className="text-accent" />
                <span>Баганын тохиргоо ({visibleColumns.length})</span>
              </button>

              {/* Popover цонх */}
              {showColumnSelector && (
                <div className="absolute right-0 top-full mt-2 w-72 p-4 rounded-xl glass-strong border border-accent-line/80 shadow-[0_12px_32px_rgba(0,0,0,0.8)] z-40 space-y-3 animate-fadeIn">
                  <div className="flex items-center justify-between border-b border-line pb-2">
                    <span className="text-xs font-mono font-bold text-text">
                      Хүснэгтийн баганууд
                    </span>
                    <button
                      onClick={() => setShowColumnSelector(false)}
                      className="text-dim hover:text-text text-xs font-mono"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Шуурхай үйлдлүүд */}
                  <div className="flex items-center justify-between gap-1 text-[11px] font-mono border-b border-line/40 pb-2">
                    <button
                      onClick={() => updateVisibleColumns(activeCodes)}
                      className="text-accent hover:underline"
                    >
                      Графиктай ижилсүүлэх
                    </button>
                    <button
                      onClick={() => updateVisibleColumns(Object.keys(INDICATOR_CONFIGS))}
                      className="text-dim hover:text-text"
                    >
                      Бүгд
                    </button>
                  </div>

                  {/* Багануудын жагсаалт */}
                  <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                    {Object.entries(INDICATOR_CONFIGS).map(([code, conf]) => {
                      const isVis = visibleColumns.includes(code)
                      return (
                        <label
                          key={code}
                          className="flex items-center gap-2 text-xs font-mono cursor-pointer hover:bg-surface-2 p-1 rounded"
                        >
                          <input
                            type="checkbox"
                            checked={isVis}
                            onChange={(e) => {
                              if (e.target.checked) {
                                updateVisibleColumns([...visibleColumns, code])
                              } else {
                                if (visibleColumns.length > 1) {
                                  updateVisibleColumns(visibleColumns.filter((c) => c !== code))
                                }
                              }
                            }}
                            className="rounded border-line bg-surface-2 text-accent focus:ring-0 cursor-pointer"
                          />
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: conf.color }}
                          />
                          <span className={isVis ? 'text-text' : 'text-dim'}>
                            {conf.name}
                          </span>
                        </label>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Хүснэгтийн хайлт */}
            <div className="relative w-full md:w-64">
              <Search
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-dim"
              />
              <input
                type="text"
                placeholder="Он, Ерөнхий сайдаар хайх..."
                value={searchTable}
                onChange={(e) => setSearchTable(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-2 border border-line text-xs font-mono text-text placeholder-faint focus:outline-none focus:border-accent"
              />
            </div>
          </div>
        </div>

        {/* Хүснэгтийн контент */}
        <div className="overflow-x-auto rounded-xl border border-line/60">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-ink-900/80 text-dim border-b border-line text-[11px] uppercase tracking-wider">
                <th className="py-3 px-3">Он</th>
                <th className="py-3 px-3">Засгийн газар</th>
                {visibleColumns.map((c) => {
                  const conf = INDICATOR_CONFIGS[c]
                  return (
                    <th
                      key={c}
                      className="py-3 px-3 text-right"
                      style={{ color: conf.color }}
                    >
                      {conf.shortName}
                    </th>
                  )
                })}
                <th className="py-3 px-3">Түүхэн үйл явдал</th>
                <th className="py-3 px-3 text-center">Эх сурвалж</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/30">
              {filteredTimeline.map((row) => {
                const isHovered = hoveredYear === row.year

                return (
                  <tr
                    key={row.year}
                    onMouseEnter={() => setHoveredYear(row.year)}
                    className={`transition-colors cursor-pointer ${
                      isHovered ? 'bg-accent-dim/20 text-text' : 'hover:bg-surface-2 text-dim'
                    }`}
                  >
                    {/* Он */}
                    <td className="py-2.5 px-3 font-bold text-accent font-display text-sm">
                      {row.year}
                    </td>

                    {/* Засгийн газар */}
                    <td className="py-2.5 px-3 text-text font-sans truncate max-w-[150px]">
                      {row.cabinet || '—'}
                    </td>

                    {/* Сонгогдсон динамик баганууд */}
                    {visibleColumns.map((c) => {
                      const val = row.values?.[c]
                      const yoy = row.yoy_growth?.[c]
                      const conf = INDICATOR_CONFIGS[c]
                      if (val === undefined || val === null) {
                        return (
                          <td key={c} className="py-2.5 px-3 text-right text-faint">
                            —
                          </td>
                        )
                      }

                      let disp = `${val}`
                      if (c === 'budget_expenditure') {
                        disp = val >= 1.0 ? `${val.toFixed(2)} т` : `${(val * 1000).toFixed(1)} трб`
                      } else if (c.includes('rate') || c === 'meat_price_kg' || c === 'housing_price_sqm' || c === 'gold_price_mnt_gram') {
                        disp = `${Math.round(val).toLocaleString()} ₮`
                      } else if (c === 'bitcoin_usd') {
                        disp = `$${val.toLocaleString()}`
                      } else if (c === 'cpi_inflation') {
                        disp = `${val}%`
                      } else if (c === 'population') {
                        disp = `${val} сая`
                      }

                      return (
                        <td key={c} className="py-2.5 px-3 text-right font-medium">
                          <div className="flex flex-col items-end">
                            <span style={{ color: conf.color }}>{disp}</span>
                            {yoy !== null && yoy !== undefined && (
                              <span
                                className={`text-[10px] ${
                                  yoy > 0 ? 'text-ok' : 'text-danger'
                                }`}
                              >
                                {yoy > 0 ? `+${yoy}%` : `${yoy}%`}
                              </span>
                            )}
                          </div>
                        </td>
                      )
                    })}

                    {/* Түүхэн үйл явдал */}
                    <td className="py-2.5 px-3 text-[11px] font-sans text-text/80 truncate max-w-[220px]">
                      {row.milestone ? (
                        <span className="flex items-center gap-1 text-warn">
                          <Zap size={11} className="shrink-0" />
                          <span className="truncate">{row.milestone}</span>
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>

                    {/* Эх сурвалж */}
                    <td className="py-2.5 px-3 text-center">
                      {row.sources && Object.values(row.sources)[0] ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedSource(Object.values(row.sources)[0])
                          }}
                          className="px-2 py-0.5 rounded text-[10px] font-mono bg-surface hover:bg-surface-3 text-accent border border-line inline-flex items-center gap-1"
                        >
                          <ShieldCheck size={10} className="text-ok" />
                          <span>Эх сурвалж</span>
                        </button>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Эх сурвалжийн дэлгэрэнгүй харах Модал ────────────────────────────── */}
      {selectedSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-950/80 backdrop-blur-md animate-fadeIn">
          <div className="glass-strong border border-accent-line p-6 rounded-2xl max-w-lg w-full space-y-4 shadow-[0_8px_32px_rgba(0,0,0,0.8)]">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2 text-xs font-mono text-accent">
                <ShieldCheck size={16} className="text-ok" />
                <span>Баталгаажсан эх сурвалжийн лавлагаа</span>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="text-dim hover:text-text font-mono text-sm px-2 py-1 rounded"
              >
                ✕
              </button>
            </div>

            <div>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-surface-3 text-accent border border-line">
                Ангилал: {selectedSource.category || 'Мэдээлэл'}
              </span>
              <h3 className="text-base font-display font-bold text-text mt-2 leading-snug">
                {selectedSource.title}
              </h3>
              {selectedSource.author && (
                <p className="text-xs text-dim font-mono mt-1">
                  Нийтлэгч / Байгууллага: {selectedSource.author}
                </p>
              )}
            </div>

            {selectedSource.url && (
              <div className="pt-2">
                <a
                  href={selectedSource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-mono bg-accent-dim text-accent border border-accent-line hover:bg-accent-line transition-all"
                >
                  <span>Эх холбоос нээх ({selectedSource.url.slice(0, 35)}...)</span>
                  <ExternalLink size={13} />
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
