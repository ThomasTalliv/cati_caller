import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, Plus } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import { surveys, exports_ } from '../api/client'
import type { ExportFormat } from '../api/types'

const FORMATS: { value: ExportFormat; label: string }[] = [
  { value: 'excel', label: 'Excel (.xlsx)' },
  { value: 'word', label: 'Word (.docx)' },
  { value: 'txt', label: 'Plain Text (.txt)' },
  { value: 'gsheets', label: 'Google Sheets' },
]

export default function Exports() {
  const qc = useQueryClient()
  const [surveyId, setSurveyId] = useState<number | ''>('')
  const [format, setFormat] = useState<ExportFormat>('excel')
  const [error, setError] = useState('')

  const { data: surveyList } = useQuery({ queryKey: ['surveys'], queryFn: surveys.list })
  const { data: exportList, isLoading } = useQuery({
    queryKey: ['exports'],
    queryFn: exports_.list,
    refetchInterval: 5_000,
  })

  const createMutation = useMutation({
    mutationFn: exports_.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['exports'] })
      setError('')
    },
    onError: (e) => setError(String(e)),
  })

  const handleCreate = () => {
    if (!surveyId) { setError('Please select a survey'); return }
    createMutation.mutate({ survey_id: Number(surveyId), format })
  }

  return (
    <div>
      <PageHeader title="Exports" subtitle="Export survey results in multiple formats" />
      <div className="p-6 space-y-6">
        {/* Create export */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="font-medium text-gray-900 mb-4">Create Export</h2>
          {error && <div className="text-red-600 text-sm mb-3">{error}</div>}
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Survey</label>
              <select
                className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={surveyId}
                onChange={(e) => setSurveyId(e.target.value ? Number(e.target.value) : '')}
              >
                <option value="">— select —</option>
                {surveyList?.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Format</label>
              <select
                className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={format}
                onChange={(e) => setFormat(e.target.value as ExportFormat)}
              >
                {FORMATS.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
            <button
              onClick={handleCreate}
              disabled={createMutation.isPending}
              className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-md"
            >
              {createMutation.isPending ? <Spinner size={16} /> : <Plus size={16} />}
              Create Export
            </button>
          </div>
        </div>

        {/* Export list */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="font-medium text-gray-900">Export History</h2>
          </div>
          {isLoading ? (
            <div className="flex justify-center py-10"><Spinner size={24} /></div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">ID</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Survey</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Format</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Created</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {exportList?.map((e) => (
                  <tr key={e.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-400 text-xs">#{e.id}</td>
                    <td className="px-4 py-3 text-gray-700">#{e.survey_id}</td>
                    <td className="px-4 py-3 text-gray-700 uppercase text-xs font-medium">{e.format}</td>
                    <td className="px-4 py-3"><StatusBadge status={e.status} /></td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(e.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      {e.status === 'completed' && (
                        <a
                          href={exports_.downloadUrl(e.id)}
                          className="flex items-center gap-1 text-brand-600 hover:underline text-xs"
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Download size={13} /> Download
                        </a>
                      )}
                      {e.status === 'failed' && e.error_message && (
                        <span className="text-red-500 text-xs" title={e.error_message}>
                          Failed
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
                {!exportList?.length && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
                      No exports yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
