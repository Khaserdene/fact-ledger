import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import EntityDetail from './pages/EntityDetail'
import EntityList from './pages/EntityList'
import FactImport from './pages/FactImport'
import GraphHub from './pages/GraphHub'
import SourceCapture from './pages/SourceCapture'
import SourceList from './pages/SourceList'
import SourceView from './pages/SourceView'
import MacroAnalytics from './pages/MacroAnalytics'

/** Хуучин замуудаас шинэ рүү чиглүүлэлт */
function RedirectWithId({ to }) {
  const { id } = useParams()
  return <Navigate to={to.replace(':id', id)} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<GraphHub />} />
          <Route path="/macro" element={<MacroAnalytics />} />
          <Route path="/sources" element={<SourceList />} />
          <Route path="/capture" element={<SourceCapture />} />
          <Route path="/sources/:id" element={<SourceView />} />
          <Route path="/entities" element={<EntityList />} />
          <Route path="/entities/:id" element={<EntityDetail />} />
          <Route path="/entities/:id/import" element={<FactImport />} />
          {/* Хуучин замууд */}
          <Route path="/articles" element={<Navigate to="/sources" replace />} />
          <Route path="/articles/:id" element={<RedirectWithId to="/sources/:id" />} />
          <Route path="/profiles" element={<Navigate to="/entities" replace />} />
          <Route path="/profiles/:id" element={<RedirectWithId to="/entities/:id" />} />
          <Route path="/profiles/:id/import" element={<RedirectWithId to="/entities/:id/import" />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}
