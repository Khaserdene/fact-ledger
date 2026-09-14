import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import Button from '../components/ui/Button'
import { Select, TextArea } from '../components/ui/Field'
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'

// Анхаар: Phase 4-т энэ промпт сервер талд (backend/ai/prompts.py) шилжинэ.
const MASTER_PROMPT_TEMPLATE = (profileJson, articleText) => `Үүрэг: Чи бол "Өөрчлөгдөшгүй Үнэний Бүртгэл" системийн дата аналитик агент. Чиний зорилго бол өгөгдсөн профайлын хуучин дата болон шинэ нийтлэлийг харьцуулж, давхардаагүй шинэ фактуудыг олборлох болон логик зөрчлийг илрүүлэх явдал юм.

Оролтын өгөгдөл:

1. [ХУУЧИН_ПРОФАЙЛ_JSON]:
${JSON.stringify(profileJson, null, 2)}

2. [ШИНЭ_НИЙТЛЭЛ_ТЕКСТ]:
${articleText}

Гүйцэтгэх алхмууд:
1. [ШИНЭ_НИЙТЛЭЛ_ТЕКСТ] дотроос тухайн хүний үндсэн нэр эсвэл aliases доторх нэрсээр дурдагдсан фактуудыг түүж ав.
2. Эдгээр фактуудыг [ХУУЧИН_ПРОФАЙЛ_JSON] доторх фактуудтай харьцуул. Давхардлыг дараах байдлаар тодорхойл:
   - Он цагийн факт: "date" болон "fact" утга хоёулаа ижил буюу ойролцоо утгатай бол давхардал гэж үз
   - Намтар факт: "fact" утга ижил буюу ойролцоо утгатай бол давхардал гэж үз
   - Давхардал илэрвэл ШУУД АЛГАС — шинэ жагсаалтад оруулахгүй.
3. Зөвхөн өмнө нь байхгүй байсан, цоо шинэ фактуудыг "он цагийн дараалалтай" (chronological) болон "он цагт хамаарахгүй намтар" (biographical) гэж ялгаж ав.
4. Холбоос задлах: Тухайн хүн өөр хүн эсвэл байгууллага (нам, компани, төр)-тэй ямар үүрэг/харилцаатай, аль хугацаанд холбогдсоныг relationships хэсэгт бүртгэ. Жишээ: "МАХН-ын дарга", "X компанийн хувьцаа эзэмшигч", "Y-н зөвлөх".
5. Зөрчил шалгах: Шинэ факт нь хуучин фактуудын аль нэгтэй цаг хугацаа, тоо баримт эсвэл утга санааны хувьд зөрчилдөж байвал түүнийг contradiction хэсэгт бүртгэ.
   ЧУХАЛ — Дараах тохиолдлуудыг ЗӨРЧИЛ гэж БҮРТГЭХГҮЙ:
   - Ижил хүн олон албан тушаал/ажлыг зэрэгцүүлж (давхцуулан) ажилласан байх. Жишээ: нэгэн зэрэг компанийн захирал, намын дарга байх нь хэвийн.
   - Эх сурвалжийн дэлгэрэнгүй байдлын зөрүү (нэг нь 1992 гэж, нөгөө нь 1990 гэж эхлүүлсэн мэт нарийвчлалын зөрүү) нь зөвхөн албан тушаал/үйл явдлын утга эсрэгцэж байвал л зөрчил.
   - Огнооны нарийвчлал өөр байх (нэг нь зөвхөн жил, нөгөө нь сар, өдөртэй).
6. Ишлэл уях: Факт болон холбоос гаргахдаа шинэ нийтлэл дотор байгаа яг тэр өгүүлбэрийг үг үсгийн алдаагүйгээр source_quote талбарт заавал хадгал.

Хариу буулгах формат: Зөвхөн доорх JSON бүтцээр хариуг өг. Өөр ямар ч нэмэлт тайлбар текст битгий бич.
ЧУХАЛ: JSON дотор string утгуудад давхар хашилт " ашиглахгүй. Жишээлбэл: "Үнэн" сонин гэхийн оронд «Үнэн» сонин буюу 'Үнэн' сонин гэж бич.

{
  "new_biographical_facts": [
    {
      "fact": "[Шинэ намтар факт]",
      "source_quote": "[Нийтлэл дэх яг тэр өгүүлбэр]"
    }
  ],
  "new_chronological_facts": [
    {
      "date": "YYYY-MM-DD эсвэл YYYY-MM эсвэл YYYY (зөвхөн жил мэдэгдэж байвал). 1968-1969 гэх хугацааны хүрзэлт бол: 1968-1969",
      "fact": "[Шинэ цаг хугацааны факт]",
      "source_quote": "[Нийтлэл дэх яг тэр өгүүлбэр]"
    }
  ],
  "new_relationships": [
    {
      "target_name": "[Холбоотой хүн эсвэл байгууллагын нэр]",
      "rel_type": "[Үүрэг/харилцаа: дарга, гишүүн, зөвлөх, хувьцаа эзэмшигч, түнш гэх мэт]",
      "target_kind": "person эсвэл org",
      "start_date": "YYYY эсвэл YYYY-MM эсвэл YYYY-MM-DD (мэдэгдэж байвал)",
      "end_date": "YYYY (дууссан бол; үргэлжилж байвал хоосон)",
      "source_quote": "[Нийтлэл дэх яг тэр өгүүлбэр]"
    }
  ],
  "contradictions_detected": [
    {
      "new_fact_quote": "[Шинэ нийтлэл дэх зөрчилтэй өгүүлбэр]",
      "contradicted_fact_id": "[Хуучин JSON доторх fact_id]",
      "reason": "[Яагаад зөрчилдөж буйн тайлбар]"
    }
  ]
}`

function StepBadge({ n }) {
  return (
    <span className="bg-accent text-ink-950 text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold shrink-0">
      {n}
    </span>
  )
}

export default function FactImport() {
  const { id } = useParams()
  const [entity, setEntity] = useState(null)
  const [sources, setSources] = useState([])
  const [selectedSourceId, setSelectedSourceId] = useState('')
  const [entityExport, setEntityExport] = useState(null)
  const [jsonInput, setJsonInput] = useState('')
  const [parseError, setParseError] = useState(null)
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [promptCopied, setPromptCopied] = useState(false)
  const [promptText, setPromptText] = useState('')
  const [showPrompt, setShowPrompt] = useState(false)
  const [loadError, setLoadError] = useState(null)

  useEffect(() => {
    Promise.all([api.getEntity(id), api.listSources(), api.exportEntityJson(id)])
      .then(([e, srcs, exp]) => {
        setEntity(e)
        setSources(srcs)
        setEntityExport(exp)
      })
      .catch((err) => setLoadError(err.message || 'Сервертэй холбогдож чадсангүй'))
  }, [id])

  // AI-ийн JSON доторх экранлаагүй хашилтуудыг мөр мөрөөр засна.
  function autoFixJson(text) {
    const textFields = [
      'fact', 'source_quote', 'reason', 'new_fact_quote',
      'contradicted_fact_id', 'role_context', 'fact_id',
      'target_name', 'rel_type', 'target_kind',
    ]
    const fieldRe = new RegExp(
      `^(\\s*"(?:${textFields.join('|')})"\\s*:\\s*)"(.*)"(,?)\\s*$`
    )

    return text
      .split('\n')
      .map((line) => {
        const m = line.match(fieldRe)
        if (!m) return line
        const [, prefix, value, comma] = m
        const fixedValue = value.replace(/\\"/g, '\x00').replace(/"/g, '\\"').replace(/\x00/g, '\\"')
        return `${prefix}"${fixedValue}"${comma}`
      })
      .join('\n')
  }

  function validateJson(text) {
    try {
      const parsed = JSON.parse(text)
      setParseError(null)
      return parsed
    } catch (_) { /* autoFix-ээр дахин оролдоно */ }

    try {
      const fixed = autoFixJson(text)
      const parsed = JSON.parse(fixed)
      setParseError(null)
      setJsonInput(fixed)
      return parsed
    } catch (e) {
      setParseError('JSON буруу бичигдсэн байна: ' + e.message)
      return null
    }
  }

  async function handleGeneratePrompt() {
    if (!entityExport || !selectedSourceId) {
      alert('Эх сурвалж сонгоно уу.')
      return
    }
    const sourceData = await api.getSource(selectedSourceId)
    const prompt = MASTER_PROMPT_TEMPLATE(entityExport, sourceData.selected_text)
    setPromptText(prompt)
    setShowPrompt(true)
    setPromptCopied(false)
  }

  async function handleCopyPrompt() {
    if (!promptText) {
      await handleGeneratePrompt()
      return
    }
    await navigator.clipboard.writeText(promptText)
    setPromptCopied(true)
    setTimeout(() => setPromptCopied(false), 3000)
  }

  async function handleSubmit() {
    const parsed = validateJson(jsonInput)
    if (!parsed) return

    setSubmitting(true)
    try {
      const payload = {
        ...parsed,
        article_id: selectedSourceId ? Number(selectedSourceId) : null,
      }
      const res = await api.importFacts(id, payload)
      setResult(res)
    } catch (e) {
      alert('Алдаа: ' + e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loadError)
    return (
      <GlassCard className="border-danger/40 p-6 text-center">
        <p className="text-danger font-semibold mb-1">⚠ Хуудас ачаалагдсангүй</p>
        <p className="text-danger/70 text-sm">{loadError}</p>
        <p className="text-faint text-xs mt-2">Backend ажиллаж байгаа эсэхийг шалгана уу (port 8020)</p>
      </GlassCard>
    )
  if (!entity) return <Spinner />

  return (
    <div>
      <div className="mb-6">
        <Link to={`/entities/${id}`} className="text-sm text-accent/80 hover:text-accent hover:underline mb-2 inline-block">
          ← {entity.name}
        </Link>
        <h1 className="font-display text-2xl font-bold text-text">Факт нэмэх</h1>
        <p className="text-sm text-faint mt-1">AI-д промпт өгч хариуг энд paste хийнэ үү.</p>
      </div>

      {/* Ажиллах дараалал */}
      <GlassCard className="p-4 mb-6 text-sm text-dim">
        <p className="font-semibold text-text mb-2">Ажиллах дараалал:</p>
        <ol className="list-decimal list-inside space-y-1.5">
          <li>Эх сурвалж сонгоно</li>
          <li>
            <span className="font-medium text-text">Промпт хуулах</span> — профайлын одоогийн мэдээлэл + текст хамт хуулагдана
          </li>
          <li>Gemini / ChatGPT / Claude-д paste хийнэ</li>
          <li>AI-ийн буцаасан JSON-г доорх талбарт paste хийнэ</li>
          <li>
            <span className="font-medium text-text">Фактуудыг хадгалах</span> — давхардалгүй фактууд профайлд нэмэгдэнэ
          </li>
        </ol>
      </GlassCard>

      {/* Алхам 1 */}
      <GlassCard className="p-5 mb-4">
        <h2 className="font-semibold text-text mb-1 flex items-center gap-2">
          <StepBadge n={1} />
          Эх сурвалж сонгох
          <span className="text-xs text-faint font-normal">(заавал биш)</span>
        </h2>
        <p className="text-xs text-faint mb-3">
          Сонгосон эх сурвалжийн текст промптод орно.
        </p>
        <Select value={selectedSourceId} onChange={(e) => setSelectedSourceId(e.target.value)}>
          <option value="">— Эх сурвалж сонгоогүй —</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title} {s.publication_date ? `(${s.publication_date})` : ''}
            </option>
          ))}
        </Select>
      </GlassCard>

      {/* Алхам 2 */}
      <GlassCard className="p-5 mb-4">
        <h2 className="font-semibold text-text mb-1 flex items-center gap-2">
          <StepBadge n={2} />
          AI-д өгөх промпт
        </h2>
        <p className="text-xs text-faint mb-3">
          Профайлын бүх мэдээлэл + текст + заавар нэг промпт болж үүснэ.
        </p>
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <Button onClick={handleGeneratePrompt}>⚙ Промпт үүсгэх</Button>
          {promptText && (
            <Button variant={promptCopied ? 'ok' : 'primary'} onClick={handleCopyPrompt}>
              {promptCopied ? '✓ Хуулагдлаа!' : '⎘ Бүгдийг хуулах'}
            </Button>
          )}
          {promptCopied && (
            <span className="text-sm text-ok animate-pulse">→ AI-д Ctrl+V дарна уу</span>
          )}
        </div>

        {showPrompt && promptText && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-faint">Промптын агуулга:</span>
              <button onClick={() => setShowPrompt(false)} className="text-xs text-faint hover:text-dim">
                Нуух ↑
              </button>
            </div>
            <TextArea
              readOnly
              value={promptText}
              rows={14}
              onClick={(e) => e.target.select()}
              className="text-xs font-mono"
            />
            <p className="text-xs text-faint mt-1">Дотор нь нэг дарахад бүгд сонгогдоно → Ctrl+C</p>
          </div>
        )}
      </GlassCard>

      {/* Алхам 3 */}
      <GlassCard className="p-5 mb-5">
        <h2 className="font-semibold text-text mb-1 flex items-center gap-2">
          <StepBadge n={3} />
          AI-ийн JSON хариуг paste хийх
        </h2>
        <p className="text-xs text-faint mb-3">AI-ийн хариуг бүтнээр нь paste хийнэ үү.</p>
        <TextArea
          value={jsonInput}
          onChange={(e) => {
            setJsonInput(e.target.value)
            setParseError(null)
            setResult(null)
          }}
          onBlur={() => jsonInput && validateJson(jsonInput)}
          rows={14}
          placeholder={`{\n  "new_biographical_facts": [],\n  "new_chronological_facts": [],\n  "contradictions_detected": []\n}`}
          className={`text-sm font-mono ${parseError ? 'border-danger/60' : ''}`}
        />
        {parseError && <p className="text-danger text-xs mt-1">⚠ {parseError}</p>}
      </GlassCard>

      {/* Үр дүн */}
      {result && (
        <GlassCard className="border-ok/40 p-4 mb-5">
          <p className="text-ok font-semibold text-sm">✓ Амжилттай!</p>
          <p className="text-text/80 text-sm mt-1">
            {result.added_facts} факт нэмэгдлээ.{' '}
            {result.added_relationships > 0 && <span>{result.added_relationships} холбоос нэмэгдлээ. </span>}
            {result.skipped_duplicates > 0 && (
              <span className="text-faint">{result.skipped_duplicates} давхардал алгасав. </span>
            )}
            {result.contradictions_saved > 0 && `${result.contradictions_saved} зөрчил бүртгэгдлээ.`}
          </p>
          {result.skipped_contradictions.length > 0 && (
            <p className="text-accent text-xs mt-1">
              Алгассан зөрчил: {result.skipped_contradictions.join(', ')}
            </p>
          )}
          <Link to={`/entities/${id}`} className="text-accent hover:underline text-sm mt-2 inline-block">
            Профайл харах →
          </Link>
        </GlassCard>
      )}

      <Button variant="primary" onClick={handleSubmit} disabled={submitting || !jsonInput.trim()}>
        {submitting ? 'Хадгалж байна…' : '✓ Фактуудыг хадгалах'}
      </Button>
    </div>
  )
}
