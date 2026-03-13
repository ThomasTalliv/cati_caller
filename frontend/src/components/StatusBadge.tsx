const colors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  active: 'bg-green-100 text-green-700',
  closed: 'bg-red-100 text-red-700',
  pending: 'bg-yellow-100 text-yellow-700',
  dialing: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  busy: 'bg-orange-100 text-orange-700',
  no_answer: 'bg-orange-100 text-orange-700',
  cancelled: 'bg-gray-100 text-gray-700',
  running: 'bg-blue-100 text-blue-700',
}

interface Props {
  status: string
}

export default function StatusBadge({ status }: Props) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        colors[status] ?? 'bg-gray-100 text-gray-700'
      }`}
    >
      {status.replace(/_/g, ' ')}
    </span>
  )
}
