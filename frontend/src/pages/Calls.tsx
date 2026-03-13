import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Phone } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import { calls, surveys } from '../api/client'
import type { CallInitiate } from '../api/types'

function InitiateCallModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const { data: surveyList } = useQuery({ queryKey: ['surveys'], queryFn: surveys.list })
  const [form, setForm] = useState<CallInitiate>({ survey_id: 0, phone_number: '' })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: calls.initiate,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['calls'] }); onClose() },
    onError: (e) => setError(String(e)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Initiate Call</h2>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Survey *</label>
            <select
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.survey_id || ''}
              onChange={(e) => setForm({ ...form, survey_id: Number(e.target.value) })}
            >
              <option value="">Select survey…</option>
              {surveyList?.filter((s) => s.status === 'active').map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Phone Number *</label>
            <input
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.phone_number}
              onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
              placeholder="+12125551234"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
          <button
            disabled={mutation.isPending || !form.survey_id || !form.phone_number}
            onClick={() => mutation.mutate(form)}
            className="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-60"
          >
            {mutation.isPending ? 'Dialing…' : 'Call'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Calls() {
  const [modal, setModal] = useState<'call' | null>(null)
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['calls', statusFilter],
    queryFn: () => calls.list({ status: statusFilter || undefined }),
    refetchInterval: 10_000,
  })

  return (
    <div>
      <PageHeader
        title="Calls"
        subtitle="Monitor and manage outbound calls"
        action={
          <button
            onClick={() => setModal('call')}
            className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-3 py-2 rounded-md"
          >
            <Phone size={16} /> Initiate Call
          </button>
        }
      />
      {modal === 'call' && <InitiateCallModal onClose={() => setModal(null)} />}
      <div className="p-6">
        <div className="mb-4 flex items-center gap-3">
          <label className="text-sm text-gray-600">Filter by status:</label>
          <select
            className="border border-gray-300 rounded px-2 py-1.5 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All</option>
            {['pending', 'dialing', 'in_progress', 'completed', 'failed', 'busy', 'no_answer', 'cancelled'].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {isLoading && (
          <div className="flex justify-center py-16"><Spinner size={32} /></div>
        )}
        {data && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">ID</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Phone</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Survey</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Duration</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Time</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-400 text-xs">#{c.id}</td>
                    <td className="px-4 py-3 font-mono text-gray-900">{c.phone_number}</td>
                    <td className="px-4 py-3 text-gray-600">#{c.survey_id}</td>
                    <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                    <td className="px-4 py-3 text-gray-600">
                      {c.duration_s != null ? `${c.duration_s}s` : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(c.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/calls/${c.id}`} className="text-brand-600 hover:underline text-xs">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
                {!data.length && (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-gray-400">
                      No calls found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
