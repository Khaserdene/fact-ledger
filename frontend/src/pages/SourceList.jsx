import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { FileText } from 'lucide-react'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import Spinner from '../components/ui/Spinner'

const TYPE_LABELS = {
  article: { label: 'Нийтлэл', tone: 'accent' },
  note: { label: 'Тэмдэглэл', tone: 'neutral' },
  document: { label: 'Баримт бичиг', tone: 'neutral' },
}

export default function SourceList() {
  const [sources, setSources] = useState(null)

  useEffect(() => {
    api.listSources().then(setSources).catch(() => setSources([]))
  }, [])

  async function handleDelete(id, title) {
    if (!confirm(`"${title}" эх сурвалжийг устгах уу?`)) return
    await api.deleteSource(id)
    setSources((prev) => prev.filter((s) => s.id !== id))
  }

  if (!sources) return <Spinner />

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-text">Эх сурвалжууд</h1>
          <p className="text-sm text-faint mt-1">
            {sources.length} баталгаажсан эх сурвалж
          </p>
        </div>
        <Link
          to="/capture"
          className="bg-accent text-ink-950 font-semibold px-4 py-2 rounded-lg text-sm hover:bg-accent-bright transition-colors"
        >
          + Нэмэх
        </Link>
      </div>

      {sources.length === 0 ? (
        <EmptyState icon={FileText} title="Эх сурвалж алга">
          <Link to="/capture" className="text-accent hover:underline">
            Эхний нийтлэлээ нэмэх →
          </Link>
        </EmptyState>
      ) : (
        <div className="grid gap-3">
          {sources.map((s) => {
            const t = TYPE_LABELS[s.source_type] || TYPE_LABELS.article
            return (
              <div key={s.id} className="glass px-5 py-4 flex items-start gap-4 group">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <Badge tone={t.tone}>{t.label}</Badge>
                    {s.publication_date && (
                      <span className="text-xs text-faint font-mono">{s.publication_date}</span>
                    )}
                  </div>
                  <Link
                    to={`/sources/${s.id}`}
                    className="font-medium text-text hover:text-accent transition-colors leading-snug block"
                  >
                    {s.title}
                  </Link>
                  <div className="flex items-center gap-3 mt-2 text-xs text-faint">
                    <span
                      className="font-mono bg-surface px-2 py-0.5 rounded border border-line"
                      title="SHA-256 — агуулгын өөрчлөлтийн баталгаа"
                    >
                      {s.sha256_hash.slice(0, 16)}…
                    </span>
                    {s.url && (
                      <span className="truncate max-w-xs opacity-70">{s.url}</span>
                    )}
                    {s.author && <span>✎ {s.author}</span>}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(s.id, s.title)}
                  className="text-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-all shrink-0"
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
