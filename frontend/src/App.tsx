import { Component, type ReactNode } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Upload from './pages/Upload'
import Reports from './pages/Reports'
import Budgets from './pages/Budgets'

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null }
  static getDerivedStateFromError(error: Error) { return { error } }
  render() {
    if (this.state.error) {
      return (
        <div className="p-8 max-w-2xl">
          <h2 className="text-lg font-bold text-rose-400 mb-2">Something went wrong</h2>
          <pre className="text-sm text-rose-300 bg-white/5 border border-white/10 p-4 rounded-xl overflow-auto whitespace-pre-wrap">
            {(this.state.error as Error).message}
            {'\n\n'}
            {(this.state.error as Error).stack}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            className="mt-4 btn-ghost"
          >
            Dismiss
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#080810]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/budgets" element={<Budgets />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  )
}
