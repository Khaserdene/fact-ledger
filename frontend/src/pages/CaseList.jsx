import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import {
  FolderGit2,
  Plus,
  Search,
  ExternalLink,
  Calendar,
  Layers,
  FileCheck,
  Users,
  Clock,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Grid3X3,
  LayoutGrid
} from 'lucide-react'
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import CrossCaseMatrix from '../components/crosscase/CrossCaseMatrix'

export default function CaseList() {
  const [cases, setCases] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [activeView, setActiveView] = useState('cards') // 'cards' | 'matrix'
  const [crossCaseData, setCrossCaseData] = useState(null)
  const [crossLoading, setCrossLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newSlug, setNewSlug] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [creating, setCreating] = useState(false)
  const [createErr, setCreateErr] = useState('')

  const CATEGORY_TABS = [
    { id: 'ALL', label: 'Бүгд' },
    { id: 'scandal', label: '🚨 Авлига & Дуулиант хэрэг' },
    { id: 'crisis', label: '⚡ Засаглалын хямрал & Огцролт' },
    { id: 'megaproject', label: '🏗️ Мега төсөл & Хувьчлал' },
    { id: 'faction', label: '🌐 Фракц, Газар & Оффшор' },
    { id: 'procurement', label: '💰 Төсөв, Сан & Худалдан авалт' },
  ]

  const fetchCases = async () => {
    try {
      setLoading(true)
      const data = await api.listCases()
      setCases(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchCrossCaseData = async () => {
    if (crossCaseData) return
    try {
      setCrossLoading(true)
      const res = await api.getCrossCaseAnalysis(1) // get all cross cases
      setCrossCaseData(res)
    } catch (err) {
      console.error('Cross-case load error:', err)
    } finally {
      setCrossLoading(false)
    }
  }

  const handleTabChange = (view) => {
    setActiveView(view)
    if (view === 'matrix' && !crossCaseData) {
      fetchCrossCaseData()
    }
  }

  useEffect(() => {
    fetchCases()
  }, [])

  // Гарчиг бичихэд автоматаар slug үүсгэх
  const handleTitleChange = (val) => {
    setNewTitle(val)
    if (!newSlug || newSlug === slugify(newTitle)) {
      setNewSlug(slugify(val))
    }
  }

  function slugify(text) {
    return text
      .toString()
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^\w-]+/g, '')
      .replace(/--+/g, '-')
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newTitle.trim() || !newSlug.trim()) {
      setCreateErr('Гарчиг болон slug заавал шаардлагатай.')
      return
    }
    setCreating(true)
    setCreateErr('')
    try {
      const created = await api.createCase({
        title: newTitle.trim(),
        slug: newSlug.trim(),
        description: newDesc.trim() || null,
        status: 'DRAFT',
      })
      setShowCreateModal(false)
      setNewTitle('')
      setNewSlug('')
      setNewDesc('')
      setCases((prev) => [created, ...(prev || [])])
    } catch (err) {
      setCreateErr(err.message)
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (e, slug, title) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm(`"${title}" хэргийг устгах уу? (Master фактууд хадгалагдан үлдэнэ)`)) return
    try {
      await api.deleteCase(slug)
      setCases((prev) => prev.filter((c) => c.slug !== slug))
    } catch (err) {
      alert('Устгахад алдаа гарлаа: ' + err.message)
    }
  }

  const filteredCases = useMemo(() => {
    if (!cases) return []
    return cases.filter((c) => {
      if (statusFilter !== 'ALL' && c.status !== statusFilter) return false
      if (categoryFilter !== 'ALL' && (c.category || 'scandal') !== categoryFilter) return false
      if (search.trim()) {
        const s = search.toLowerCase()
        const matchTitle = c.title?.toLowerCase().includes(s)
        const matchDesc = c.description?.toLowerCase().includes(s)
        const matchSlug = c.slug?.toLowerCase().includes(s)
        if (!matchTitle && !matchDesc && !matchSlug) return false
      }
      return true
    })
  }, [cases, statusFilter, categoryFilter, search])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-line pb-6">
        <div>
          <div className="flex items-center gap-2">
            <FolderGit2 className="text-accent" size={24} />
            <h1 className="text-2xl font-bold font-display text-text tracking-wide">
              МӨРДЛӨГ & ХЭРГИЙН ДЭД-ГРАФ
            </h1>
          </div>
          <p className="text-xs font-mono text-dim mt-1.5 uppercase tracking-wider">
            Investigation & Case Canvas Editor (System Builder)
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="flex items-center p-1 bg-surface-1 border border-line rounded">
            <button
              onClick={() => handleTabChange('cards')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono transition ${
                activeView === 'cards'
                  ? 'bg-accent/15 text-accent font-bold border border-accent/40 shadow-sm'
                  : 'text-dim hover:text-text'
              }`}
            >
              <LayoutGrid size={14} />
              <span>ЖАГСААЛТ</span>
            </button>
            <button
              onClick={() => handleTabChange('matrix')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono transition ${
                activeView === 'matrix'
                  ? 'bg-accent/15 text-accent font-bold border border-accent/40 shadow-sm'
                  : 'text-dim hover:text-text'
              }`}
            >
              <Grid3X3 size={14} />
              <span>БҮЛЭГЛЭЛИЙН МАТРИЦ</span>
            </button>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-accent text-ink-950 font-mono text-xs font-bold rounded hover:bg-accent/90 transition shadow-[0_0_15px_rgb(56_224_255/0.2)]"
          >
            <Plus size={16} />
            ШИНЭ ХЭРЭГ ҮҮСГЭХ
          </button>
        </div>
      </div>

      {activeView === 'matrix' ? (
        <div>
          {crossLoading ? (
            <div className="py-24 flex flex-col items-center justify-center gap-3">
              <Spinner />
              <p className="text-xs font-mono text-dim animate-pulse">
                Бүлэглэлийн хөндлөн матриц өгөгдлийг тооцоолж байна...
              </p>
            </div>
          ) : (
            <CrossCaseMatrix data={crossCaseData} />
          )}
        </div>
      ) : (
        <>
          {/* Thematic Category Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {CATEGORY_TABS.map((cat) => {
              const isActive = categoryFilter === cat.id
              const count = cases
                ? cat.id === 'ALL'
                  ? cases.length
                  : cases.filter((c) => (c.category || 'scandal') === cat.id).length
                : 0

              return (
                <button
                  key={cat.id}
                  onClick={() => setCategoryFilter(cat.id)}
                  className={`px-3 py-1.5 rounded-md text-xs font-mono whitespace-nowrap transition flex items-center gap-2 border ${
                    isActive
                      ? 'bg-accent/15 border-accent text-accent shadow-[0_0_12px_rgb(56_224_255/0.15)] font-bold'
                      : 'bg-surface-1/80 border-line text-dim hover:text-text hover:border-line-bright'
                  }`}
                >
                  <span>{cat.label}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isActive ? 'bg-accent/30 text-accent' : 'bg-surface-2 text-faint'}`}>
                    {count}
                  </span>
                </button>
              )
            })}
          </div>

          {/* Filter & Search Bar */}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-dim" size={16} />
              <input
                type="text"
                placeholder="Хэргийн нэр, тодорхойлолтоор хайх..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-surface-1 border border-line rounded text-sm text-text font-mono placeholder:text-faint focus:border-accent focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-1 bg-surface-1 p-1 border border-line rounded w-full sm:w-auto overflow-x-auto">
              {['ALL', 'DRAFT', 'PUBLISHED', 'ARCHIVED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1 text-xs font-mono rounded transition ${
                    statusFilter === st
                      ? 'bg-accent-dim text-accent border border-accent-line'
                      : 'text-dim hover:text-text'
                  }`}
                >
                  {st === 'ALL' ? 'БҮГД' : st}
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {/* List / Cards */}
      {activeView === 'cards' && (
        loading ? (
          <div className="py-24 flex justify-center">
            <Spinner />
          </div>
        ) : error ? (
          <div className="p-4 bg-danger/10 border border-danger/30 rounded text-danger text-sm font-mono flex items-center gap-2">
            <AlertCircle size={16} /> {error}
          </div>
        ) : filteredCases.length === 0 ? (
          <EmptyState
            icon={FolderGit2}
            title="Хэрэг олдсонгүй"
            description={
              search
                ? 'Хайлтад тохирох мөрдлөгийн хэрэг олдсонгүй.'
                : 'Одоогоор ямар нэг мөрдлөгийн хэрэг бүртгэгдээгүй байна.'
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredCases.map((c) => {
              const linksCount = c.links_count ?? c.links?.length ?? 0
              return (
                <Link
                  key={c.id}
                  to={`/cases/${c.slug}`}
                  className="group block"
                >
                  <GlassCard className="p-5 h-full flex flex-col justify-between border-line group-hover:border-accent-line transition-all duration-200 group-hover:shadow-[0_0_20px_rgb(56_224_255/0.08)]">
                    <div>
                      <div className="flex items-start justify-between gap-3 mb-2.5">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                          <span className="text-xs font-mono text-dim tracking-wider">
                            /case/{c.slug}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {c.category && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-accent-line/60 bg-surface-2 text-accent">
                              {c.category === 'crisis'
                                ? '⚡ Хямрал'
                                : c.category === 'megaproject'
                                ? '🏗️ Мега төсөл'
                                : c.category === 'faction'
                                ? '🌐 Фракц & Оффшор'
                                : c.category === 'procurement'
                                ? '💰 Сан & Худалдан авалт'
                                : '🚨 Дуулиант хэрэг'}
                            </span>
                          )}
                          <Badge
                            tone={
                              c.status === 'PUBLISHED'
                                ? 'ok'
                                : c.status === 'ARCHIVED'
                                ? 'neutral'
                                : 'warn'
                            }
                          >
                            {c.status}
                          </Badge>
                          <button
                            title="Хэрэг устгах"
                            onClick={(e) => handleDelete(e, c.slug, c.title)}
                            className="text-dim hover:text-danger p-1 rounded hover:bg-surface-2 transition"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>

                      <h2 className="text-lg font-bold text-text group-hover:text-accent transition font-display mb-2">
                        {c.title}
                      </h2>

                      <p className="text-xs text-dim line-clamp-2 leading-relaxed mb-4">
                        {c.description || 'Нэмэлт тодорхойлолт бүртгэгдээгүй байна.'}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-line/60 flex items-center justify-between text-[11px] font-mono text-dim">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1">
                          <Layers size={13} className="text-accent" />
                          {linksCount} холбоос
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar size={13} />
                          {c.created_at ? new Date(c.created_at).toLocaleDateString('mn-MN') : '—'}
                        </span>
                      </div>
                      <span className="text-accent group-hover:translate-x-0.5 transition-transform">
                        Нээх →
                      </span>
                    </div>
                  </GlassCard>
                </Link>
              )
            })}
          </div>
        )
      )}

      {/* Шинэ хэрэг үүсгэх Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg bg-surface-1 border border-line rounded-lg shadow-2xl p-6 relative">
            <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
              <div className="flex items-center gap-2">
                <FolderGit2 className="text-accent" size={18} />
                <h3 className="font-bold text-text font-display">ШИНЭ МӨРДЛӨГИЙН ХЭРЭГ</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-dim hover:text-text font-mono text-sm"
              >
                ✕
              </button>
            </div>

            {createErr && (
              <div className="mb-4 p-2.5 bg-danger/10 border border-danger/30 rounded text-danger text-xs font-mono">
                {createErr}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-dim mb-1">
                  ХЭРГИЙН НЭР / ГАРЧИГ *
                </label>
                <input
                  type="text"
                  required
                  placeholder="ж: Нүүрсний хулгайн хэрэг"
                  value={newTitle}
                  onChange={(e) => handleTitleChange(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-2 border border-line rounded text-sm text-text font-mono focus:border-accent focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-dim mb-1">
                  URL SLUG * (латин, зураас)
                </label>
                <input
                  type="text"
                  required
                  placeholder="coal-theft-case"
                  value={newSlug}
                  onChange={(e) => setNewSlug(slugify(e.target.value))}
                  className="w-full px-3 py-2 bg-surface-2 border border-line rounded text-sm text-text font-mono focus:border-accent focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-dim mb-1">
                  ТОДОРХОЙЛОЛТ
                </label>
                <textarea
                  rows={3}
                  placeholder="Хэргийн товч тойм, хамрах хүрээ..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-2 border border-line rounded text-sm text-text font-mono focus:border-accent focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-line">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-line text-dim text-xs font-mono rounded hover:bg-surface-2"
                >
                  ЦУЦЛАХ
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-accent text-ink-950 text-xs font-mono font-bold rounded hover:bg-accent/90 disabled:opacity-50"
                >
                  {creating ? 'ҮҮСГЭЖ БАЙНА...' : 'ҮҮСГЭХ'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
