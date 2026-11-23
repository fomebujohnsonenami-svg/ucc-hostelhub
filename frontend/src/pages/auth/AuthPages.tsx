import { useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router'
import { Field, Heading } from '../../components/common/UI'
import { useSession } from '../../contexts/SessionContext'
import { ApiError, apiRequest, payload } from '../../services/api'
import { supabase } from '../../services/supabase'

export function AuthPage({ mode, startingRole }: { mode: 'login' | 'register'; startingRole?: 'student' | 'manager' }) {
  const client = supabase
  const [query] = useSearchParams()
  const requested = query.get('next') ?? ''
  const next = /^\/(hostels|roommates)\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\/?$/i.test(requested) ? requested : ''
  const loginQuery = `/login?${new URLSearchParams({ role: query.get('role') === 'manager' ? 'manager' : 'student', ...(next ? { next } : {}) })}`
  const registration = next ? `/register?${new URLSearchParams({ next })}` : '/register'
  const { account, token, loading, error: profileError, refresh } = useSession()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [role, setRole] = useState(startingRole ?? (query.get('role') === 'manager' ? 'manager' : 'student'))

  async function run(operation: () => Promise<void>) {
    setBusy(true)
    setError('')
    try { await operation() } catch (error) {
      setError(error instanceof Error ? error.message : 'The request could not be completed.')
    } finally { setBusy(false) }
  }

  if (account?.role === 'student' && next) return <Navigate to={next} replace />

  const newProfile = token && profileError instanceof ApiError && profileError.status === 401
  return <div className="auth-wrap"><div className="panel padded">
    <Heading title={mode === 'login' ? 'Welcome back' : 'Create an account'} />
    {!client ? <p role="alert">Email sign-in is not configured for this deployment.</p> : loading ? <p role="status">Checking your session…</p> :
      account ? <Link className="btn primary" to={`/${account.role}`}>Open your dashboard</Link> :
      newProfile ? <form className="stack" onSubmit={event => {
        event.preventDefault()
        const data = new FormData(event.currentTarget)
        void run(async () => {
          await apiRequest('onboarding/', payload('POST', { full_name: data.get('name'), username: data.get('username'), role, ...(role === 'manager' ? { business_name: data.get('business') } : {}) }), token)
          refresh()
        })
      }}>
        <h2>Complete your profile</h2><Field label="Full name"><input name="name" maxLength={150} required /></Field>
        <Field label="Username"><input name="username" maxLength={64} pattern="[A-Za-z0-9_\-]+" required /></Field>
        <Field label="Account role"><select value={role} onChange={event => setRole(event.target.value === 'manager' ? 'manager' : 'student')}><option value="student">Student</option><option value="manager">Hostel Manager</option></select></Field>
        {role === 'manager' && <Field label="Business name"><input name="business" maxLength={160} required /></Field>}
        <button className="btn primary" disabled={busy}>Save profile</button>
      </form> : profileError ? <><p role="alert">{profileError.message}</p><button className="btn outline" onClick={refresh}>Try again</button></> :
      <><form className="stack" onSubmit={event => {
        event.preventDefault()
        const data = new FormData(event.currentTarget)
        void run(async () => {
          const email = String(data.get('email')).trim()
          const password = String(data.get('password') ?? '')
          if (mode === 'register') {
            const result = await client.auth.signUp({ email, password })
            if (result.error) throw result.error
            if (!result.data.session) throw new Error('Instant signup is unavailable. Contact support.')
          } else {
            const result = await client.auth.signInWithPassword({ email, password })
            if (result.error) throw result.error
          }
        })
      }}>
        <Field label="Email address"><input name="email" type="email" autoComplete="username" required /></Field>
        <Field label="Password"><input name="password" type="password" minLength={mode === 'register' ? 8 : undefined} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} required /></Field>
        {mode === 'register' && <Field label="Account role"><select value={role} onChange={event => setRole(event.target.value === 'manager' ? 'manager' : 'student')}><option value="student">Student</option><option value="manager">Hostel Manager</option></select></Field>}
        <button className="btn primary" disabled={busy}>{mode === 'login' ? 'Log in' : 'Create account'}</button>
      </form>
        <div className="row dashboard-gap">{mode === 'login' ? <Link className="text-link" to={registration}>Create an account</Link> : <Link className="text-link" to={loginQuery}>Back to login</Link>}</div>
      </>}
    {error && <p className="notice error" role="alert">{error}</p>}
  </div></div>
}
