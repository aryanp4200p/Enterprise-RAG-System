import { API_BASE, REQUEST_TIMEOUT_MS } from './config'

async function readErrorMessage(response) {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    if (typeof body.error === 'string') return body.error
    if (Array.isArray(body.detail)) return 'Please check your question and try again.'
  } catch {
    // body was not JSON - fall through
  }
  return `Server error (${response.status}). Please try again.`
}

/**
 * POST /ask. Rejects with an Error whose message is safe to show to the user.
 * `signal` lets the caller cancel; the request also times out by itself.
 */
export async function askQuestion({ query, role, signal }) {
  const timeout = new AbortController()
  const timer = setTimeout(() => timeout.abort(), REQUEST_TIMEOUT_MS)
  const onCallerAbort = () => timeout.abort()
  signal?.addEventListener('abort', onCallerAbort)

  try {
    const response = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, role }),
      signal: timeout.signal
    })

    if (!response.ok) throw new Error(await readErrorMessage(response))

    const data = await response.json()
    if (data.error) throw new Error(data.error) // older backend versions returned 200 + {error}
    return data
  } catch (err) {
    if (signal?.aborted) throw err // cancelled by the caller on purpose
    if (err.name === 'AbortError') {
      throw new Error('The request timed out. The backend may be waking up - please try again.', { cause: err })
    }
    if (err instanceof TypeError) {
      throw new Error('Cannot reach the backend. Check your connection and that the server allows this site (CORS).', { cause: err })
    }
    throw err
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', onCallerAbort)
  }
}

/** GET / - true when the backend answers. */
export async function checkHealth(signal) {
  try {
    const response = await fetch(`${API_BASE}/`, { signal })
    return response.ok
  } catch {
    return false
  }
}
