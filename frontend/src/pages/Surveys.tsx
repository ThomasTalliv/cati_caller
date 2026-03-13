import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Pencil, Trash2, Play } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import { surveys } from '../api/client'

export default function Surveys() {
  const qc = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['surveys'],
    queryFn: surveys.list,
  })

  const deleteMutation = useMutation({
    mutationFn: surveys.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['surveys'] }),
  })

  const activateMutation = useMutation({
    mutationFn: surveys.activate,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['surveys'] }),
  })

  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)

  return (
    <div>
      <PageHeader
        title="Surveys"
        subtitle="Manage your CATI surveys"
        action={
          <Link
            to="/surveys/new"
            className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-3 py-2 rounded-md"
          >
            <Plus size={16} />
            New Survey
          </Link>
        }
      />
      <div className="p-6">
        {isLoading && (
          <div className="flex justify-center py-16">
            <Spinner size={32} />
          </div>
        )}
        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded px-4 py-3">
            {String(error)}
          </div>
        )}
        {data && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Language</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Questions</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Created</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{s.name}</td>
                    <td className="px-4 py-3 text-gray-600 uppercase text-xs">{s.language}</td>
                    <td className="px-4 py-3 text-gray-600">{s.questions.length}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 justify-end">
                        {s.status === 'draft' && (
                          <button
                            onClick={() => activateMutation.mutate(s.id)}
                            className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                            title="Activate"
                          >
                            <Play size={15} />
                          </button>
                        )}
                        <Link
                          to={`/surveys/${s.id}/edit`}
                          className="p-1.5 text-gray-500 hover:bg-gray-100 rounded"
                          title="Edit"
                        >
                          <Pencil size={15} />
                        </Link>
                        {confirmDelete === s.id ? (
                          <span className="flex gap-1 text-xs">
                            <button
                              onClick={() => { deleteMutation.mutate(s.id); setConfirmDelete(null) }}
                              className="px-2 py-0.5 bg-red-600 text-white rounded"
                            >
                              Yes
                            </button>
                            <button
                              onClick={() => setConfirmDelete(null)}
                              className="px-2 py-0.5 bg-gray-200 rounded"
                            >
                              No
                            </button>
                          </span>
                        ) : (
                          <button
                            onClick={() => setConfirmDelete(s.id)}
                            className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                            title="Delete"
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!data.length && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
                      No surveys yet.{' '}
                      <Link to="/surveys/new" className="text-brand-600 underline">
                        Create your first survey
                      </Link>
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
