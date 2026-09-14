/**
 * Фактын source_quote-уудыг нийтлэлийн текст дотор тодруулж HTML болгоно.
 * АНХААР: Энэ логик нь ArticleView.jsx-ээс үг үсэггүй зөөгдсөн — exact substring
 * matching дээр тулгуурладаг тул өөрчлөхөөс болгоомжил.
 */
export function buildAnnotatedHtml(text, facts) {
  if (!text || !facts.length) return text

  const anchored = facts
    .filter((f) => f.source_quote && text.includes(f.source_quote))
    .sort((a, b) => b.source_quote.length - a.source_quote.length)

  const replacements = []
  let workingText = text

  for (const fact of anchored) {
    const idx = workingText.indexOf(fact.source_quote)
    if (idx === -1) continue
    const cls = fact.has_contradiction ? 'fact-highlight contradiction' : 'fact-highlight'
    const tooltip = fact.has_contradiction
      ? `⚠️ Зөрчил илэрсэн\n${fact.fact_text}`
      : fact.fact_text
    const html = `<span class="${cls}" data-fact-id="${fact.id}"><span class="fact-tooltip">${tooltip}\n📅 ${fact.fact_date || '—'}</span>${fact.source_quote}</span>`
    replacements.push({ idx, len: fact.source_quote.length, html })
    workingText = workingText.slice(0, idx) + '\x01'.repeat(fact.source_quote.length) + workingText.slice(idx + fact.source_quote.length)
  }

  let result = text
  for (const { idx, len, html } of [...replacements].sort((a, b) => b.idx - a.idx)) {
    result = result.slice(0, idx) + html + result.slice(idx + len)
  }
  return result
}
