import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { CalendarClock, Flag } from 'lucide-react'
import EntityBadge, { ENTITY_TYPES, getPartyInfo } from '../components/entity/EntityBadge'
import Timeline from '../components/timeline/Timeline'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import { Input, Label, Select, TextArea } from '../components/ui/Field'
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'
import Tabs from '../components/ui/Tabs'
import { formatPeriod } from '../lib/dates'

function SentimentDot({ score }) {
  if (score == null) return <span className="inline-block w-2 h-2 rounded-full bg-line-strong mt-1.5 shrink-0" />
  if (score < -0.3) return <span title={`Сентимент: ${score}`} className="inline-block w-2 h-2 rounded-full bg-danger mt-1.5 shrink-0" />
  if (score > 0.3) return <span title={`Сентимент: ${score}`} className="inline-block w-2 h-2 rounded-full bg-ok mt-1.5 shrink-0" />
  return <span title={`Сентимент: ${score}`} className="inline-block w-2 h-2 rounded-full bg-line-strong mt-1.5 shrink-0" />
}

export default function EntityDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [entity, setEntity] = useState(null)
  const [facts, setFacts] = useState([])
  const [relationships, setRelationships] = useState([])
  const [incoming, setIncoming] = useState([])
  const [candidates, setCandidates] = useState([])
  const [summary, setSummary] = useState(null)
  const [flags, setFlags] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({ name: '', entity_type: 'person', description: '' })
  const [activeTab, setActiveTab] = useState('timeline')
  const [activeTag, setActiveTag] = useState(null)

  useEffect(() => {
    setLoading(true)
    api
      .getEntity(id)
      .then((e) => {
        // Нэгтгэгдсэн субъект → шинэ хаяг руу шилжинэ
        if (e.merged_into_id) {
          navigate(`/entities/${e.merged_into_id}`, { replace: true })
          return null
        }
        setEntity(e)
        setEditForm({ name: e.name, entity_type: e.entity_type, description: e.description || '' })
        return Promise.all([
          api.getEntityFacts(id),
          api.getEntityRelationships(id),
          api.getRelationshipCandidates(id),
          api.getIncomingRelationships(id),
          api.getEntitySummary(id),
          api.getEntityFlags(id),
        ]).then(([f, r, c, inc, sum, flg]) => {
          setFacts(f)
          setRelationships(r)
          setCandidates(c)
          setIncoming(inc)
          setSummary(sum)
          setFlags(flg)
        })
      })
      .catch((e) => alert('Алдаа: ' + e.message))
      .finally(() => setLoading(false))
  }, [id, navigate])

  const allTags = useMemo(() => {
    const map = {}
    for (const f of facts) for (const t of f.tags) map[t] = (map[t] || 0) + 1
    return Object.entries(map).sort((a, b) => b[1] - a[1])
  }, [facts])

  async function handleConfirmLink(relId) {
    await api.linkRelationship(relId, Number(id))
    setCandidates((prev) => prev.filter((c) => c.id !== relId))
    api.getIncomingRelationships(id).then(setIncoming)
  }

  async function handleRejectLink(relId) {
    await api.dismissRelationshipLink(relId, Number(id))
    setCandidates((prev) => prev.filter((c) => c.id !== relId))
  }

  async function handleUpdate(e) {
    e.preventDefault()
    const updated = await api.updateEntity(id, {
      name: editForm.name,
      entity_type: editForm.entity_type,
      description: editForm.description || null,
    })
    setEntity(updated)
    setEditing(false)
  }

  async function handleDelete() {
    if (!confirm(`"${entity.name}" субъектийг бүх фактуудтай нь устгах уу?\nЭнэ үйлдлийг буцааж болохгүй.`)) return
    try {
      await api.deleteEntity(id)
      navigate('/entities')
    } catch (e) {
      alert('Устгахад алдаа: ' + e.message)
    }
  }

  async function handleClearFacts() {
    if (!confirm(`"${entity.name}"-н бүх фактыг устгах уу?\nСубъект хэвээр үлдэнэ, зөвхөн фактууд цэвэрлэгдэнэ.`)) return
    try {
      await api.clearEntityFacts(id)
      setFacts([])
    } catch (e) {
      alert('Алдаа: ' + e.message)
    }
  }

  async function handleDeleteFact(factId) {
    if (!confirm('Энэ фактыг устгах уу?')) return
    await api.deleteFact(factId)
    setFacts((prev) => prev.filter((f) => f.id !== factId))
  }

  async function handleDeleteRelationship(relId) {
    if (!confirm('Энэ холбоосыг устгах уу?')) return
    await api.deleteRelationship(relId)
    setRelationships((prev) => prev.filter((r) => r.id !== relId))
  }

  if (loading) return <Spinner />
  if (!entity) return null

  const bioFacts = facts.filter((f) => f.fact_type === 'biographical')
  const chronFacts = facts
    .filter((f) => f.fact_type === 'chronological')
    .filter((f) => !activeTag || f.tags.includes(activeTag))

  const redCount = flags?.red_flags?.length || 0
  const greenCount = flags?.green_flags?.length || 0

  return (
    <div>
      {/* Толгой */}
      <div className="mb-6">
        <Link to="/entities" className="text-sm text-accent/80 hover:text-accent hover:underline mb-3 inline-block">
          ← Субъектүүд
        </Link>

        {editing ? (
          <GlassCard strong className="p-5">
            <form onSubmit={handleUpdate} className="grid gap-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>Үндсэн нэр</Label>
                  <Input
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>Төрөл</Label>
                  <Select
                    value={editForm.entity_type}
                    onChange={(e) => setEditForm({ ...editForm, entity_type: e.target.value })}
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
                <Label>Тайлбар</Label>
                <TextArea
                  rows={2}
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                />
              </div>
              <div className="flex gap-3">
                <Button variant="primary" type="submit">
                  Хадгалах
                </Button>
                <Button type="button" onClick={() => setEditing(false)}>
                  Цуцлах
                </Button>
              </div>
            </form>
          </GlassCard>
        ) : (
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="font-display text-3xl font-bold text-text">{entity.name}</h1>
                <EntityBadge type={entity.entity_type} />
                {entity.party_name && (() => {
                  const pInfo = getPartyInfo(entity.party_name)
                  return (
                    <span
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold border transition-all"
                      style={{
                        backgroundColor: pInfo.bg,
                        borderColor: pInfo.border,
                        color: pInfo.color,
                        boxShadow: `0 0 10px ${pInfo.border}`
                      }}
                      title={pInfo.name}
                    >
                      <Flag size={11} style={{ color: pInfo.color }} />
                      <span>{pInfo.name}</span>
                    </span>
                  )
                })()}
                {entity.is_stub && <Badge>Түүхий</Badge>}
              </div>
              {entity.aliases.length > 0 && (
                <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                  {entity.aliases.map((a) => (
                    <span
                      key={a.id}
                      className="text-xs text-dim bg-surface border border-line rounded-full px-2.5 py-0.5"
                    >
                      {a.alias}
                    </span>
                  ))}
                </div>
              )}
              {entity.description && (
                <p className="text-sm text-dim mt-2 max-w-xl leading-relaxed">{entity.description}</p>
              )}
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button size="sm" onClick={() => setEditing(true)}>
                ✎ Засах
              </Button>
              <Link
                to={`/entities/${id}/import`}
                className="bg-accent text-ink-950 font-semibold px-3 py-1.5 rounded-lg text-xs hover:bg-accent-bright transition-colors inline-flex items-center"
              >
                + Факт нэмэх
              </Link>
              {facts.length > 0 && (
                <Button size="sm" onClick={handleClearFacts} title="Бүх фактыг устгаад дахин оруулах">
                  ⟳ Цэвэрлэх
                </Button>
              )}
              <Button size="sm" variant="danger" onClick={handleDelete}>
                Устгах
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Хураангуй */}
      {summary && (
        <GlassCard className="p-5 mb-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-display font-semibold text-text">Хураангуй тойм</span>
            <span className="text-xs text-faint">({summary.stats.total_facts} факт)</span>
          </div>
          {entity.tldr_summary ? (
            <p className="text-sm text-text/90 leading-relaxed">{entity.tldr_summary}</p>
          ) : (
            <p className="text-xs text-faint italic">Хураангуй одоогоор бэлэн болоогүй.</p>
          )}
          <div className="flex flex-wrap gap-4 mt-3 pt-3 border-t border-line text-xs">
            <span className="text-dim">
              Намтар: <strong className="text-text">{summary.stats.biographical_facts}</strong>
            </span>
            <span className="text-dim">
              Он цаг: <strong className="text-text">{summary.stats.chronological_facts}</strong>
            </span>
            <span className="text-danger">
              Улаан туг: <strong>{summary.stats.red_flags}</strong>
            </span>
            <span className="text-ok">
              Ногоон туг: <strong>{summary.stats.green_flags}</strong>
            </span>
          </div>
        </GlassCard>
      )}

      {/* Туг товчоо */}
      {flags && (redCount > 0 || greenCount > 0) && (
        <div className="grid md:grid-cols-2 gap-4 mb-5">
          <GlassCard className="border-danger/30 p-4">
            <h3 className="text-sm font-semibold text-danger mb-2">Улаан туг ({redCount})</h3>
            <div className="space-y-1">
              {flags.red_flags.slice(0, 3).map((f) => (
                <p key={f.id} className="text-xs text-text/80 leading-relaxed">
                  • {f.fact_text}
                </p>
              ))}
              {redCount > 3 && (
                <button onClick={() => setActiveTab('flags')} className="text-xs text-danger hover:underline mt-1">
                  + {redCount - 3} дэлгэрэнгүй
                </button>
              )}
            </div>
          </GlassCard>
          <GlassCard className="border-ok/30 p-4">
            <h3 className="text-sm font-semibold text-ok mb-2">Ногоон туг ({greenCount})</h3>
            <div className="space-y-1">
              {flags.green_flags.slice(0, 3).map((f) => (
                <p key={f.id} className="text-xs text-text/80 leading-relaxed">
                  • {f.fact_text}
                </p>
              ))}
              {greenCount > 3 && (
                <button onClick={() => setActiveTab('flags')} className="text-xs text-ok hover:underline mt-1">
                  + {greenCount - 3} дэлгэрэнгүй
                </button>
              )}
            </div>
          </GlassCard>
        </div>
      )}

      {/* Холбоос баталгаажуулалт */}
      {candidates.length > 0 && (
        <GlassCard strong className="border-accent-line p-5 mb-5">
          <h2 className="font-display font-semibold text-accent mb-1">
            Баталгаажуулах ({candidates.length})
          </h2>
          <p className="text-xs text-dim mb-3">
            Дараах эх сурвалжуудад энэ нэр холбоосоор дурдагдсан байна. Эдгээр нь{' '}
            <strong className="text-text">{entity.name}</strong> мөн үү?
          </p>
          <div className="grid gap-2">
            {candidates.map((c) => (
              <div key={c.id} className="flex items-start gap-3 glass px-3 py-2.5 text-sm">
                <div className="flex-1 min-w-0">
                  <span className="text-text/90">
                    <Link to={`/entities/${c.source_entity_id}`} className="font-medium text-accent hover:underline">
                      {c.source_entity_name}
                    </Link>{' '}
                    — <span className="font-medium">{c.target_name}</span> <Badge>{c.rel_type}</Badge>{' '}
                    {formatPeriod(c.start_date, null, c.end_date, null) && (
                      <span className="text-xs text-faint ml-1">
                        {formatPeriod(c.start_date, null, c.end_date, null)}
                      </span>
                    )}
                  </span>
                  {c.source_quote && (
                    <p className="text-xs text-faint mt-1 italic border-l-2 border-line-strong pl-2">
                      «{c.source_quote.slice(0, 110)}
                      {c.source_quote.length > 110 ? '…' : ''}»
                    </p>
                  )}
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button size="sm" variant="ok" onClick={() => handleConfirmLink(c.id)}>
                    ✓ Тийм
                  </Button>
                  <Button size="sm" onClick={() => handleRejectLink(c.id)}>
                    Биш
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Холбоосууд */}
      {(relationships.length > 0 || incoming.length > 0) && (
        <GlassCard className="p-5 mb-5">
          <h2 className="font-display font-semibold text-text mb-3">Холбоосууд</h2>

          {incoming.length > 0 && (
            <div className="grid gap-2 mb-2">
              {incoming.map((r) => (
                <div key={`in-${r.id}`} className="flex items-start gap-3 text-sm border border-line rounded-lg px-3 py-2 bg-surface">
                  <span className="text-base shrink-0 mt-0.5 text-faint">←</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Link to={`/entities/${r.source_entity_id}`} className="font-medium text-accent hover:underline">
                        {r.source_entity_name}
                      </Link>
                      <Badge>{r.rel_type}</Badge>
                      {formatPeriod(r.start_date, null, r.end_date, null) && (
                        <span className="text-xs text-faint">
                          {formatPeriod(r.start_date, null, r.end_date, null)}
                        </span>
                      )}
                    </div>
                    {r.source_quote && (
                      <p className="text-xs text-faint mt-1 italic border-l-2 border-line-strong pl-2">
                        «{r.source_quote.slice(0, 110)}
                        {r.source_quote.length > 110 ? '…' : ''}»
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="grid gap-2">
            {relationships.map((r) => (
              <div key={r.id} className="flex items-start gap-3 text-sm border border-line rounded-lg px-3 py-2">
                <span className="shrink-0 mt-1 text-faint">
                  {(() => {
                    const { Icon } = ENTITY_TYPES[r.target_kind] || ENTITY_TYPES.other
                    return <Icon size={15} strokeWidth={1.75} />
                  })()}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {r.target_entity_id ? (
                      <Link to={`/entities/${r.target_entity_id}`} className="font-medium text-accent hover:underline">
                        {r.target_name}
                      </Link>
                    ) : (
                      <span className="font-medium text-text">{r.target_name}</span>
                    )}
                    <Badge>{r.rel_type}</Badge>
                    {formatPeriod(r.start_date, r.start_precision, r.end_date, r.end_precision) && (
                      <span className="text-xs text-faint">
                        {formatPeriod(r.start_date, r.start_precision, r.end_date, r.end_precision)}
                      </span>
                    )}
                  </div>
                  {r.source_quote && (
                    <p className="text-xs text-faint mt-1 italic border-l-2 border-line-strong pl-2">
                      «{r.source_quote.slice(0, 110)}
                      {r.source_quote.length > 110 ? '…' : ''}»
                    </p>
                  )}
                  {r.source_id && (
                    <Link to={`/sources/${r.source_id}`} className="text-xs text-accent/70 hover:text-accent hover:underline mt-0.5 inline-block">
                      ⎘ Эх сурвалж →
                    </Link>
                  )}
                </div>
                <button
                  onClick={() => handleDeleteRelationship(r.id)}
                  className="text-faint hover:text-danger shrink-0"
                  title="Устгах"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Табууд */}
      <Tabs
        className="mb-4"
        tabs={[
          { key: 'timeline', label: `Он цагийн хэлхээс (${chronFacts.length})` },
          { key: 'bio', label: `Намтар (${bioFacts.length})` },
          { key: 'flags', label: `Тугнууд (${redCount + greenCount})` },
        ]}
        active={activeTab}
        onChange={setActiveTab}
      />

      {/* Шошгын шүүлт */}
      {activeTab === 'timeline' && allTags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-5">
          <button
            onClick={() => setActiveTag(null)}
            className={`text-xs px-3 py-1 rounded-full border transition-colors ${
              activeTag === null
                ? 'bg-accent-dim text-accent border-accent-line'
                : 'border-line text-faint hover:text-dim'
            }`}
          >
            Бүгд
          </button>
          {allTags.map(([tag, count]) => (
            <button
              key={tag}
              onClick={() => setActiveTag(activeTag === tag ? null : tag)}
              className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                activeTag === tag
                  ? 'bg-accent-dim text-accent border-accent-line'
                  : 'border-line text-faint hover:text-dim'
              }`}
            >
              {tag} <span className="opacity-50">({count})</span>
            </button>
          ))}
        </div>
      )}

      {/* Таб: Он цагийн хэлхээс */}
      {activeTab === 'timeline' &&
        (chronFacts.length === 0 ? (
          <EmptyState icon={CalendarClock} title="Он цагийн баримт алга">
            {activeTag ? (
              `"${activeTag}" шошготой баримт байхгүй.`
            ) : (
              <Link to={`/entities/${id}/import`} className="text-accent hover:underline">
                Факт нэмэх →
              </Link>
            )}
          </EmptyState>
        ) : (
          <Timeline
            facts={chronFacts}
            onDeleteFact={handleDeleteFact}
            activeTag={activeTag}
            onTagClick={(t) => setActiveTag(t === activeTag ? null : t)}
          />
        ))}

      {/* Таб: Намтар */}
      {activeTab === 'bio' && (
        <GlassCard className="p-5">
          {bioFacts.length === 0 ? (
            <p className="text-faint text-sm text-center py-8">Намтрын баримт байхгүй байна.</p>
          ) : (
            <div className="grid gap-3">
              {bioFacts.map((f) => (
                <div key={f.id} className="flex items-start gap-3 text-sm">
                  <SentimentDot score={f.sentiment_score} />
                  <div className="flex-1 leading-relaxed">
                    <span className="text-text/90">{f.fact_text}</span>
                    {f.source_id && (
                      <Link
                        to={`/sources/${f.source_id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-medium text-accent/90 hover:text-accent bg-accent/10 hover:bg-accent/20 border border-accent/20 px-2 py-0.5 rounded ml-2 transition-colors"
                        title={f.source_title || 'Эх сурвалж'}
                      >
                        <span>⎘</span>
                        <span className="truncate max-w-[150px]">{f.source_title || 'Эх сурвалж'}</span>
                      </Link>
                    )}
                  </div>
                  {f.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 shrink-0">
                      {f.tags.map((t) => (
                        <span key={t} className="text-xs bg-surface-2 text-faint px-2 py-0.5 rounded-full">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={() => handleDeleteFact(f.id)}
                    className="text-faint hover:text-danger shrink-0"
                    title="Устгах"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {/* Таб: Тугнууд */}
      {activeTab === 'flags' && (
        <div className="grid gap-5">
          <GlassCard className="border-danger/30 p-5">
            <h3 className="font-semibold text-danger mb-3">Улаан туг — сөрөг, сэжигтэй ({redCount})</h3>
            {redCount === 0 ? (
              <p className="text-sm text-faint italic">Байхгүй.</p>
            ) : (
              <div className="space-y-2">
                {flags.red_flags.map((f) => (
                  <div key={f.id} className="glass px-4 py-3 text-sm">
                    <p className="text-text/90">{f.fact_text}</p>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      {f.fact_date && <span className="text-xs text-faint font-mono">{f.fact_date.slice(0, 10)}</span>}
                      {f.source_id && (
                        <Link to={`/sources/${f.source_id}`} className="text-xs text-accent/80 hover:underline inline-flex items-center gap-1">
                          ⎘ {f.source_title || 'Эх сурвалж'}
                        </Link>
                      )}
                      {f.tags.map((t) => (
                        <Badge key={t} tone="danger">{t}</Badge>
                      ))}
                      <span className="text-xs text-danger/70 ml-auto">оноо: {f.sentiment_score?.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>

          <GlassCard className="border-ok/30 p-5">
            <h3 className="font-semibold text-ok mb-3">Ногоон туг — эерэг, гавьяа ({greenCount})</h3>
            {greenCount === 0 ? (
              <p className="text-sm text-faint italic">Байхгүй.</p>
            ) : (
              <div className="space-y-2">
                {flags.green_flags.map((f) => (
                  <div key={f.id} className="glass px-4 py-3 text-sm">
                    <p className="text-text/90">{f.fact_text}</p>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      {f.fact_date && <span className="text-xs text-faint font-mono">{f.fact_date.slice(0, 10)}</span>}
                      {f.source_id && (
                        <Link to={`/sources/${f.source_id}`} className="text-xs text-accent/80 hover:underline inline-flex items-center gap-1">
                          ⎘ {f.source_title || 'Эх сурвалж'}
                        </Link>
                      )}
                      {f.tags.map((t) => (
                        <Badge key={t} tone="ok">{t}</Badge>
                      ))}
                      <span className="text-xs text-ok/70 ml-auto">оноо: +{f.sentiment_score?.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      )}
    </div>
  )
}
