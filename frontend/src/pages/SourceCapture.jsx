import React, { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import Button from '../components/ui/Button'
import { Input } from '../components/ui/Field'
import GlassCard from '../components/ui/GlassCard'

const HEADING_STYLE = {
  h1: 'text-xl font-bold text-text',
  h2: 'text-lg font-bold text-text',
  h3: 'text-base font-semibold text-text',
  h4: 'text-sm font-semibold text-text/90',
  h5: 'text-sm font-semibold text-text/90',
  h6: 'text-sm font-semibold text-text/90',
}

const HEADING_TAGS = new Set(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

// ─── Блок toggle горим ───────────────────────────────────────────────────────

function BlockToggleMode({ blocks, activeBlocks, onToggle, onSelectAll, onClearAll }) {
  return (
    <div>
      <GlassCard className="px-4 py-3 text-sm text-dim mb-4 flex items-center justify-between">
        <span>
          <strong className="text-text">Горим 1:</strong> Хэсэг бүр дээр нэг дарж идэвхжүүлэх / цуцлах.
          <span className="ml-2 font-medium text-accent">
            {activeBlocks.size}/{blocks.length} сонгосон
          </span>
        </span>
        <div className="flex gap-3 text-xs">
          <button onClick={onSelectAll} className="text-accent hover:underline font-medium">
            Бүгд
          </button>
          <button onClick={onClearAll} className="text-accent hover:underline font-medium">
            Цуцлах
          </button>
        </div>
      </GlassCard>

      <div className="space-y-1.5 mb-6">
        {blocks.map((block, i) => {
          const isHeading = HEADING_TAGS.has(block.type)
          const active = activeBlocks.has(i)
          return (
            <div
              key={i}
              onClick={() => onToggle(i)}
              className={`cursor-pointer rounded-xl border select-none transition-all ${
                active
                  ? 'border-accent-line bg-accent-dim/60'
                  : 'border-line bg-surface hover:border-line-strong'
              } ${isHeading ? 'px-4 py-2.5' : 'px-4 py-3'}`}
            >
              <div className="flex items-start gap-2">
                <span
                  className={`mt-0.5 text-xs shrink-0 w-4 text-center ${
                    active ? 'text-accent' : 'text-faint'
                  }`}
                >
                  {active ? '✓' : '○'}
                </span>
                <span
                  className={
                    isHeading
                      ? HEADING_STYLE[block.type] + (active ? '' : ' opacity-40')
                      : `text-sm leading-relaxed ${active ? 'text-text/90' : 'text-faint'}`
                  }
                >
                  {block.text}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Маркер горим ────────────────────────────────────────────────────────────

function MarkerMode({ fullText, markedTexts, onAdd, onRemove }) {
  const containerRef = useRef(null)
  const [floatPos, setFloatPos] = useState(null)
  const [pendingText, setPendingText] = useState('')

  function handleMouseUp() {
    const sel = window.getSelection()
    const text = sel?.toString().trim()
    if (!text || text.length < 5) {
      setFloatPos(null)
      setPendingText('')
      return
    }
    const range = sel.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    const containerRect = containerRef.current.getBoundingClientRect()
    setFloatPos({
      top: rect.top - containerRect.top - 40,
      left: rect.left - containerRect.left,
    })
    setPendingText(text)
  }

  function handleAdd() {
    if (pendingText) {
      onAdd(pendingText)
      window.getSelection()?.removeAllRanges()
      setFloatPos(null)
      setPendingText('')
    }
  }

  function renderHighlighted() {
    if (markedTexts.length === 0) return fullText

    const parts = []
    const hits = []
    for (const mt of markedTexts) {
      let idx = fullText.indexOf(mt)
      while (idx !== -1) {
        hits.push({ start: idx, end: idx + mt.length, text: mt })
        idx = fullText.indexOf(mt, idx + 1)
      }
    }
    hits.sort((a, b) => a.start - b.start)

    let pos = 0
    for (const hit of hits) {
      if (hit.start < pos) continue
      if (hit.start > pos) parts.push(<span key={pos}>{fullText.slice(pos, hit.start)}</span>)
      parts.push(
        <mark key={hit.start} className="bg-accent-dim text-accent-bright rounded px-0.5">
          {fullText.slice(hit.start, hit.end)}
        </mark>
      )
      pos = hit.end
    }
    if (pos < fullText.length) parts.push(<span key={pos}>{fullText.slice(pos)}</span>)
    return parts
  }

  return (
    <div>
      <GlassCard className="px-4 py-3 text-sm text-dim mb-4">
        <strong className="text-text">Горим 2:</strong> Хулганаар дурын хэсгийг тодруулаад{' '}
        <kbd className="bg-surface-2 px-1.5 py-0.5 rounded text-xs font-mono border border-line">
          + Нэмэх
        </kbd>{' '}
        товч дарна.
        <span className="ml-2 font-medium text-accent">{markedTexts.length} хэсэг тэмдэглэсэн</span>
      </GlassCard>

      {markedTexts.length > 0 && (
        <div className="mb-4 space-y-1.5">
          {markedTexts.map((t, i) => (
            <div
              key={i}
              className="flex items-start gap-2 glass border-accent-line/50 px-3 py-2 text-sm"
            >
              <span className="flex-1 text-text/90 line-clamp-2">{t}</span>
              <button
                onClick={() => onRemove(i)}
                className="text-faint hover:text-danger shrink-0 text-base leading-none"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <div ref={containerRef} className="relative glass p-6" onMouseUp={handleMouseUp}>
        {floatPos && (
          <button
            onMouseDown={(e) => {
              e.preventDefault()
              handleAdd()
            }}
            style={{ top: floatPos.top, left: floatPos.left }}
            className="absolute z-20 bg-accent text-ink-950 text-xs font-bold px-2.5 py-1 rounded-full shadow-lg hover:bg-accent-bright select-none"
          >
            + Нэмэх
          </button>
        )}

        <div className="text-sm leading-8 text-text/90 whitespace-pre-wrap select-text font-sans">
          {renderHighlighted()}
        </div>
      </div>
    </div>
  )
}

// ─── Үндсэн компонент ────────────────────────────────────────────────────────

export default function SourceCapture() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [scraped, setScraped] = useState(null)
  const [activeBlocks, setActiveBlocks] = useState(new Set())
  const [markedTexts, setMarkedTexts] = useState([])
  const [mode, setMode] = useState('toggle')
  const [extractMethod, setExtractMethod] = useState('trafilatura')
  const [pubDate, setPubDate] = useState('')
  const [saving, setSaving] = useState(false)
  const [existingSource, setExistingSource] = useState(null)
  const navigate = useNavigate()

  const currentBlocks = React.useMemo(() => {
    if (!scraped) return []
    if (extractMethod === 'trafilatura') {
      return (scraped.trafilatura_text || '')
        .split('\n\n')
        .filter((t) => t.trim())
        .map((t) => ({ type: 'p', text: t }))
    }
    if (extractMethod === 'bs4') {
      return scraped.blocks || []
    }
    return []
  }, [scraped, extractMethod])

  React.useEffect(() => {
    setActiveBlocks(new Set(currentBlocks.map((_, i) => i)))
  }, [currentBlocks])

  async function handleScrape(e) {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    setScraped(null)
    setExistingSource(null)
    setMarkedTexts([])
    try {
      const [result, existing] = await Promise.all([
        api.scrape(url.trim()),
        api.findSourceByUrl(url.trim()),
      ])
      setScraped(result)
      setExistingSource(existing.length > 0 ? existing[0] : null)
      const today = new Date().toISOString().slice(0, 10)
      setPubDate(result.pub_date || today)
      setExtractMethod(result.trafilatura_text ? 'trafilatura' : 'bs4')
      setMode('toggle')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function toggleBlock(i) {
    setActiveBlocks((prev) => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })
  }

  function addMarkedText(text) {
    setMarkedTexts((prev) => (prev.includes(text) ? prev : [...prev, text]))
  }

  function removeMarkedText(i) {
    setMarkedTexts((prev) => prev.filter((_, idx) => idx !== i))
  }

  function getSelectedBlocks() {
    if (extractMethod === 'raw' || mode === 'marker') {
      return markedTexts
    }
    return [...activeBlocks].sort((a, b) => a - b).map((i) => currentBlocks[i].text)
  }

  function getRawText() {
    if (extractMethod === 'trafilatura') return scraped.trafilatura_text
    if (extractMethod === 'bs4') return scraped.blocks.map((b) => b.text).join('\n\n')
    if (extractMethod === 'raw') return scraped.raw_html
    return ''
  }

  const selectedCount =
    extractMethod === 'raw' || mode === 'marker' ? markedTexts.length : activeBlocks.size

  async function handleSave() {
    const selected = getSelectedBlocks()
    if (selected.length === 0) {
      alert('Хадгалах текст сонгоогүй байна.')
      return
    }
    setSaving(true)
    try {
      const source = await api.createSource({
        source_type: 'article',
        url: url.trim(),
        title: scraped.title,
        pub_date: pubDate || null,
        selected_blocks: selected,
        raw_text: getRawText(),
      })
      navigate(`/sources/${source.id}`)
    } catch (e) {
      alert('Хадгалахад алдаа: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  const methodBtn = (key, label) => (
    <button
      onClick={() => setExtractMethod(key)}
      className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
        extractMethod === key
          ? 'bg-accent-dim text-accent border border-accent-line'
          : 'text-dim hover:text-text border border-transparent'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-text mb-6">Нийтлэл нэмэх</h1>

      <form onSubmit={handleScrape} className="flex gap-3 mb-6">
        <Input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://  (мэдээний сайт эсвэл mn.wikipedia.org)"
          className="flex-1"
          required
        />
        <Button variant="primary" type="submit" disabled={loading} className="whitespace-nowrap">
          {loading ? 'Уншиж байна…' : 'Унших'}
        </Button>
      </form>

      {error && (
        <GlassCard className="border-danger/40 px-4 py-3 text-sm text-danger mb-6">
          ⚠ {error}
        </GlassCard>
      )}

      {scraped && (
        <div>
          {/* Мета мэдээлэл */}
          <GlassCard className="p-5 mb-5">
            <h2 className="font-display font-semibold text-text text-lg mb-3 leading-snug">
              {scraped.title}
            </h2>
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <label className="text-dim font-medium shrink-0">Нийтлэгдсэн огноо:</label>
              <Input
                type="date"
                value={pubDate}
                onChange={(e) => setPubDate(e.target.value)}
                className="w-auto"
              />
              {scraped.pub_date ? (
                <span className="text-ok text-xs">✓ Сайтаас автоматаар илрүүлсэн</span>
              ) : (
                <span className="text-faint text-xs">Сайтаас олдсонгүй — өнөөдрийн огноо</span>
              )}
            </div>
          </GlassCard>

          {/* Давхардсан URL анхааруулга */}
          {existingSource && (
            <GlassCard className="border-accent-line px-4 py-3 text-sm mb-5 flex items-center justify-between gap-4">
              <span className="text-dim">
                ⚠ Энэ линк өмнө нэмэгдсэн байна —{' '}
                <strong className="text-text">{existingSource.title}</strong>{' '}
                {existingSource.publication_date && `(${existingSource.publication_date})`}
              </span>
              <Link
                to={`/sources/${existingSource.id}`}
                className="shrink-0 text-accent font-medium hover:underline"
              >
                Харах →
              </Link>
            </GlassCard>
          )}

          {/* Текст ялгах арга */}
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <span className="text-sm text-faint font-medium mr-1">Текст унших арга:</span>
            {methodBtn('trafilatura', 'Ухаалаг ялгагч')}
            {methodBtn('bs4', 'Бүх блок')}
            {methodBtn('raw', 'Raw HTML')}
          </div>

          {extractMethod === 'bs4' && (
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm text-faint font-medium mr-1">Сонгох горим:</span>
              <Button
                size="sm"
                variant={mode === 'toggle' ? 'primary' : 'ghost'}
                onClick={() => setMode('toggle')}
              >
                ☑ Блок toggle
              </Button>
              <Button
                size="sm"
                variant={mode === 'marker' ? 'primary' : 'ghost'}
                onClick={() => setMode('marker')}
              >
                ✍ Маркер сонгох
              </Button>
            </div>
          )}

          {extractMethod === 'trafilatura' || (extractMethod === 'bs4' && mode === 'toggle') ? (
            <BlockToggleMode
              blocks={currentBlocks}
              activeBlocks={activeBlocks}
              onToggle={toggleBlock}
              onSelectAll={() => setActiveBlocks(new Set(currentBlocks.map((_, i) => i)))}
              onClearAll={() => setActiveBlocks(new Set())}
            />
          ) : (
            <MarkerMode
              fullText={
                extractMethod === 'trafilatura'
                  ? scraped.trafilatura_text
                  : extractMethod === 'raw'
                    ? scraped.raw_html
                    : scraped.blocks.map((b) => b.text).join('\n\n')
              }
              markedTexts={markedTexts}
              onAdd={addMarkedText}
              onRemove={removeMarkedText}
            />
          )}

          <div className="flex items-center gap-4 pt-2">
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={saving || selectedCount === 0}
            >
              {saving ? 'Хадгалж байна…' : `✓ Баталгаажуулж хадгалах (${selectedCount} хэсэг)`}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
