import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { 
  FileText, Search, ExternalLink, Calendar, 
  ArrowUpDown, LayoutGrid, List, Landmark, BarChart3, 
  Newspaper, BookOpen, CheckCircle2, Globe, X
} from 'lucide-react'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import Spinner from '../components/ui/Spinner'
import GlassCard from '../components/ui/GlassCard'

const CATEGORY_CONFIG = {
  all: { label: 'Бүгд', icon: Globe, tone: 'neutral' },
  media: { label: 'Мэдээллийн сайтууд', icon: Newspaper, tone: 'neutral' },
  government: { label: 'Төрийн албан ёсны', icon: Landmark, tone: 'accent' },
  statistics: { label: 'ҮСХ & Статистик', icon: BarChart3, tone: 'ok' },
  encyclopedia: { label: 'Нэвтэрхий толь', icon: BookOpen, tone: 'neutral' },
  document: { label: 'Албан баримт', icon: FileText, tone: 'neutral' },
}

function getDomain(url) {
  if (!url) return null
  try {
    const u = new URL(url)
    return u.hostname.replace('www.', '')
  } catch {
    return url.split('/')[2] || url
  }
}

export default function SourceList() {
  const [sources, setSources] = useState(null)
  const [activeCategory, setActiveCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('facts_desc') // 'newest' | 'facts_desc' | 'date_desc' | 'title'
  const [viewMode, setViewMode] = useState('compact') // 'compact' | 'cards'

  useEffect(() => {
    api.listSources().then(setSources).catch(() => setSources([]))
  }, [])

  async function handleDelete(id, title) {
    if (!confirm(`"${title}" эх сурвалжийг устгах уу?`)) return
    await api.deleteSource(id)
    setSources((prev) => prev.filter((s) => s.id !== id))
  }

  // Category counts
  const categoryCounts = useMemo(() => {
    if (!sources) return {}
    const counts = { all: sources.length }
    for (const s of sources) {
      const cat = s.category || 'media'
      counts[cat] = (counts[cat] || 0) + 1
    }
    return counts
  }, [sources])

  // Overview statistics
  const stats = useMemo(() => {
    if (!sources) return { total: 0, totalFacts: 0, mediaCount: 0, govCount: 0 }
    let factsSum = 0
    let media = 0
    let gov = 0
    for (const s of sources) {
      factsSum += (s.facts_count || 0)
      if (s.category === 'media') media++
      if (s.category === 'government' || s.category === 'statistics') gov++
    }
    return {
      total: sources.length,
      totalFacts: factsSum,
      mediaCount: media,
      govCount: gov,
    }
  }, [sources])

  // Filtering and Sorting
  const filteredSources = useMemo(() => {
    if (!sources) return []
    let list = sources

    // 1. Category Filter
    if (activeCategory !== 'all') {
      list = list.filter((s) => (s.category || 'media') === activeCategory)
    }

    // 2. Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      list = list.filter((s) => 
        (s.title || '').toLowerCase().includes(q) ||
        (s.url || '').toLowerCase().includes(q) ||
        (s.author || '').toLowerCase().includes(q)
      )
    }

    // 3. Sorting
    return [...list].sort((a, b) => {
      if (sortBy === 'facts_desc') {
        return (b.facts_count || 0) - (a.facts_count || 0)
      }
      if (sortBy === 'newest') {
        return new Date(b.created_at || 0) - new Date(a.created_at || 0)
      }
      if (sortBy === 'date_desc') {
        return (b.publication_date || '').localeCompare(a.publication_date || '')
      }
      if (sortBy === 'title') {
        return (a.title || '').localeCompare(b.title || '')
      }
      return 0
    })
  }, [sources, activeCategory, searchQuery, sortBy])

  if (!sources) return <Spinner />

  return (
    <div className="space-y-6">
      {/* Толгой хэсэг */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-text">Эх сурвалжуудын бүртгэл</h1>
          <p className="text-sm text-dim mt-1">
            Баримт, төсөв, түүхэн үйл явдлын нотолгоо болох баталгаажсан эх сурвалжууд
          </p>
        </div>
        <Link
          to="/capture"
          className="bg-accent text-ink-950 font-semibold px-4 py-2 rounded-lg text-sm hover:bg-accent-bright transition-colors inline-flex items-center gap-2 self-start"
        >
          <span>+</span> Эх сурвалж нэмэх
        </Link>
      </div>

      {/* Статистик тоон үзүүлэлтүүд (Stat Cards) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <GlassCard className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-surface-2 text-accent">
            <FileText size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-text">{stats.total}</div>
            <div className="text-xs text-dim">Нийт эх сурвалж</div>
          </div>
        </GlassCard>

        <GlassCard className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-ok/10 text-ok">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-ok">{stats.totalFacts}</div>
            <div className="text-xs text-dim">Холбогдсон баримтууд</div>
          </div>
        </GlassCard>

        <GlassCard className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-accent/10 text-accent">
            <Landmark size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-accent">{stats.govCount}</div>
            <div className="text-xs text-dim">Төр ба Статистик</div>
          </div>
        </GlassCard>

        <GlassCard className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-surface-2 text-faint">
            <Newspaper size={20} />
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-text">{stats.mediaCount}</div>
            <div className="text-xs text-dim">Мэдээллийн хэвлэл</div>
          </div>
        </GlassCard>
      </div>

      {/* Ангиллын шүүлтүүр ба хяналтын самбар */}
      <div className="space-y-3">
        {/* Ангиллын табууд */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
          {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
            const Icon = config.icon
            const count = categoryCounts[key] || 0
            const isActive = activeCategory === key
            return (
              <button
                key={key}
                onClick={() => setActiveCategory(key)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all shrink-0 cursor-pointer ${
                  isActive
                    ? 'bg-accent text-ink-950 font-semibold shadow-sm'
                    : 'bg-surface hover:bg-surface-2 text-dim hover:text-text border border-line'
                }`}
              >
                <Icon size={14} />
                <span>{config.label}</span>
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                  isActive ? 'bg-ink-950/20 text-ink-950' : 'bg-surface-2 text-faint'
                }`}>
                  {count}
                </span>
              </button>
            )
          })}
        </div>

        {/* Хайлт, эрэмбэлэлт, харагдац солих */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
          {/* Хайлтын талбар */}
          <div className="relative w-full sm:w-80">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
            <input
              type="text"
              placeholder="Гарчиг, сайт, зохиогчоор хайх..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface border border-line rounded-lg pl-9 pr-8 py-1.5 text-xs text-text placeholder:text-faint focus:outline-none focus:border-accent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-faint hover:text-text"
              >
                <X size={13} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto w-full sm:w-auto justify-end">
            {/* Эрэмбэлэлт */}
            <div className="flex items-center gap-1.5 text-xs text-dim">
              <ArrowUpDown size={13} className="text-faint" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-surface border border-line rounded-lg px-2.5 py-1.5 text-xs text-text focus:outline-none focus:border-accent cursor-pointer"
              >
                <option value="facts_desc">Баримтын тоогоор (Их нь эхэндээ)</option>
                <option value="newest">Сүүлд нэмэгдсэн</option>
                <option value="date_desc">Нийтлэгдсэн огноогоор</option>
                <option value="title">Цагаан толгойн дарааллаар</option>
              </select>
            </div>

            {/* Харагдацын горим */}
            <div className="flex items-center bg-surface border border-line rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('compact')}
                className={`p-1.5 rounded text-xs transition-colors ${
                  viewMode === 'compact' ? 'bg-surface-2 text-accent' : 'text-faint hover:text-text'
                }`}
                title="Товч хүснэгтэн харагдац"
              >
                <List size={15} />
              </button>
              <button
                onClick={() => setViewMode('cards')}
                className={`p-1.5 rounded text-xs transition-colors ${
                  viewMode === 'cards' ? 'bg-surface-2 text-accent' : 'text-faint hover:text-text'
                }`}
                title="Дэлгэрэнгүй карт харагдац"
              >
                <LayoutGrid size={15} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Үр дүнгийн жагсаалт */}
      {filteredSources.length === 0 ? (
        <EmptyState icon={FileText} title="Хайлтад тохирох эх сурвалж олдсонгүй">
          {searchQuery || activeCategory !== 'all' ? (
            <button
              onClick={() => { setSearchQuery(''); setActiveCategory('all'); }}
              className="text-accent hover:underline text-xs"
            >
              Шүүлтүүрийг цэвэрлэх
            </button>
          ) : (
            <Link to="/capture" className="text-accent hover:underline text-xs">
              Эхний эх сурвалжаа нэмэх →
            </Link>
          )}
        </EmptyState>
      ) : viewMode === 'compact' ? (
        /* 1. Товч хүснэгтэн харагдац (High Density Table View) */
        <div className="glass rounded-xl overflow-hidden border border-line">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-line bg-surface/50 text-faint font-medium">
                  <th className="py-2.5 px-4 w-36">Ангилал</th>
                  <th className="py-2.5 px-4">Эх сурвалжийн гарчиг</th>
                  <th className="py-2.5 px-4 w-44">Домэйн / Сайт</th>
                  <th className="py-2.5 px-4 w-28">Огноо</th>
                  <th className="py-2.5 px-4 w-24 text-center">Баримт</th>
                  <th className="py-2.5 px-3 w-16 text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {filteredSources.map((s) => {
                  const catConfig = CATEGORY_CONFIG[s.category] || CATEGORY_CONFIG.media
                  const domain = getDomain(s.url)
                  const factsCount = s.facts_count || 0
                  return (
                    <tr key={s.id} className="hover:bg-surface-2/40 transition-colors group">
                      <td className="py-2.5 px-4">
                        <Badge tone={catConfig.tone}>
                          {catConfig.label}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-4">
                        <Link
                          to={`/sources/${s.id}`}
                          className="font-medium text-text hover:text-accent transition-colors line-clamp-1 leading-snug"
                        >
                          {s.title}
                        </Link>
                        {s.author && (
                          <span className="text-[11px] text-faint block mt-0.5">
                            ✎ {s.author}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-4">
                        {s.url ? (
                          <a
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-dim hover:text-accent font-mono text-[11px] inline-flex items-center gap-1 truncate max-w-[160px]"
                            title={s.url}
                          >
                            <span>{domain}</span>
                            <ExternalLink size={10} className="shrink-0 opacity-60" />
                          </a>
                        ) : (
                          <span className="text-faint italic font-mono text-[11px]">Бүртгэл</span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-faint text-[11px]">
                        {s.publication_date || '—'}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded-full font-mono text-xs ${
                          factsCount > 0
                            ? 'bg-accent/15 text-accent font-semibold'
                            : 'bg-surface text-faint'
                        }`}>
                          {factsCount}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={() => handleDelete(s.id, s.title)}
                          className="text-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity p-1"
                          title="Устгах"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* 2. Дэлгэрэнгүй картын харагдац (Detailed Cards View) */
        <div className="grid gap-3">
          {filteredSources.map((s) => {
            const catConfig = CATEGORY_CONFIG[s.category] || CATEGORY_CONFIG.media
            const domain = getDomain(s.url)
            const factsCount = s.facts_count || 0
            return (
              <div key={s.id} className="glass px-5 py-4 flex items-start gap-4 group rounded-xl border border-line">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <Badge tone={catConfig.tone}>{catConfig.label}</Badge>
                    {domain && (
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface border border-line text-dim">
                        {domain}
                      </span>
                    )}
                    {s.publication_date && (
                      <span className="text-xs text-faint font-mono flex items-center gap-1">
                        <Calendar size={12} />
                        {s.publication_date}
                      </span>
                    )}
                    <span className="ml-auto inline-flex items-center gap-1 text-xs font-mono text-accent bg-accent/10 px-2.5 py-0.5 rounded-full">
                      <strong>{factsCount}</strong> баримт
                    </span>
                  </div>

                  <Link
                    to={`/sources/${s.id}`}
                    className="font-medium text-text hover:text-accent transition-colors leading-snug block text-base"
                  >
                    {s.title}
                  </Link>

                  {s.selected_text && (
                    <p className="text-xs text-dim mt-2 line-clamp-2 leading-relaxed bg-surface/40 p-2 rounded border border-line/50 italic">
                      «{s.selected_text.slice(0, 160)}…»
                    </p>
                  )}

                  <div className="flex items-center gap-3 mt-3 text-xs text-faint flex-wrap">
                    <span
                      className="font-mono bg-surface px-2 py-0.5 rounded border border-line text-[11px]"
                      title="SHA-256 агуулгын хэш"
                    >
                      SHA: {s.sha256_hash.slice(0, 14)}…
                    </span>
                    {s.url && (
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-dim hover:text-accent inline-flex items-center gap-1 truncate max-w-sm"
                      >
                        <span className="truncate">{s.url}</span>
                        <ExternalLink size={11} className="shrink-0" />
                      </a>
                    )}
                    {s.author && <span>✎ {s.author}</span>}
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(s.id, s.title)}
                  className="text-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-all shrink-0 p-1"
                  title="Устгах"
                >
                  ✕
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
