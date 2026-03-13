const API_BASE = '/api/v1'

// Read API key from localStorage (set on login/settings screen)
function getApiKey(): string {
  return localStorage.getItem('cati_api_key') || ''
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  const apiKey = getApiKey()
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      detail = JSON.parse(text)?.detail ?? text
    } catch {
      // use raw text
    }
    throw new Error(detail || `HTTP ${res.status}`)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

// ── Surveys ────────────────────────────────────────────────────────────────────

import type {
  Survey, SurveyCreate, Question, QuestionCreate, SkipRule,
  Contact, ContactCreate,
  Call, CallInitiate, CallBatch, BatchCreate,
  Response, TranscriptTurn, SurveyStats,
  AnalysisReport,
  Export, ExportCreate,
} from './types'

export const surveys = {
  list: () => request<Survey[]>('/surveys'),
  get: (id: number) => request<Survey>(`/surveys/${id}`),
  create: (data: SurveyCreate) =>
    request<Survey>('/surveys', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<SurveyCreate>) =>
    request<Survey>(`/surveys/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<void>(`/surveys/${id}`, { method: 'DELETE' }),
  activate: (id: number) =>
    request<Survey>(`/surveys/${id}/activate`, { method: 'POST' }),
  addQuestion: (surveyId: number, data: QuestionCreate) =>
    request<Question>(`/surveys/${surveyId}/questions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateQuestion: (surveyId: number, qid: number, data: Partial<QuestionCreate>) =>
    request<Question>(`/surveys/${surveyId}/questions/${qid}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteQuestion: (surveyId: number, qid: number) =>
    request<void>(`/surveys/${surveyId}/questions/${qid}`, { method: 'DELETE' }),
  addSkipRule: (
    surveyId: number,
    data: { source_question_id: number; target_question_id: number; condition_expr: string; priority?: number },
  ) =>
    request<SkipRule>(`/surveys/${surveyId}/skip-rules`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

// ── Contacts ───────────────────────────────────────────────────────────────────

export const contacts = {
  list: (params?: { dnc_only?: boolean; page?: number; page_size?: number }) => {
    const qs = new URLSearchParams()
    if (params?.dnc_only) qs.set('dnc_only', 'true')
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    const q = qs.toString()
    return request<Contact[]>(`/contacts${q ? `?${q}` : ''}`)
  },
  get: (id: number) => request<Contact>(`/contacts/${id}`),
  create: (data: ContactCreate) =>
    request<Contact>('/contacts', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<ContactCreate>) =>
    request<Contact>(`/contacts/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  setDnc: (id: number) =>
    request<Contact>(`/contacts/${id}/do-not-call`, { method: 'POST' }),
  clearDnc: (id: number) =>
    request<Contact>(`/contacts/${id}/do-not-call`, { method: 'DELETE' }),
  checkDnc: (phone_number: string) =>
    request<{ phone_number: string; is_dnc: boolean }>('/contacts/check-dnc', {
      method: 'POST',
      body: JSON.stringify({ phone_number }),
    }),
}

// ── Calls ──────────────────────────────────────────────────────────────────────

export const calls = {
  list: (params?: { survey_id?: number; status?: string; page?: number }) => {
    const qs = new URLSearchParams()
    if (params?.survey_id) qs.set('survey_id', String(params.survey_id))
    if (params?.status) qs.set('status', params.status)
    if (params?.page) qs.set('page', String(params.page))
    const q = qs.toString()
    return request<Call[]>(`/calls${q ? `?${q}` : ''}`)
  },
  get: (id: number) => request<Call>(`/calls/${id}`),
  initiate: (data: CallInitiate) =>
    request<Call>('/calls/initiate', { method: 'POST', body: JSON.stringify(data) }),
  batch: (data: BatchCreate) =>
    request<CallBatch>('/calls/batch', { method: 'POST', body: JSON.stringify(data) }),
  getBatch: (id: number) => request<CallBatch>(`/batches/${id}`),
  pauseBatch: (id: number) =>
    request<CallBatch>(`/batches/${id}/pause`, { method: 'POST' }),
  resumeBatch: (id: number) =>
    request<CallBatch>(`/batches/${id}/resume`, { method: 'POST' }),
}

// ── Responses ──────────────────────────────────────────────────────────────────

export const responses = {
  forCall: (callId: number) => request<Response[]>(`/calls/${callId}/responses`),
  transcript: (callId: number) => request<TranscriptTurn[]>(`/calls/${callId}/transcript`),
  forSurvey: (surveyId: number) => request<Response[]>(`/surveys/${surveyId}/responses`),
  stats: (surveyId: number) => request<SurveyStats>(`/surveys/${surveyId}/stats`),
}

// ── Analysis ───────────────────────────────────────────────────────────────────

export const analysis = {
  triggerCall: (callId: number) =>
    request<AnalysisReport>(`/analysis/calls/${callId}`, { method: 'POST' }),
  getCall: (callId: number) => request<AnalysisReport>(`/analysis/calls/${callId}`),
  triggerSurvey: (surveyId: number) =>
    request<AnalysisReport>(`/analysis/surveys/${surveyId}`, { method: 'POST' }),
  getSurvey: (surveyId: number) => request<AnalysisReport>(`/analysis/surveys/${surveyId}`),
}

// ── Exports ────────────────────────────────────────────────────────────────────

export const exports_ = {
  list: () => request<Export[]>('/exports'),
  create: (data: ExportCreate) =>
    request<Export>('/exports', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: number) => request<Export>(`/exports/${id}`),
  downloadUrl: (id: number) => `${API_BASE}/exports/${id}/download`,
}

// ── Health ─────────────────────────────────────────────────────────────────────

export const health = {
  check: () => request<{ status: string; version: string }>('/health'),
}
