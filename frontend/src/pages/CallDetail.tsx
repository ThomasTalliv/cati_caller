import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import { calls, responses, analysis } from '../api/client'

export default function CallDetail() {
  const { id } = useParams()
  const callId = Number(id)

  const { data: call } = useQuery({
    queryKey: ['call', callId],
    queryFn: () => calls.get(callId),
  })
  const { data: transcript } = useQuery({
    queryKey: ['transcript', callId],
    queryFn: () => responses.transcript(callId),
  })
  const { data: callResponses } = useQuery({
    queryKey: ['responses', callId],
    queryFn: () => responses.forCall(callId),
  })
  const { data: report, refetch: refetchReport } = useQuery({
    queryKey: ['analysis-call', callId],
    queryFn: () => analysis.getCall(callId),
    retry: false,
  })

  const triggerAnalysis = useMutation({
    mutationFn: () => analysis.triggerCall(callId),
    onSuccess: () => refetchReport(),
  })

  if (!call) {
    return (
      <div className="flex justify-center py-16"><Spinner size={32} /></div>
    )
  }

  return (
    <div>
      <PageHeader
        title={`Call #${callId}`}
        subtitle={call.phone_number}
        action={
          <Link to="/calls" className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900">
            <ArrowLeft size={16} /> Back
          </Link>
        }
      />
      <div className="p-6 space-y-6 max-w-4xl">
        {/* Call info */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-medium text-gray-900 mb-3">Details</h2>
          <dl className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Status</dt>
              <dd className="mt-1"><StatusBadge status={call.status} /></dd>
            </div>
            <div>
              <dt className="text-gray-500">Survey ID</dt>
              <dd className="mt-1 text-gray-900">#{call.survey_id}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Duration</dt>
              <dd className="mt-1 text-gray-900">{call.duration_s != null ? `${call.duration_s}s` : '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Attempt</dt>
              <dd className="mt-1 text-gray-900">#{call.attempt_number}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Created</dt>
              <dd className="mt-1 text-gray-900">{new Date(call.created_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-gray-500">SignalWire ID</dt>
              <dd className="mt-1 text-gray-700 font-mono text-xs truncate">{call.signalwire_call_id ?? '—'}</dd>
            </div>
          </dl>
        </div>

        {/* Transcript */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-medium text-gray-900 mb-3">Transcript</h2>
          {transcript ? (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {transcript.map((turn) => (
                <div
                  key={turn.id}
                  className={`flex gap-2 ${turn.speaker === 'agent' ? '' : 'justify-end'}`}
                >
                  <div
                    className={`max-w-sm px-3 py-2 rounded-lg text-sm ${
                      turn.speaker === 'agent'
                        ? 'bg-gray-100 text-gray-800'
                        : 'bg-brand-600 text-white'
                    }`}
                  >
                    <div className="text-xs opacity-60 mb-0.5 capitalize">{turn.speaker}</div>
                    {turn.text}
                  </div>
                </div>
              ))}
              {!transcript.length && (
                <p className="text-sm text-gray-400">No transcript available.</p>
              )}
            </div>
          ) : (
            <Spinner />
          )}
        </div>

        {/* Responses */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-medium text-gray-900 mb-3">Recorded Responses</h2>
          {callResponses ? (
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 text-xs">
                  <th className="pb-2">Question Key</th>
                  <th className="pb-2">Parsed Value</th>
                  <th className="pb-2">Refused</th>
                  <th className="pb-2">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {callResponses.map((r) => (
                  <tr key={r.id}>
                    <td className="py-2 font-mono text-gray-700">{r.question_key}</td>
                    <td className="py-2 text-gray-900">{JSON.stringify(r.parsed_value)}</td>
                    <td className="py-2 text-gray-600">{r.is_refused ? 'Yes' : 'No'}</td>
                    <td className="py-2 text-gray-600">{(r.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
                {!callResponses.length && (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-gray-400">No responses recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <Spinner />
          )}
        </div>

        {/* Analysis */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium text-gray-900">AI Analysis</h2>
            <button
              onClick={() => triggerAnalysis.mutate()}
              disabled={triggerAnalysis.isPending}
              className="flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 disabled:opacity-50"
            >
              <RefreshCw size={14} className={triggerAnalysis.isPending ? 'animate-spin' : ''} />
              {report ? 'Re-run' : 'Run Analysis'}
            </button>
          </div>
          {report ? (
            <div className="space-y-3 text-sm">
              {report.content.summary && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Summary</div>
                  <p className="text-gray-800">{report.content.summary}</p>
                </div>
              )}
              {report.content.overall_sentiment && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Overall Sentiment</div>
                  <p className="text-gray-800 capitalize">{report.content.overall_sentiment}</p>
                </div>
              )}
              {report.content.key_themes?.length ? (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Key Themes</div>
                  <div className="flex flex-wrap gap-1">
                    {report.content.key_themes.map((t) => (
                      <span key={t} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No analysis yet. Click "Run Analysis" to generate.</p>
          )}
        </div>
      </div>
    </div>
  )
}
