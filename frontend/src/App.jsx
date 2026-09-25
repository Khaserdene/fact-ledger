import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/LoginPage'
import CodeGeneratorPage from './pages/CodeGeneratorPage'
import EntityDetail from './pages/EntityDetail'
import EntityList from './pages/EntityList'
import FactImport from './pages/FactImport'
import GraphHub from './pages/GraphHub'
import SourceCapture from './pages/SourceCapture'
import SourceList from './pages/SourceList'
import SourceView from './pages/SourceView'
import MacroAnalytics from './pages/MacroAnalytics'
import CaseList from './pages/CaseList'
import CaseEditor from './pages/CaseEditor'
import MediaIntelligence from './pages/MediaIntelligence'

/** Хуучин замуудаас шинэ рүү чиглүүлэлт */
function RedirectWithId({ to }) {
  const { id } = useParams()
  return <Navigate to={to.replace(':id', id)} replace />
}

/** Нэвтэрсэн эсэхийг шалгах route wrapper */
function ProtectedRoutes() {
  const { authed } = useAuth()
  if (!authed) return <Navigate to="/login" replace />
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<GraphHub />} />
        <Route path="/macro" element={<MacroAnalytics />} />
        <Route path="/cases" element={<CaseList />} />
        <Route path="/cases/:slug" element={<CaseEditor />} />
        <Route path="/media" element={<MediaIntelligence />} />
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
        {/* Бусад замыг нүүр хуудас руу */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

/** Нэвтрэх хуудас: аль хэдийн нэвтэрсэн бол тохирох нүүр рүү шилжинэ */
function LoginRoute() {
  const { authed, isMaster } = useAuth()
  if (authed) {
    return <Navigate to={isMaster ? '/generate' : '/'} replace />
  }
  return <LoginPage />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/generate" element={<CodeGeneratorPage />} />
          <Route path="/generator" element={<Navigate to="/generate" replace />} />
          <Route path="/*" element={<ProtectedRoutes />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
