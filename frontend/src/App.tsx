import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Surveys from './pages/Surveys'
import SurveyEditor from './pages/SurveyEditor'
import Contacts from './pages/Contacts'
import Calls from './pages/Calls'
import CallDetail from './pages/CallDetail'
import Results from './pages/Results'
import Exports from './pages/Exports'
import Settings from './pages/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="surveys" element={<Surveys />} />
          <Route path="surveys/new" element={<SurveyEditor />} />
          <Route path="surveys/:id/edit" element={<SurveyEditor />} />
          <Route path="contacts" element={<Contacts />} />
          <Route path="calls" element={<Calls />} />
          <Route path="calls/:id" element={<CallDetail />} />
          <Route path="results" element={<Results />} />
          <Route path="exports" element={<Exports />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
