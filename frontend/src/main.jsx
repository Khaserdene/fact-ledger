import { Component, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class GlobalErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, info: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('Captured Render Error:', error, info)
    this.setState({ info })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '32px', background: '#090d16', color: '#ff6b6b', fontFamily: 'monospace', minHeight: '100vh' }}>
          <h1 style={{ fontSize: '20px', color: '#ff4d4f', marginBottom: '12px' }}>🚨 React Component Render Error</h1>
          <div style={{ background: '#141c2e', padding: '16px', borderRadius: '8px', border: '1px solid #ff4d4f33', marginBottom: '16px' }}>
            <strong>{this.state.error?.toString()}</strong>
          </div>
          <pre style={{ fontSize: '11px', color: '#94a3b8', overflowX: 'auto', background: '#05080e', padding: '16px', borderRadius: '8px' }}>
            {this.state.info?.componentStack || this.state.error?.stack}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{ marginTop: '16px', padding: '8px 16px', background: '#38e0ff', color: '#090d16', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Хуудсыг дахин ачааллах (Reload)
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <GlobalErrorBoundary>
      <App />
    </GlobalErrorBoundary>
  </StrictMode>,
)

