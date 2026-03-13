// ── Surveys ────────────────────────────────────────────────────────────────────

export type SurveyStatus = 'draft' | 'active' | 'closed'
export type QuestionType = 'yes_no' | 'single_choice' | 'numeric' | 'rating_scale' | 'open_ended'

export interface QuestionOption {
  value: string | number
  label: string
  spoken_label?: string
}

export interface Validation {
  min?: number
  max?: number
}

export interface Question {
  id: number
  survey_id: number
  question_key: string
  question_type: QuestionType
  text: string
  rephrased_text?: string
  options?: QuestionOption[]
  validation?: Validation
  required: boolean
  max_retries: number
  position: number
}

export interface SkipRule {
  id: number
  survey_id: number
  source_question_id: number
  target_question_id: number
  condition_expr: string
  priority: number
}

export interface Survey {
  id: number
  name: string
  description?: string
  status: SurveyStatus
  language: string
  intro_text?: string
  outro_text?: string
  created_at: string
  updated_at: string
  questions: Question[]
  skip_rules: SkipRule[]
}

export interface SurveyCreate {
  name: string
  description?: string
  language?: string
  intro_text?: string
  outro_text?: string
  questions: Omit<Question, 'id' | 'survey_id'>[]
}

export interface QuestionCreate {
  question_key: string
  question_type: QuestionType
  text: string
  rephrased_text?: string
  options?: QuestionOption[]
  validation?: Validation
  required?: boolean
  max_retries?: number
  position?: number
}

// ── Contacts ───────────────────────────────────────────────────────────────────

export interface Contact {
  id: number
  phone_number: string
  name?: string
  email?: string
  do_not_call: boolean
  metadata?: Record<string, unknown>
  created_at: string
}

export interface ContactCreate {
  phone_number: string
  name?: string
  email?: string
  metadata?: Record<string, unknown>
}

// ── Calls ──────────────────────────────────────────────────────────────────────

export type CallStatus = 'pending' | 'dialing' | 'in_progress' | 'completed' | 'failed' | 'busy' | 'no_answer' | 'cancelled'

export interface Call {
  id: number
  survey_id: number
  contact_id?: number
  batch_id?: number
  status: CallStatus
  phone_number: string
  signalwire_call_id?: string
  duration_s?: number
  attempt_number: number
  created_at: string
  updated_at: string
}

export interface CallInitiate {
  survey_id: number
  phone_number: string
  contact_id?: number
}

export interface BatchCreate {
  survey_id: number
  contact_ids: number[]
  scheduled_at?: string
  max_concurrent?: number
}

export interface CallBatch {
  id: number
  survey_id: number
  status: string
  scheduled_at?: string
  created_at: string
  total_calls: number
  completed_calls: number
  failed_calls: number
}

// ── Responses ──────────────────────────────────────────────────────────────────

export interface Response {
  id: number
  call_id: number
  question_id: number
  question_key: string
  raw_transcript?: string
  parsed_value: unknown
  is_refused: boolean
  confidence: number
  created_at: string
}

export interface TranscriptTurn {
  id: number
  call_id: number
  speaker: 'agent' | 'respondent'
  text: string
  audio_offset_ms?: number
  created_at: string
}

export interface SurveyStats {
  survey_id: number
  total_calls: number
  completed_calls: number
  completion_rate: number
  avg_duration_s: number
  question_stats: Record<string, {
    response_count: number
    refusal_count: number
    avg_confidence: number
    value_distribution?: Record<string, number>
  }>
}

// ── Analysis ───────────────────────────────────────────────────────────────────

export interface AnalysisReport {
  id: number
  call_id?: number
  survey_id?: number
  report_type: string
  llm_provider: string
  content: {
    summary?: string
    overall_sentiment?: string
    per_question_sentiment?: Record<string, string>
    key_themes?: string[]
    completion_quality?: string
    yes_no_distributions?: Record<string, { yes: number; no: number }>
    numeric_stats?: Record<string, { mean: number; std_dev: number; min: number; max: number }>
    thematic_clusters?: Record<string, string[]>
  }
  created_at: string
}

// ── Exports ────────────────────────────────────────────────────────────────────

export type ExportFormat = 'txt' | 'excel' | 'word' | 'gsheets'
export type ExportStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface Export {
  id: number
  survey_id: number
  format: ExportFormat
  status: ExportStatus
  file_path?: string
  external_url?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface ExportCreate {
  survey_id: number
  format: ExportFormat
}

// ── Pagination ─────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
