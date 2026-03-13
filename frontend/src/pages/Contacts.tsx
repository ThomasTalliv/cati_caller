import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Ban, CheckCircle } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import { contacts } from '../api/client'
import type { ContactCreate } from '../api/types'

function AddContactModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState<ContactCreate>({ phone_number: '' })
  const [error, setError] = useState('')
  const mutation = useMutation({
    mutationFn: contacts.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contacts'] })
      onClose()
    },
    onError: (e) => setError(String(e)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Add Contact</h2>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Phone Number (E.164) *</label>
            <input
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.phone_number}
              onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
              placeholder="+12125551234"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
            <input
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.name ?? ''}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
            <input
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.email ?? ''}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded">
            Cancel
          </button>
          <button
            disabled={mutation.isPending}
            onClick={() => mutation.mutate(form)}
            className="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-60"
          >
            {mutation.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Contacts() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [dncOnly, setDncOnly] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', dncOnly],
    queryFn: () => contacts.list({ dnc_only: dncOnly }),
  })

  const dncMutation = useMutation({
    mutationFn: ({ id, set }: { id: number; set: boolean }) =>
      set ? contacts.setDnc(id) : contacts.clearDnc(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  })

  return (
    <div>
      <PageHeader
        title="Contacts"
        subtitle="Manage respondent phone numbers"
        action={
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-3 py-2 rounded-md"
          >
            <Plus size={16} /> Add Contact
          </button>
        }
      />
      {showModal && <AddContactModal onClose={() => setShowModal(false)} />}
      <div className="p-6">
        <div className="mb-4 flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={dncOnly}
              onChange={(e) => setDncOnly(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            Show DNC only
          </label>
        </div>

        {isLoading && (
          <div className="flex justify-center py-16">
            <Spinner size={32} />
          </div>
        )}
        {data && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Phone</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Email</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">DNC</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Added</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-gray-900">{c.phone_number}</td>
                    <td className="px-4 py-3 text-gray-700">{c.name ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-600">{c.email ?? '—'}</td>
                    <td className="px-4 py-3">
                      {c.do_not_call ? (
                        <span className="inline-flex items-center gap-1 text-xs text-red-600 font-medium">
                          <Ban size={12} /> DNC
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => dncMutation.mutate({ id: c.id, set: !c.do_not_call })}
                        className={`p-1.5 rounded text-xs font-medium ${
                          c.do_not_call
                            ? 'text-green-600 hover:bg-green-50'
                            : 'text-red-500 hover:bg-red-50'
                        }`}
                        title={c.do_not_call ? 'Remove from DNC' : 'Add to DNC'}
                      >
                        {c.do_not_call ? <CheckCircle size={15} /> : <Ban size={15} />}
                      </button>
                    </td>
                  </tr>
                ))}
                {!data.length && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
                      No contacts found.
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
