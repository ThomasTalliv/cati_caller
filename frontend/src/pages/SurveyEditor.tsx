import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, ArrowLeft, Save } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import { surveys } from '../api/client'
import type { QuestionCreate, QuestionType } from '../api/types'

const QUESTION_TYPES: { value: QuestionType; label: string }[] = [
  { value: 'yes_no', label: 'Yes / No' },
  { value: 'single_choice', label: 'Single Choice' },
  { value: 'numeric', label: 'Numeric' },
  { value: 'rating_scale', label: 'Rating Scale' },
  { value: 'open_ended', label: 'Open Ended' },
]

interface QuestionForm extends QuestionCreate {
  _id: string // local key
}

function makeQuestion(): QuestionForm {
  return {
    _id: Math.random().toString(36).slice(2),
    question_key: '',
    question_type: 'yes_no',
    text: '',
    required: true,
    max_retries: 2,
    position: 0,
  }
}

export default function SurveyEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const isEdit = Boolean(id)

  const { data: existing, isLoading } = useQuery({
    queryKey: ['survey', id],
    queryFn: () => surveys.get(Number(id)),
    enabled: isEdit,
  })

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [language, setLanguage] = useState('en')
  const [introText, setIntroText] = useState('')
  const [outroText, setOutroText] = useState('')
  const [questions, setQuestions] = useState<QuestionForm[]>([makeQuestion()])
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (existing) {
      setName(existing.name)
      setDescription(existing.description ?? '')
      setLanguage(existing.language)
      setIntroText(existing.intro_text ?? '')
      setOutroText(existing.outro_text ?? '')
      setQuestions(
        existing.questions.map((q) => ({
          _id: String(q.id),
          question_key: q.question_key,
          question_type: q.question_type,
          text: q.text,
          rephrased_text: q.rephrased_text,
          options: q.options,
          validation: q.validation,
          required: q.required,
          max_retries: q.max_retries,
          position: q.position,
        })),
      )
    }
  }, [existing])

  const addQuestion = () => setQuestions((qs) => [...qs, { ...makeQuestion(), position: qs.length }])
  const removeQuestion = (idx: number) => setQuestions((qs) => qs.filter((_, i) => i !== idx))
  const updateQuestion = (idx: number, patch: Partial<QuestionForm>) =>
    setQuestions((qs) => qs.map((q, i) => (i === idx ? { ...q, ...patch } : q)))

  const handleSave = async () => {
    setError('')
    setSaving(true)
    try {
      const payload = {
        name,
        description,
        language,
        intro_text: introText,
        outro_text: outroText,
        questions: questions.map((q, i) => ({
          question_key: q.question_key,
          question_type: q.question_type,
          text: q.text,
          rephrased_text: q.rephrased_text,
          options: q.options,
          validation: q.validation,
          required: q.required ?? true,
          max_retries: q.max_retries ?? 2,
          position: i,
        })),
      }

      if (isEdit) {
        await surveys.update(Number(id), payload)
      } else {
        await surveys.create(payload)
      }
      await qc.invalidateQueries({ queryKey: ['surveys'] })
      navigate('/surveys')
    } catch (err) {
      setError(String(err))
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size={32} />
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={isEdit ? 'Edit Survey' : 'New Survey'}
        action={
          <button
            onClick={() => navigate('/surveys')}
            className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft size={16} />
            Back
          </button>
        }
      />
      <div className="p-6 max-w-3xl space-y-6">
        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded px-4 py-3">{error}</div>
        )}

        {/* Basic info */}
        <section className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <h2 className="font-medium text-gray-900">Survey Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Survey name"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Language</label>
              <select
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {['en', 'da', 'de', 'fr', 'es', 'pt', 'it', 'nl'].map((l) => (
                  <option key={l} value={l}>{l.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Intro Text (TTS)</label>
              <textarea
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                rows={2}
                value={introText}
                onChange={(e) => setIntroText(e.target.value)}
                placeholder="What the caller says at the beginning"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Outro Text (TTS)</label>
              <textarea
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                rows={2}
                value={outroText}
                onChange={(e) => setOutroText(e.target.value)}
                placeholder="What the caller says at the end"
              />
            </div>
          </div>
        </section>

        {/* Questions */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-medium text-gray-900">Questions</h2>
            <button
              onClick={addQuestion}
              className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700"
            >
              <Plus size={15} /> Add Question
            </button>
          </div>

          {questions.map((q, idx) => (
            <div key={q._id} className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Question {idx + 1}
                </span>
                <button
                  onClick={() => removeQuestion(idx)}
                  className="p-1 text-gray-300 hover:text-red-500"
                  disabled={questions.length === 1}
                >
                  <Trash2 size={14} />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Key *</label>
                  <input
                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
                    value={q.question_key}
                    onChange={(e) => updateQuestion(idx, { question_key: e.target.value })}
                    placeholder="e.g. q1_age"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Type</label>
                  <select
                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
                    value={q.question_type}
                    onChange={(e) =>
                      updateQuestion(idx, { question_type: e.target.value as QuestionType })
                    }
                  >
                    {QUESTION_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Question Text *</label>
                  <textarea
                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
                    rows={2}
                    value={q.text}
                    onChange={(e) => updateQuestion(idx, { text: e.target.value })}
                    placeholder="The question the caller will speak"
                  />
                </div>
                {q.question_type === 'single_choice' && (
                  <div className="col-span-2">
                    <label className="block text-xs text-gray-500 mb-1">
                      Options (JSON array, e.g. [{`{"value":"a","label":"Option A"}`}])
                    </label>
                    <textarea
                      className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-brand-500"
                      rows={3}
                      value={q.options ? JSON.stringify(q.options, null, 2) : ''}
                      onChange={(e) => {
                        try {
                          updateQuestion(idx, { options: JSON.parse(e.target.value) })
                        } catch {
                          // ignore parse errors while typing
                        }
                      }}
                    />
                  </div>
                )}
                {(q.question_type === 'numeric' || q.question_type === 'rating_scale') && (
                  <div className="col-span-2 flex gap-3">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Min</label>
                      <input
                        type="number"
                        className="w-24 border border-gray-300 rounded px-2 py-1.5 text-sm"
                        value={q.validation?.min ?? ''}
                        onChange={(e) =>
                          updateQuestion(idx, {
                            validation: { ...q.validation, min: Number(e.target.value) },
                          })
                        }
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Max</label>
                      <input
                        type="number"
                        className="w-24 border border-gray-300 rounded px-2 py-1.5 text-sm"
                        value={q.validation?.max ?? ''}
                        onChange={(e) =>
                          updateQuestion(idx, {
                            validation: { ...q.validation, max: Number(e.target.value) },
                          })
                        }
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">Max Retries</label>
                      <input
                        type="number"
                        min={0}
                        max={5}
                        className="w-20 border border-gray-300 rounded px-2 py-1.5 text-sm"
                        value={q.max_retries}
                        onChange={(e) =>
                          updateQuestion(idx, { max_retries: Number(e.target.value) })
                        }
                      />
                    </div>
                  </div>
                )}
                <div className="col-span-2 flex items-center gap-2">
                  <input
                    type="checkbox"
                    id={`req-${q._id}`}
                    checked={q.required}
                    onChange={(e) => updateQuestion(idx, { required: e.target.checked })}
                    className="h-4 w-4 text-brand-600 rounded border-gray-300"
                  />
                  <label htmlFor={`req-${q._id}`} className="text-sm text-gray-600">
                    Required
                  </label>
                </div>
              </div>
            </div>
          ))}
        </section>

        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-5 py-2.5 rounded-md"
          >
            {saving ? <Spinner size={16} /> : <Save size={16} />}
            {isEdit ? 'Save Changes' : 'Create Survey'}
          </button>
        </div>
      </div>
    </div>
  )
}
