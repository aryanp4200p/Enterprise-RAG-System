import { useEffect, useMemo, useRef, useState } from 'react'
import heroAsset from './assets/hero.png'
import { askQuestion, checkHealth } from './api'
import { API_BASE, API_HOST, MAX_QUERY_CHARS } from './config'
import './App.css'

// `value` must match a role known to the backend (backend/app/security/rbac.py).
const ROLES = [
  {
    value: 'finance',
    label: 'Finance',
    tone: 'Annual report, revenue, strategy',
    accent: 'emerald',
    examples: ['What was the projected revenue growth?', 'What investments were made in AI infrastructure?']
  },
  {
    value: 'stock_market',
    label: 'Market Insights',
    tone: 'Stocks, trends, 2024 performance',
    accent: 'violet',
    examples: ['How did AI stocks perform in 2024?', 'Summarize stock market performance.']
  },
  {
    value: 'hr',
    label: 'HR',
    tone: 'Policies, leave, remote work',
    accent: 'rose',
    examples: ['What are the remote work policies?', 'Explain employee leave benefits.']
  },
  {
    value: 'engineering',
    label: 'Engineering',
    tone: 'Architecture, security, retrieval',
    accent: 'blue',
    examples: ['What vector database is used?', 'What security layers are included?']
  },
  {
    value: 'executive',
    label: 'Executive',
    tone: 'Finance, HR, engineering and markets',
    accent: 'amber',
    examples: ['Summarize the financial strategy.', 'What are the remote work policies?']
  }
]

const HEALTH_LABEL = {
  checking: 'Connecting...',
  online: 'Backend online',
  offline: 'Backend unreachable'
}

// Backends return chunks either as plain strings (old) or {text, source, page, department}.
const normalizeDoc = (doc) =>
  typeof doc === 'string'
    ? { text: doc }
    : { text: doc?.text ?? '', source: doc?.source, page: doc?.page, department: doc?.department }

function App() {
  const [query, setQuery] = useState('')
  const [role, setRole] = useState('engineering')
  const [answer, setAnswer] = useState('')
  const [answeredRole, setAnsweredRole] = useState('')
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [health, setHealth] = useState('checking')
  const requestRef = useRef(null)

  const activeRole = useMemo(() => ROLES.find((item) => item.value === role), [role])
  const answerLabel = ROLES.find((item) => item.value === answeredRole)?.label

  // Real backend status (this used to be a hard-coded "Backend online").
  useEffect(() => {
    const controller = new AbortController()
    checkHealth(controller.signal).then((ok) => {
      if (!controller.signal.aborted) setHealth(ok ? 'online' : 'offline')
    })
    return () => controller.abort()
  }, [])

  // Cancel any in-flight request when the page is closed.
  useEffect(() => () => requestRef.current?.abort(), [])

  const handleSubmit = async (event) => {
    event?.preventDefault()
    const question = query.trim()
    if (!question) {
      setError('Please type a question first.')
      return
    }
    if (loading) return

    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller

    setLoading(true)
    setError('')
    setAnswer('')
    setAnsweredRole('')
    setDocs([])

    try {
      const data = await askQuestion({ query: question, role, signal: controller.signal })
      setAnswer(data.answer || 'No answer returned from the backend.')
      setAnsweredRole(data.role || role)
      setDocs(Array.isArray(data.retrieved_docs) ? data.retrieved_docs.map(normalizeDoc) : [])
      setHealth('online')
    } catch (err) {
      if (controller.signal.aborted) return
      setError(err.message || 'Unable to reach backend.')
      checkHealth().then((ok) => setHealth(ok ? 'online' : 'offline'))
    } finally {
      if (requestRef.current === controller) {
        setLoading(false)
        requestRef.current = null
      }
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) handleSubmit(event)
  }

  const handleExample = (example) => {
    if (!loading) {
      setQuery(example)
      setError('')
    }
  }

  return (
    <div className={`app-shell theme-${activeRole.accent}`}>
      <header className="hero">
        <nav className="nav">
          <div className="brand">
            <span className="brand-mark">R</span>
            <span>RAG Command</span>
          </div>
          <div className="status-pill" data-state={health} role="status">
            <span className="status-dot" />
            {HEALTH_LABEL[health]}
          </div>
        </nav>

        <div className="hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Enterprise RAG Assistant</p>
            <h1>Ask your deployed knowledge base with role-aware precision.</h1>
            <p className="subtitle">
              Query your Hugging Face RAG backend, inspect retrieved sources, and switch business
              context without leaving a focused workspace.
            </p>
            <div className="hero-actions" aria-label="App highlights">
              <span>Secure role context</span>
              <span>Source visibility</span>
              <span>Live retrieval</span>
            </div>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <img src={heroAsset} alt="" />
            <div className="metric-strip">
              <div>
                <strong>{ROLES.length}</strong>
                <span>roles</span>
              </div>
              <div>
                <strong>{docs.length}</strong>
                <span>sources</span>
              </div>
              <div>
                <strong>{loading ? '...' : answer ? '1' : '0'}</strong>
                <span>answers</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="workspace">
        <section className="query-panel" aria-labelledby="question-title">
          <div className="section-heading">
            <div>
              <p className="kicker">Prompt console</p>
              <h2 id="question-title">Compose your question</h2>
            </div>
            <span className="live-badge">{activeRole.label}</span>
          </div>

          <form onSubmit={handleSubmit} className="query-form">
            <label className="field-label" htmlFor="query">
              Question
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about market research notes, internal policies, engineering docs, or financial plans..."
              rows={7}
              maxLength={MAX_QUERY_CHARS}
              disabled={loading}
            />
            <div className="char-count">
              Ctrl/Cmd + Enter to send | {query.length}/{MAX_QUERY_CHARS}
            </div>

            <div className="role-block">
              <div className="field-label">Role context</div>
              <div className="role-grid" role="radiogroup" aria-label="Role context">
                {ROLES.map((option) => (
                  <button
                    className={`role-option ${role === option.value ? 'active' : ''}`}
                    type="button"
                    key={option.value}
                    onClick={() => setRole(option.value)}
                    disabled={loading}
                    role="radio"
                    aria-checked={role === option.value}
                  >
                    <span>{option.label}</span>
                    <small>{option.tone}</small>
                  </button>
                ))}
              </div>
            </div>

            <div className="example-row" aria-label="Example questions">
              {activeRole.examples.map((example) => (
                <button key={example} type="button" onClick={() => handleExample(example)} disabled={loading}>
                  {example}
                </button>
              ))}
            </div>

            {error && (
              <div className="alert" role="alert">
                {error}
              </div>
            )}

            <button type="submit" className="submit-button" disabled={loading}>
              <span>{loading ? 'Searching knowledge base' : 'Send question'}</span>
              <span className="button-icon" aria-hidden="true">
                {loading ? '...' : '->'}
              </span>
            </button>
          </form>
        </section>

        <section className="answer-panel" aria-labelledby="answer-title">
          <div className="section-heading">
            <div>
              <p className="kicker">Generated response</p>
              <h2 id="answer-title">Answer preview</h2>
            </div>
            <span className="live-badge">{answerLabel ? `${answerLabel} answer` : 'Live API'}</span>
          </div>

          <div className="answer-box">
            {loading ? (
              <div className="loading-state">
                <span />
                <p>Retrieving the most relevant passages...</p>
              </div>
            ) : answer ? (
              <p>{answer}</p>
            ) : (
              <div className="empty-state">
                <strong>Ready when you are.</strong>
                <span>Submit a question and your answer will appear here with sources below.</span>
              </div>
            )}
          </div>

          <div className="sources-header">
            <h3>Retrieved documents</h3>
            <span>{docs.length} found</span>
          </div>

          {docs.length > 0 ? (
            <ul className="source-list">
              {docs.map((doc, index) => (
                <li key={`${doc.source ?? 'doc'}-${doc.page ?? index}-${index}`}>
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <div>
                    {doc.source && (
                      <small className="source-meta">
                        {doc.source}
                        {doc.page ? ` | page ${doc.page}` : ''}
                      </small>
                    )}
                    <p>{doc.text}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="source-empty">Sources will populate after a successful retrieval.</div>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>Deployed backend</span>
        <a href={API_BASE} target="_blank" rel="noreferrer">
          {API_HOST}
        </a>
      </footer>
    </div>
  )
}

export default App
