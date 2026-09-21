import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Users, Flag } from 'lucide-react'
import EntityBadge, { ENTITY_TYPES, getPartyInfo } from '../components/entity/EntityBadge'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import { Input, Label, Select } from '../components/ui/Field'
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'

export default function EntityList() {
  const [entities, setEntities] = useState(null)
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [partyFilter, setPartyFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', entity_type: 'person', aliases: '' })
  const [creating, setCreating] = useState(false)

  function load() {
    api.listEntities().then(setEntities).catch(() => setEntities([]))
  }

  useEffect(load, [])

  const partyCounts = useMemo(() => {
    if (!entities) return []
    const counts = {}
    for (const e of entities) {
      if (e.party_name) counts[e.party_name] = (counts[e.party_name] || 0) + 1
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
  }, [entities])

  const filtered = useMemo(() => {
    if (!entities) return []
    let out = entities
    if (typeFilter) out = out.filter((e) => e.entity_type === typeFilter)
    if (partyFilter) out = out.filter((e) => e.party_name === partyFilter)
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      out = out.filter(
        (e) =>
          e.name.toLowerCase().includes(q) ||
          e.aliases.some((a) => a.alias.toLowerCase().includes(q))
      )
    }
    // Намаар нь бүлэглэж эрэмбэлэх
    if (partyFilter) out = [...out].sort((a, b) => (a.name > b.name ? 1 : -1))
    return out
  }, [entities, query, typeFilter, partyFilter])

  const presentTypes = useMemo(() => {
    if (!entities) return []
    return [...new Set(entities.map((e) => e.entity_type))]
  }, [entities])

  async function handleCreate(e) {
    e.preventDefault()
    setCreating(true)
    try {
      const aliases = form.aliases.split(',').map((s) => s.trim()).filter(Boolean)
      await api.createEntity({ name: form.name, entity_type: form.entity_type, aliases })
      setForm({ name: '', entity_type: 'person', aliases: '' })
      setShowCreate(false)
      load()
    } catch (err) {
      alert('Алдаа: ' + err.message)
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(entity) {
    if (!confirm(`"${entity.name}" субъектийг бүх фактуудтай нь устгах уу?\nЭнэ үйлдлийг буцааж болохгүй.`)) return
    await api.deleteEntity(entity.id)
    load()
  }

  if (!entities) return <Spinner />

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-text">Субъектүүд</h1>
          <p className="text-sm text-faint mt-1">{entities.length} профайл</p>
        </div>
        <Button variant="primary" onClick={() => setShowCreate((v) => !v)}>
          + Субъект үүсгэх
        </Button>
      </div>

      {showCreate && (
        <GlassCard strong className="p-5 mb-6">
          <form onSubmit={handleCreate} className="grid gap-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>Үндсэн нэр</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Доржийн Бат"
                  required
                />
              </div>
              <div>
                <Label>Төрөл</Label>
                <Select
                  value={form.entity_type}
                  onChange={(e) => setForm({ ...form, entity_type: e.target.value })}
                >
                  {Object.entries(ENTITY_TYPES).map(([key, t]) => (
                    <option key={key} value={key}>
                      {t.label}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <div>
              <Label>Нэрийн хувилбарууд (таслалаар)</Label>
              <Input
                value={form.aliases}
                onChange={(e) => setForm({ ...form, aliases: e.target.value })}
                placeholder="Д.Бат, Бат сайд, Доржийн Бат"
              />
            </div>
            <div className="flex gap-3">
              <Button variant="primary" type="submit" disabled={creating}>
                {creating ? 'Үүсгэж байна…' : 'Үүсгэх'}
              </Button>
              <Button type="button" onClick={() => setShowCreate(false)}>
                Цуцлах
              </Button>
            </div>
          </form>
        </GlassCard>
      )}

      {/* Хайлт + төрлийн шүүлт */}
      <div className="flex items-center gap-3 mb-3 flex-wrap">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Нэр эсвэл хувилбараар хайх…"
          className="max-w-xs"
        />
        {presentTypes.length > 1 && (
          <div className="flex gap-1.5 flex-wrap">
            <button
              onClick={() => setTypeFilter('')}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                !typeFilter
                  ? 'bg-accent-dim text-accent border-accent-line'
                  : 'border-line text-faint hover:text-dim'
              }`}
            >
              Бүгд
            </button>
            {presentTypes.map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(typeFilter === t ? '' : t)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  typeFilter === t
                    ? 'bg-accent-dim text-accent border-accent-line'
                    : 'border-line text-faint hover:text-dim'
                }`}
              >
                {(ENTITY_TYPES[t] || ENTITY_TYPES.other).label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Намаар ангилал */}
      {partyCounts.length > 0 && (
        <div className="flex items-center gap-2 mb-5 flex-wrap">
          <span className="terminal-label mr-1">НАМААР</span>
          <button
            onClick={() => setPartyFilter('')}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              !partyFilter
                ? 'bg-accent-dim text-accent border-accent-line'
                : 'border-line text-faint hover:text-dim'
            }`}
          >
            Бүгд
          </button>
          {partyCounts.map(([name, count]) => {
            const pInfo = getPartyInfo(name)
            const isActive = partyFilter === name
            return (
              <button
                key={name}
                onClick={() => setPartyFilter(isActive ? '' : name)}
                className="text-xs px-3 py-1.5 rounded-full border transition-all font-mono flex items-center gap-1.5"
                style={{
                  backgroundColor: isActive ? pInfo.bg : 'transparent',
                  borderColor: isActive ? pInfo.border : 'rgba(255,255,255,0.08)',
                  color: isActive ? pInfo.color : '#94a3b8',
                  boxShadow: isActive ? `0 0 10px ${pInfo.border}` : 'none'
                }}
              >
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: pInfo.color }}
                />
                <span>{pInfo.short || name}</span>
                <span className="text-faint">({count})</span>
              </button>
            )
          })}
        </div>
      )}

      {filtered.length === 0 ? (
        <EmptyState icon={Users} title="Субъект олдсонгүй">
          {entities.length === 0 ? 'Эхний субъектээ үүсгээрэй.' : 'Хайлтын үр дүн хоосон.'}
        </EmptyState>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {filtered.map((e) => {
            const pInfo = e.party_name ? getPartyInfo(e.party_name) : null
            return (
              <div key={e.id} className="glass p-4 group relative">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <EntityBadge type={e.entity_type} />
                    {pInfo && (
                      <span
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono border"
                        style={{
                          backgroundColor: pInfo.bg,
                          borderColor: pInfo.border,
                          color: pInfo.color
                        }}
                        title={pInfo.name}
                      >
                        <Flag size={9} style={{ color: pInfo.color }} />
                        <span>{pInfo.short}</span>
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(e)}
                    className="text-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-all"
                    title="Устгах"
                  >
                    ✕
                  </button>
                </div>
                <Link
                  to={`/entities/${e.id}`}
                  className="font-display font-semibold text-lg text-text hover:text-accent transition-colors block leading-snug"
                >
                  {e.name}
                </Link>
                {e.aliases.length > 0 && (
                  <p className="text-xs text-faint mt-1.5 leading-relaxed">
                    {e.aliases.slice(0, 3).map((a) => a.alias).join(' · ')}
                    {e.aliases.length > 3 && ` +${e.aliases.length - 3}`}
                  </p>
                )}
                {e.party_name && (
                  <p className="text-xs mt-1.5 font-mono flex items-center gap-1" style={{ color: pInfo?.color || '#eab308' }}>
                    <span>⚑</span> <span>{e.party_name}</span>
                  </p>
                )}
                {e.is_stub && (
                  <span className="inline-block mt-2 text-[10px] uppercase tracking-wider text-faint border border-line rounded px-1.5 py-0.5">
                    Түүхий
                  </span>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
