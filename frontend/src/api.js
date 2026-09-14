const BASE = '/api'

async function req(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return null
  return res.json()
}

function qs(params) {
  const clean = Object.fromEntries(
    Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== null && v !== '')
  )
  const s = new URLSearchParams(clean).toString()
  return s ? `?${s}` : ''
}

export const api = {
  // Knowledge graph
  getGraph: () => req('GET', '/graph'),

  // Scrape
  scrape: (url) => req('POST', '/scrape', { url }),

  // Эх сурвалжууд
  createSource: (data) => req('POST', '/sources', data),
  listSources: (params) => req('GET', `/sources${qs(params)}`),
  findSourceByUrl: (url) => req('GET', `/sources${qs({ url })}`),
  getSource: (id) => req('GET', `/sources/${id}`),
  deleteSource: (id) => req('DELETE', `/sources/${id}`),
  verifySource: (id) => req('POST', `/sources/${id}/verify`),

  // Субъектүүд
  listEntities: (params) => req('GET', `/entities${qs(params)}`),
  createEntity: (data) => req('POST', '/entities', data),
  getEntity: (id) => req('GET', `/entities/${id}`),
  updateEntity: (id, data) => req('PATCH', `/entities/${id}`, data),
  deleteEntity: (id) => req('DELETE', `/entities/${id}`),
  mergeEntity: (survivorId, sourceEntityId) =>
    req('POST', `/entities/${survivorId}/merge`, { source_entity_id: sourceEntityId }),
  addAlias: (entityId, alias, kind) => req('POST', `/entities/${entityId}/aliases`, { alias, kind }),
  deleteAlias: (entityId, aliasId) => req('DELETE', `/entities/${entityId}/aliases/${aliasId}`),

  getEntityFacts: (id) => req('GET', `/entities/${id}/facts`),
  clearEntityFacts: (id) => req('DELETE', `/entities/${id}/facts`),
  getEntitySummary: (id) => req('GET', `/entities/${id}/summary`),
  getEntityFlags: (id) => req('GET', `/entities/${id}/flags`),
  getEntityRelationships: (id) => req('GET', `/entities/${id}/relationships`),
  getRelationshipCandidates: (id) => req('GET', `/entities/${id}/relationship-candidates`),
  getIncomingRelationships: (id) => req('GET', `/entities/${id}/relationships-incoming`),
  exportEntityJson: (id) => req('GET', `/entities/${id}/export-json`),
  importFacts: (id, data) => req('POST', `/entities/${id}/import-facts`, data),

  // Фактууд
  createFact: (data) => req('POST', '/facts', data),
  getFact: (id) => req('GET', `/facts/${id}`),
  updateFact: (id, data) => req('PATCH', `/facts/${id}`, data),
  deleteFact: (id) => req('DELETE', `/facts/${id}`),

  // Холбоосууд
  createRelationship: (data) => req('POST', '/relationships', data),
  linkRelationship: (relId, targetEntityId) =>
    req('POST', `/relationships/${relId}/link`, { target_entity_id: targetEntityId }),
  dismissRelationshipLink: (relId, entityId) =>
    req('POST', `/relationships/${relId}/dismiss-link`, { entity_id: entityId }),
  deleteRelationship: (relId) => req('DELETE', `/relationships/${relId}`),

  // Зөрчлүүд
  listContradictions: (params) => req('GET', `/contradictions${qs(params)}`),
  updateContradiction: (id, data) => req('PATCH', `/contradictions/${id}`, data),
}
