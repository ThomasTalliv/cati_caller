import { useQuery } from '@tanstack/react-query'
import { PhoneCall, ClipboardList, Users, CheckCircle } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import { surveys, calls, contacts } from '../api/client'

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType
  label: string
  value: string | number
  color: string
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        <div className="text-sm text-gray-500">{label}</div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: surveyList, isLoading: s } = useQuery({
    queryKey: ['surveys'],
    queryFn: surveys.list,
  })
  const { data: callList, isLoading: c } = useQuery({
    queryKey: ['calls'],
    queryFn: () => calls.list(),
  })
  const { data: contactList, isLoading: ct } = useQuery({
    queryKey: ['contacts'],
    queryFn: () => contacts.list(),
  })

  const isLoading = s || c || ct
  const activeSurveys = surveyList?.filter((s) => s.status === 'active').length ?? 0
  const totalCalls = callList?.length ?? 0
  const completedCalls = callList?.filter((c) => c.status === 'completed').length ?? 0
  const totalContacts = contactList?.length ?? 0

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Overview of your CATI campaign activity" />
      <div className="p-6 space-y-6">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spinner size={32} />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
              <StatCard icon={ClipboardList} label="Active Surveys" value={activeSurveys} color="bg-brand-600" />
              <StatCard icon={PhoneCall} label="Total Calls" value={totalCalls} color="bg-violet-500" />
              <StatCard icon={CheckCircle} label="Completed Calls" value={completedCalls} color="bg-green-500" />
              <StatCard icon={Users} label="Contacts" value={totalContacts} color="bg-orange-500" />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              {/* Recent surveys */}
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="px-4 py-3 border-b border-gray-100">
                  <h2 className="font-medium text-gray-900">Recent Surveys</h2>
                </div>
                <ul className="divide-y divide-gray-100">
                  {surveyList?.slice(0, 5).map((s) => (
                    <li key={s.id} className="px-4 py-3 flex items-center justify-between">
                      <span className="text-sm text-gray-800">{s.name}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${
                          s.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : s.status === 'draft'
                            ? 'bg-gray-100 text-gray-600'
                            : 'bg-red-100 text-red-600'
                        }`}
                      >
                        {s.status}
                      </span>
                    </li>
                  ))}
                  {!surveyList?.length && (
                    <li className="px-4 py-6 text-sm text-gray-400 text-center">No surveys yet</li>
                  )}
                </ul>
              </div>

              {/* Recent calls */}
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="px-4 py-3 border-b border-gray-100">
                  <h2 className="font-medium text-gray-900">Recent Calls</h2>
                </div>
                <ul className="divide-y divide-gray-100">
                  {callList?.slice(0, 5).map((c) => (
                    <li key={c.id} className="px-4 py-3 flex items-center justify-between">
                      <span className="text-sm font-mono text-gray-700">{c.phone_number}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${
                          c.status === 'completed'
                            ? 'bg-green-100 text-green-700'
                            : c.status === 'failed'
                            ? 'bg-red-100 text-red-600'
                            : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {c.status}
                      </span>
                    </li>
                  ))}
                  {!callList?.length && (
                    <li className="px-4 py-6 text-sm text-gray-400 text-center">No calls yet</li>
                  )}
                </ul>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
