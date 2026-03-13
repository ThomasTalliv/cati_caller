import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Save, CheckCircle } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import { health } from '../api/client'

export default function Settings() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('cati_api_key') ?? '')
  const [saved, setSaved] = useState(false)

  const { data: healthData, refetch, isError } = useQuery({
    queryKey: ['health'],
    queryFn: health.check,
    retry: false,
  })

  const handleSave = () => {
    localStorage.setItem('cati_api_key', apiKey)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
    refetch()
  }

  return (
    <div>
      <PageHeader title="Settings" subtitle="API connection and configuration" />
      <div className="p-6 max-w-xl space-y-6">
        {/* API connection */}
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <h2 className="font-medium text-gray-900">API Connection</h2>

          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-600">Status:</span>
            {healthData ? (
              <span className="flex items-center gap-1 text-green-600">
                <CheckCircle size={14} /> Connected ({healthData.version})
              </span>
            ) : isError ? (
              <span className="text-red-500">Not connected</span>
            ) : (
              <span className="text-gray-400">Checking…</span>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">API Key</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
            />
            <p className="mt-1 text-xs text-gray-400">
              Set via <code className="bg-gray-100 px-1 rounded">API_KEY</code> environment variable on the server.
              Default: <code className="bg-gray-100 px-1 rounded">change-me</code>
            </p>
          </div>

          <button
            onClick={handleSave}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-md"
          >
            {saved ? <CheckCircle size={16} /> : <Save size={16} />}
            {saved ? 'Saved!' : 'Save'}
          </button>
        </div>

        {/* Info */}
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-2">
          <h2 className="font-medium text-gray-900">About</h2>
          <p className="text-sm text-gray-600">
            CATI Caller — AI-powered telephone interviewing platform.
          </p>
          <dl className="text-sm space-y-1 text-gray-600">
            <div className="flex gap-2">
              <dt className="text-gray-400 w-28">API Base</dt>
              <dd className="font-mono">/api/v1</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-gray-400 w-28">Docs</dt>
              <dd>
                <a href="/docs" target="_blank" className="text-brand-600 hover:underline">
                  /docs (Swagger)
                </a>
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
