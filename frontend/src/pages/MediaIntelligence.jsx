import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { 
  Radio, ShieldAlert, AlertTriangle, EyeOff, Sparkles, 
  ExternalLink, BarChart2, TrendingUp, TrendingDown,
  FileText, CheckCircle2, ChevronRight, HelpCircle
} from 'lucide-react'
import GlassCard from '../components/ui/GlassCard'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

export default function MediaIntelligence() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [filterMode, setFilterMode] = useState('all') // 'all' | 'suspicious' | 'blackout'

  useEffect(() => {
    setLoading(true)
    api.getMediaIntelligence()
      .then((res) => {
        setData(res)
        if (res.media_profiles && res.media_profiles.length > 0) {
          setSelectedDomain(res.media_profiles[0])
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="py-32 flex justify-center">
        <Spinner />
      </div>
    )
  }

  if (error || !data) {
    return (
      <GlassCard className="p-6 text-danger font-mono">
        <p className="font-bold flex items-center gap-2">
          <AlertTriangle size={18} /> Хэвлэлийн мониторинг ачааллахад алдаа гарлаа:
        </p>
        <p className="mt-1 text-sm">{error || 'Өгөгдөл олдсонгүй'}</p>
      </GlassCard>
    )
  }

  const { total_monitored_domains, media_profiles, case_coverage } = data

  // Шүүлт
  const filteredProfiles = media_profiles.filter((p) => {
    if (filterMode === 'suspicious') return p.suspicious_contracts.length > 0
    if (filterMode === 'blackout') return p.blackout_cases_count > 0
    return true
  })

  return (
    <div className="space-y-6">
      {/* Толгой хэсэг */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Radio size={22} className="text-accent animate-pulse" />
            <h1 className="font-display text-2xl font-bold text-text tracking-wide">
              Media Intelligence & Хаалтын Гэрээ Илрүүлэгч
            </h1>
          </div>
          <p className="text-sm text-dim mt-1 max-w-3xl leading-relaxed">
            Хэвлэлүүд хэнийг магтаж, хэнийг шүүмжилж байна вэ? Хэрэг дэлбэрэхэд огт мэдээлээгүй өнгөрсөн 
            <span className="text-rose-400 font-bold"> «Мэдээллийн дүлий бүс»</span> болон улс төрчидтэй байгуулсан 
            байж болзошгүй <span className="text-amber-400 font-bold">«Хаалтын гэрээ»</span>-ний магадлалыг тооцоолсон шинжилгээ.
          </p>
        </div>
        <Link
          to="/sources"
          className="px-3.5 py-2 rounded-lg text-xs font-mono bg-surface-2 border border-line text-text hover:border-accent hover:text-accent transition-all flex items-center gap-2 self-start shrink-0 shadow-sm"
        >
          <FileText size={15} />
          <span>Бүх Эх Сурвалж & Нийтлэлүүд →</span>
        </Link>
      </div>

      {/* Тоон статистикийн хураангуй */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <GlassCard className="p-4">
          <div className="text-xs text-dim font-mono">ХЯНАЛТАД БУЙ ЭХ СУРВАЛЖ</div>
          <div className="text-2xl font-bold font-mono text-text mt-1">{total_monitored_domains} домэйн</div>
          <div className="text-[11px] text-faint mt-0.5">Вэбсайт, агентлаг, албан сонин</div>
        </GlassCard>

        <GlassCard className="p-4 border-amber-500/30 bg-amber-500/5">
          <div className="text-xs text-amber-400 font-mono flex items-center gap-1.5">
            <ShieldAlert size={14} /> СЭЖИГТЭЙ ХААЛТЫН ГЭРЭЭ
          </div>
          <div className="text-2xl font-bold font-mono text-amber-300 mt-1">
            {media_profiles.filter((p) => p.suspicious_contracts.length > 0).length} эх сурвалж
          </div>
          <div className="text-[11px] text-amber-400/70 mt-0.5">Магтаал өндөр + Хэргийг нуусан</div>
        </GlassCard>

        <GlassCard className="p-4 border-rose-500/30 bg-rose-500/5">
          <div className="text-xs text-rose-400 font-mono flex items-center gap-1.5">
            <EyeOff size={14} /> ДҮЛИЙ БҮС БҮХИЙ ХЭРГҮҮД
          </div>
          <div className="text-2xl font-bold font-mono text-rose-300 mt-1">
            {case_coverage.filter((c) => c.silent_media_count > 0).length} дуулиан
          </div>
          <div className="text-[11px] text-rose-400/70 mt-0.5">Зарим хэвлэлүүд 0 дурдсан</div>
        </GlassCard>

        <GlassCard className="p-4">
          <div className="text-xs text-dim font-mono">ШИНЖИЛСЭН БАРИМТ</div>
          <div className="text-2xl font-bold font-mono text-accent mt-1">
            {media_profiles.reduce((acc, p) => acc + p.facts_count, 0)} факт
          </div>
          <div className="text-[11px] text-faint mt-0.5">Мэдрэмж + хамаарлын үнэлгээтэй</div>
        </GlassCard>
      </div>

      {/* Гол агуулга: 2 Багана (Зүүн: Хэвлэлийн жагсаалт & Шүүлт, Баруун: Нарийвчилсан Досье) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Зүүн багана: Эх сурвалжуудын радарын жагсаалт (5 багана) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between pb-1 border-b border-line/60">
            <span className="terminal-label">Хэвлэл мэдээллийн эх сурвалжууд</span>
            <div className="flex items-center gap-1">
              {[
                { id: 'all', label: 'Бүгд' },
                { id: 'suspicious', label: '⚠️ Сэжигтэй' },
                { id: 'blackout', label: 'Дүлий бүс' },
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => setFilterMode(m.id)}
                  className={`px-2 py-0.5 text-[11px] font-mono rounded transition ${
                    filterMode === m.id
                      ? 'bg-accent text-ink-950 font-bold'
                      : 'text-dim hover:text-text hover:bg-surface-2'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2 max-h-[750px] overflow-y-auto pr-1">
            {filteredProfiles.map((p) => {
              const isSelected = selectedDomain?.domain === p.domain
              const hasRisk = p.suspicious_contracts.length > 0
              return (
                <button
                  key={p.domain}
                  onClick={() => setSelectedDomain(p)}
                  className={`w-full text-left p-3 rounded-lg border transition-all cursor-pointer flex flex-col gap-1.5 ${
                    isSelected
                      ? 'bg-accent/15 border-accent-line shadow-[0_0_15px_rgb(56_224_255/0.15)]'
                      : hasRisk
                      ? 'bg-surface border-amber-500/40 hover:border-amber-500 hover:bg-surface-2'
                      : 'bg-surface border-line hover:border-line-bright hover:bg-surface-2'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-text truncate max-w-[220px]">
                      {p.domain}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {hasRisk && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1">
                          <AlertTriangle size={10} /> Гэрээний эрсдэл
                        </span>
                      )}
                      <span className="data-label text-[10px]">
                        {p.facts_count} факт
                      </span>
                    </div>
                  </div>

                  {/* Мэдрэмжийн индикатор */}
                  <div className="flex items-center justify-between text-xs font-mono text-dim pt-1 border-t border-line/40">
                    <span className="flex items-center gap-1">
                      Хандлага:
                      <span className={p.average_sentiment > 0 ? 'text-ok font-bold' : p.average_sentiment < 0 ? 'text-rose-400 font-bold' : 'text-dim'}>
                        {p.average_sentiment > 0 ? `+${p.average_sentiment}` : p.average_sentiment}
                      </span>
                    </span>
                    <span className="text-[11px] text-faint">
                      Дүлий хэргүүд: <b className={p.blackout_cases_count > 0 ? 'text-rose-300' : 'text-faint'}>{p.blackout_cases_count}</b>
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Баруун багана: Сонгогдсон хэвлэлийн нарийвчилсан Досье (7 багана) */}
        <div className="lg:col-span-7">
          {selectedDomain ? (
            <GlassCard className="p-6 space-y-6">
              {/* Домэйн гарчиг */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-line">
                <div>
                  <div className="terminal-label">Хэвлэлийн дүн шинжилгээний Досье</div>
                  <h2 className="text-xl font-bold font-mono text-text flex items-center gap-2 mt-1">
                    {selectedDomain.domain}
                  </h2>
                  <div className="flex gap-2 mt-1.5 flex-wrap">
                    {selectedDomain.primary_categories.map((cat, i) => (
                      <Badge key={i} tone="neutral">{cat}</Badge>
                    ))}
                    <Badge tone="accent">{selectedDomain.sources_count} нийтлэл/эх сурвалж</Badge>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs font-mono text-dim">Дундаж хандлага (Sentiment)</div>
                  <div className={`text-2xl font-bold font-mono mt-0.5 ${
                    selectedDomain.average_sentiment > 0 ? 'text-ok' : selectedDomain.average_sentiment < 0 ? 'text-rose-400' : 'text-dim'
                  }`}>
                    {selectedDomain.average_sentiment > 0 ? `+${selectedDomain.average_sentiment}` : selectedDomain.average_sentiment}
                  </div>
                </div>
              </div>

              {/* 1. Сэжигтэй Хаалтын Гэрээний анхааруулга (Muted Contracts Risk) */}
              {selectedDomain.suspicious_contracts.length > 0 ? (
                <div className="p-4 rounded-lg border border-amber-500/50 bg-amber-500/10 space-y-3">
                  <div className="flex items-center gap-2 text-amber-400 font-bold font-mono text-sm">
                    <ShieldAlert size={16} />
                    <span>«ХААЛТЫН ГЭРЭЭ»-НИЙ СЭЖИГТЭЙ СХЕМ ИЛЭРСЭН</span>
                  </div>
                  <p className="text-xs text-amber-200/90 leading-relaxed font-mono">
                    Энэ сайт нь дараах улс төрчдийг эерэгээр бичдэг атлаа тэдгээрийн шууд холбогдсон авлига, хулгайн томоохон хэргүүдийн талаар 
                    <b className="text-rose-300"> 0 дурдалттай (Blackout)</b> өнгөрсөн байна:
                  </p>
                  <div className="space-y-2 mt-2">
                    {selectedDomain.suspicious_contracts.map((sc, i) => (
                      <div key={i} className="p-3 bg-surface-1/80 border border-amber-500/30 rounded-md">
                        <div className="flex items-center justify-between">
                          <Link to={`/entities/${sc.entity_id}`} className="font-bold text-text text-sm hover:text-accent flex items-center gap-1">
                            {sc.entity_name} <ExternalLink size={12} />
                          </Link>
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                            Эрсдэлийн магадлал: {sc.contract_probability_pct}%
                          </span>
                        </div>
                        <div className="mt-2 text-[11px] font-mono text-dim">
                          Огт мэдээлээгүй хэргүүд:
                          <div className="flex flex-wrap gap-1.5 mt-1">
                            {sc.muted_cases.map((mc, j) => (
                              <span key={j} className="px-1.5 py-0.5 rounded bg-rose-500/15 border border-rose-500/30 text-rose-300">
                                ✕ {mc}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded-lg border border-ok/30 bg-ok/5 flex items-center gap-2 text-xs font-mono text-ok">
                  <CheckCircle2 size={16} />
                  <span>Тус сайт дээр илэрхий хаалтын гэрээний хазайлтын сэжиг бүртгэгдээгүй байна.</span>
                </div>
              )}

              {/* 2. Магтсан vs Шүүмжилсэн субъектүүд (Asymmetry Tracker) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Магтсан */}
                <div className="p-3.5 rounded-lg border border-line bg-surface space-y-2">
                  <div className="text-xs font-mono font-bold text-ok flex items-center gap-1.5">
                    <TrendingUp size={14} /> ХАМГИЙН ЭЕРЭГ ДУРДСАН
                  </div>
                  {selectedDomain.favored_entities.length > 0 ? (
                    <div className="space-y-1.5">
                      {selectedDomain.favored_entities.map((e, i) => (
                        <div key={i} className="flex items-center justify-between text-xs font-mono p-1.5 rounded bg-surface-2">
                          <Link to={`/entities/${e.entity_id}`} className="text-text hover:text-accent truncate max-w-[180px]">
                            {e.name}
                          </Link>
                          <span className="text-ok font-bold">+{e.sentiment_avg}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs font-mono text-faint py-3 text-center">Илэрхий магтсан тэмдэглэгээгүй</div>
                  )}
                </div>

                {/* Шүүмжилсэн */}
                <div className="p-3.5 rounded-lg border border-line bg-surface space-y-2">
                  <div className="text-xs font-mono font-bold text-rose-400 flex items-center gap-1.5">
                    <TrendingDown size={14} /> ХАМГИЙН СӨРӨГ ДУРДСАН
                  </div>
                  {selectedDomain.criticized_entities.length > 0 ? (
                    <div className="space-y-1.5">
                      {selectedDomain.criticized_entities.map((e, i) => (
                        <div key={i} className="flex items-center justify-between text-xs font-mono p-1.5 rounded bg-surface-2">
                          <Link to={`/entities/${e.entity_id}`} className="text-text hover:text-accent truncate max-w-[180px]">
                            {e.name}
                          </Link>
                          <span className="text-rose-400 font-bold">{e.sentiment_avg}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs font-mono text-faint py-3 text-center">Шүүмжилсэн бичвэр цөөн</div>
                  )}
                </div>
              </div>

              {/* 3. Мэдээллийн дүлий бүс (Огт дурдаагүй хэргүүдийн жагсаалт) */}
              <div className="space-y-2 pt-2 border-t border-line">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-text flex items-center gap-1.5">
                    <EyeOff size={14} className="text-rose-400" />
                    Энэ сайт дээр огт мэдээлэгдээгүй дуулиант хэргүүд (Blackout Cases)
                  </span>
                  <span className="data-label text-[10px]">
                    Нийт {selectedDomain.blackout_cases_count} хэрэг
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {selectedDomain.blackout_cases.map((bc, i) => (
                    <Link
                      key={i}
                      to={`/cases/${bc.slug}`}
                      className="p-2.5 rounded border border-line/60 bg-surface-2/40 hover:border-accent hover:bg-surface-2 text-xs font-mono flex items-center justify-between transition group"
                    >
                      <span className="truncate pr-2 text-dim group-hover:text-text">{bc.title}</span>
                      <ChevronRight size={13} className="text-faint group-hover:text-accent shrink-0" />
                    </Link>
                  ))}
                </div>
              </div>

            </GlassCard>
          ) : (
            <div className="h-full flex items-center justify-center p-12 text-center text-dim font-mono border border-dashed border-line rounded-lg">
              Зүүн талын жагсаалтаас хэвлэлийн эх сурвалжийг сонгож дүн шинжилгээг харна уу
            </div>
          )}
        </div>

      </div>

      {/* Томоохон хэргүүд дээрх хэвлэлүүдийн хамрах хүрээ (Coverage Matrix) */}
      <GlassCard className="p-6 space-y-4">
        <div className="flex items-center gap-2">
          <BarChart2 size={18} className="text-accent" />
          <h2 className="font-display text-lg font-bold text-text">
            Хэргүүдийн Хэвлэл Дэх Хамрах Хүрээ (Media Coverage Matrix)
          </h2>
        </div>
        <p className="text-xs text-dim font-mono">
          Томоохон хэрэг бүрийг хэдэн сайт бичиж, ямар хэвлэлүүд чимээгүй өнгөрснийг харуулсан нэгдсэн хяналтын самбар.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-line text-dim">
                <th className="py-2.5 px-3">Мөрдлөгийн хэрэг</th>
                <th className="py-2.5 px-3">Мэдээлсэн хэвлэл</th>
                <th className="py-2.5 px-3">Чимээгүй өнгөрсөн хэвлэлүүд (Дүлий бүс)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/40">
              {case_coverage.slice(0, 10).map((c) => (
                <tr key={c.case_id} className="hover:bg-surface-2/60 transition">
                  <td className="py-3 px-3">
                    <Link to={`/cases/${c.slug}`} className="font-bold text-text hover:text-accent flex items-center gap-1.5">
                      {c.title} <ExternalLink size={11} className="text-faint" />
                    </Link>
                    <span className="data-label text-[10px] block mt-0.5">{c.category}</span>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className="px-2 py-1 rounded bg-ok/15 text-ok font-bold border border-ok/30">
                      {c.reported_media_count} сайт мэдээлсэн
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex flex-wrap gap-1.5">
                      {c.silent_domains.map((sd, j) => (
                        <span key={j} className="px-1.5 py-0.5 rounded bg-surface-2 text-faint text-[10px] border border-line">
                          {sd}
                        </span>
                      ))}
                      {c.silent_media_count > 8 && (
                        <span className="text-[10px] text-dim self-center">+{c.silent_media_count - 8} бусад</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  )
}
