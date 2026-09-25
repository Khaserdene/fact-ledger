import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { buildAnnotatedHtml } from '../lib/anchor'
import { formatFlexDate } from '../lib/dates'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'
import Tabs from '../components/ui/Tabs'

export default function SourceView() {
  const { id } = useParams()
  const [source, setSource] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('annotated')
  const [verifying, setVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState(null)

  useEffect(() => {
    setLoading(true)
    api
      .getSource(id)
      .then(setSource)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <Spinner />
  if (error) return <div className="text-danger text-center py-16">{error}</div>
  if (!source) return null

  async function dismissContradiction(contradictionId) {
    try {
      await api.updateContradiction(contradictionId, {
        status: 'dismissed',
        resolution_note: 'Ижил хүн олон албан тушаалыг давхцуулж ажиллаж болно — зөрчил биш гэж үнэлэв.',
      })
      const updated = await api.getSource(id)
      setSource(updated)
    } catch (e) {
      alert('Алдаа гарлаа: ' + e.message)
    }
  }

  const annotatedHtml = buildAnnotatedHtml(source.selected_text, source.facts || [])
  const contradictions = (source.facts || []).filter((f) => f.has_contradiction)
  const isArticle = source.source_type === 'article' && source.url

  async function handleVerify() {
    setVerifying(true)
    setVerifyResult(null)
    try {
      const res = await api.verifySource(id)
      setVerifyResult(res)
    } catch (e) {
      alert('Алдаа гарлаа: ' + e.message)    } finally {
      setVerifying(false)
    }
  }

  return (
    <div>
      {/* Толгой */}
      <div className="mb-6">
        <Link to="/sources" className="text-sm text-accent/80 hover:text-accent hover:underline mb-2 inline-block">
          ← Бүх эх сурвалжууд
        </Link>
        <h1 className="font-display text-2xl font-bold text-text leading-snug">{source.title}</h1>
        <div className="flex flex-wrap items-center gap-3 mt-3 text-sm text-faint">
          {source.publication_date && (
            <span className="font-mono text-xs">{source.publication_date}</span>
          )}
          {source.author && <span className="text-xs">✎ {source.author}</span>}
          <span
            className="font-mono bg-surface px-2 py-0.5 rounded border border-line text-xs"
            title="SHA-256 — агуулгын өөрчлөлтийн баталгаа"
          >
            SHA-256: {source.sha256_hash.slice(0, 20)}…
          </span>
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent/80 hover:text-accent hover:underline truncate max-w-xs text-xs"
            >
              Эх холбоос ↗
            </a>
          )}
          {isArticle && (
            <Button size="sm" onClick={handleVerify} disabled={verifying} className="ml-auto">
              {verifying ? 'Шалгаж байна…' : '⌖ Эх сурвалжийг тулгах'}
            </Button>
          )}
        </div>
      </div>

      {/* Тулгалтын үр дүн */}
      {verifyResult && (
        <GlassCard
          className={`mb-5 p-4 ${verifyResult.unchanged ? 'border-ok/40' : 'border-danger/40'}`}
        >
          <div className={`font-semibold mb-2 text-sm ${verifyResult.unchanged ? 'text-ok' : 'text-danger'}`}>
            {verifyResult.unchanged ? '✓ ' : '⚠ '}
            {verifyResult.message}
          </div>
          <div className="text-xs text-faint mb-3 font-mono bg-surface inline-block px-2 py-1 rounded border border-line">
            Одоогийн хэш: {verifyResult.live_raw_hash.slice(0, 20)}…
          </div>
          {verifyResult.diff_html && (
            <div
              className="bg-ink-900 p-4 rounded-lg border border-line overflow-x-auto text-xs font-mono diff-container"
              dangerouslySetInnerHTML={{ __html: verifyResult.diff_html }}
            />
          )}
        </GlassCard>
      )}

      {/* Зөрчлийн анхааруулга */}
      {contradictions.length > 0 && (
        <GlassCard className="border-danger/40 p-4 mb-5">
          <p className="text-danger font-semibold text-sm mb-2">
            ⚠ {contradictions.length} зөрчил илэрсэн
          </p>
          <ul className="space-y-2">
            {contradictions.map((f) => (
              <li key={f.id} className="text-danger/80 text-xs">
                <div className="flex items-start justify-between gap-3">
                  <span>• {f.fact_text}</span>
                  {f.contradictions?.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => dismissContradiction(c.id)}
                      title={c.reason}
                      className="shrink-0 text-[10px] font-mono text-faint hover:text-danger border border-line hover:border-danger/40 rounded-md px-2 py-1 transition-colors"
                    >
                      ЗӨРЧИЛ БИШ
                    </button>
                  ))}
                </div>
                {f.contradictions?.some((c) => c.reason) && (
                  <p className="text-faint mt-1 ml-3">
                    {f.contradictions.filter((c) => c.reason).map((c) => c.reason).join('; ')}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      <Tabs
        className="mb-4"
        tabs={[
          { key: 'annotated', label: 'Тодруулгатай текст' },
          { key: 'raw', label: 'Эх текст' },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === 'annotated' && (
        <>
          {(source.facts || []).length > 0 && (
            <div className="flex items-center gap-4 text-xs text-faint mb-4">
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-2 bg-accent-dim border-b-2 border-accent rounded-sm" />
                Баримтжуулсан текст
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-2 bg-danger-dim border-b-2 border-danger rounded-sm" />
                Зөрчилтэй баримт
              </span>
              <span className="opacity-60">(хулгана аваачихад дэлгэрэнгүй)</span>
            </div>
          )}

          <GlassCard className="p-6">
            <div
              className="text-sm leading-8 text-text/90 whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ __html: annotatedHtml }}
            />
          </GlassCard>

          {(source.facts || []).length > 0 && (
            <div className="mt-8">
              <h2 className="font-display text-lg font-semibold text-text mb-4">
                Холбогдсон баримтууд
              </h2>
              <div className="grid gap-2">
                {source.facts.map((f) => (
                  <div
                    key={f.id}
                    className={`glass px-4 py-3 text-sm ${f.has_contradiction ? 'border-danger/40' : ''}`}
                  >
                    <div className="flex items-start gap-2">
                      <Badge tone={f.fact_type === 'chronological' ? 'accent' : 'neutral'}>
                        {f.fact_type === 'chronological'
                          ? formatFlexDate(f.fact_date, f.date_precision, f.fact_date_end) || 'Огноогүй'
                          : 'Намтар'}
                      </Badge>
                      <span className="text-text/90 flex-1">{f.fact_text}</span>
                      {f.has_contradiction && <Badge tone="danger">⚠ Зөрчил</Badge>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {tab === 'raw' && (
        <div>
          <GlassCard className="p-4 mb-4 flex items-center justify-between text-sm">
            <span className="text-dim">
              Баталгаажуулсан бүтэн эх текст
              <span className="ml-2 text-faint">({source.selected_text.length} тэмдэгт)</span>
            </span>
            <button
              onClick={() => navigator.clipboard.writeText(source.selected_text)}
              className="text-accent/80 hover:text-accent hover:underline text-xs"
            >
              ⎘ Хуулах
            </button>
          </GlassCard>
          <GlassCard className="p-6">
            <pre className="text-sm leading-7 text-text/90 whitespace-pre-wrap font-sans">
              {source.selected_text}
            </pre>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
