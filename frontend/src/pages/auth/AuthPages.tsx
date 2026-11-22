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
  const registration = next ? `/register?${new URLSearchParams({ next })}` : '/register'
  const { account, token, loading, error: profileError, refresh } = useSession()
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [role, setRole] = useState(startingRole ?? (query.get('role') === 'manager' ? 'manager' : 'student'))
  const [email, setEmail] = useState('')
  const loginQuery = `/login?${new URLSearchParams({ role, ...(next ? { next } : {}) })}`

  async function run(operation: () => Promise<void>) {
    setBusy(true)
    setError('')
    setNotice('')
    try { await operation() } catch (error) {
      setError(error instanceof Error ? error.message : 'The request could not be completed.')
    } finally { setBusy(false) }
  }

  async function sendCode(address: string) {
    if (!client) return
    const { error } = await client.auth.signInWithOtp({
      email: address,
      options: { shouldCreateUser: mode === 'register' },
    })
    if (error) throw error
    setEmail(address)
    setNotice('Check your inbox for your sign-in code.')
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
      <>
        {email ? <>
          <form className="stack" onSubmit={event => {
            event.preventDefault()
            const code = String(new FormData(event.currentTarget).get('code')).trim()
            void run(async () => {
              const { error } = await client.auth.verifyOtp({ email, token: code, type: 'email' })
              if (error) throw error
            })
          }}>
            <p>Enter the one-time code sent to <strong>{email}</strong>.</p>
            <Field label="Verification code"><input name="code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]+" required /></Field>
            <button className="btn primary" disabled={busy}>Verify code</button>
          </form>
          <div className="row dashboard-gap">
            <button type="button" className="btn outline" disabled={busy} onClick={() => void run(() => sendCode(email))}>Resend code</button>
            <button type="button" className="btn outline" disabled={busy} onClick={() => {
              setEmail('')
              setError('')
              setNotice('')
            }}>Change email</button>
          </div>
        </> : <form className="stack" onSubmit={event => {
          event.preventDefault()
          const address = String(new FormData(event.currentTarget).get('email')).trim()
          void run(() => sendCode(address))
        }}>
          <Field label="Email address"><input name="email" type="email" autoComplete="email" required /></Field>
          {mode === 'register' && <Field label="Account role"><select value={role} onChange={event => setRole(event.target.value === 'manager' ? 'manager' : 'student')}><option value="student">Student</option><option value="manager">Hostel Manager</option></select></Field>}
          <button className="btn primary" disabled={busy}>Send verification code</button>
        </form>}
        <div className="row dashboard-gap">{mode === 'login' ? <Link className="text-link" to={registration}>Create an account</Link> : <Link className="text-link" to={loginQuery}>Back to login</Link>}</div>
      </>}
    {notice && <p className="notice" role="status">{notice}</p>}{error && <p className="notice error" role="alert">{error}</p>}
  </div></div>
}
