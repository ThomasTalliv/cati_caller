import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import { surveys, responses, analysis } from '../api/client'

export default function Results() {
  const [selectedSurvey, setSelectedSurvey] = useState<number | null>(null)

  const { data: surveyList } = useQuery({
    queryKey: ['surveys'],
    queryFn: surveys.list,
  })

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['survey-stats', selectedSurvey],
    queryFn: () => responses.stats(selectedSurvey!),
    enabled: selectedSurvey != null,
  })

  const { data: report, refetch } = useQuery({
    queryKey: ['analysis-survey', selectedSurvey],
    queryFn: () => analysis.getSurvey(selectedSurvey!),
    enabled: selectedSurvey != null,
    retry: false,
  })

  const triggerMutation = useMutation({
    mutationFn: () => analysis.triggerSurvey(selectedSurvey!),
    onSuccess: () => refetch(),
  })

  return (
    <div>
      <PageHeader title="Results" subtitle="Survey response statistics and AI analysis" />
      <div className="p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Survey</label>
          <select
            className="border border-gray-300 rounded px-3 py-2 text-sm w-72 focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={selectedSurvey ?? ''}
            onChange={(e) => setSelectedSurvey(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">— choose —</option>
            {surveyList?.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        {selectedSurvey && (
          <>
            {/* Stats */}
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <h2 className="font-medium text-gray-900 mb-4">Response Statistics</h2>
              {statsLoading ? (
                <Spinner />
              ) : stats ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-2xl font-bold text-gray-900">{stats.total_calls}</div>
                      <div className="text-xs text-gray-500">Total Calls</div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-3">
                      <div className="text-2xl font-bold text-green-700">{stats.completed_calls}</div>
                      <div className="text-xs text-gray-500">Completed</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-3">
                      <div className="text-2xl font-bold text-blue-700">
                        {(stats.completion_rate * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">Completion Rate</div>
                    </div>
                  </div>

                  {/* Per-question stats */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Per Question</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="text-left text-xs text-gray-500">
                            <th className="pb-2">Question Key</th>
                            <th className="pb-2">Responses</th>
                            <th className="pb-2">Refusals</th>
                            <th className="pb-2">Avg Confidence</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {Object.entries(stats.question_stats).map(([key, qs]) => (
                            <tr key={key}>
                              <td className="py-2 font-mono text-gray-700">{key}</td>
                              <td className="py-2 text-gray-900">{qs.response_count}</td>
                              <td className="py-2 text-gray-600">{qs.refusal_count}</td>
                              <td className="py-2 text-gray-600">
                                {(qs.avg_confidence * 100).toFixed(0)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-400">No data available yet.</p>
              )}
            </div>

            {/* Survey-level analysis */}
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-medium text-gray-900">AI Analysis</h2>
                <button
                  onClick={() => triggerMutation.mutate()}
                  disabled={triggerMutation.isPending}
                  className="flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 disabled:opacity-50"
                >
                  <RefreshCw size={14} className={triggerMutation.isPending ? 'animate-spin' : ''} />
                  {report ? 'Re-run Analysis' : 'Run Analysis'}
                </button>
              </div>
              {report ? (
                <div className="space-y-4 text-sm">
                  {report.content.summary && (
                    <div>
                      <div className="text-xs text-gray-500 mb-1 font-medium">Summary</div>
                      <p className="text-gray-800">{report.content.summary}</p>
                    </div>
                  )}
                  {report.content.key_themes?.length ? (
                    <div>
                      <div className="text-xs text-gray-500 mb-1 font-medium">Key Themes</div>
                      <div className="flex flex-wrap gap-1.5">
                        {report.content.key_themes.map((t) => (
                          <span key={t} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {report.content.yes_no_distributions &&
                    Object.keys(report.content.yes_no_distributions).length > 0 && (
                      <div>
                        <div className="text-xs text-gray-500 mb-2 font-medium">Yes/No Distributions</div>
                        <div className="space-y-2">
                          {Object.entries(report.content.yes_no_distributions).map(([key, dist]) => {
                            const total = dist.yes + dist.no
                            const yesPct = total ? Math.round((dist.yes / total) * 100) : 0
                            return (
                              <div key={key}>
                                <div className="flex justify-between text-xs text-gray-600 mb-0.5">
                                  <span className="font-mono">{key}</span>
                                  <span>{yesPct}% yes</span>
                                </div>
                                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-green-500 rounded-full"
                                    style={{ width: `${yesPct}%` }}
                                  />
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                </div>
              ) : (
                <p className="text-sm text-gray-400">No analysis yet.</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
