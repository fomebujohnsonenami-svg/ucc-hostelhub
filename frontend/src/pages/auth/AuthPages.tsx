import { useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router'
import { Field, Heading } from '../../components/common/UI'
import { useSession } from '../../contexts/SessionContext'
import { apiRequest, payload } from '../../services/api'

export function AuthPage({ mode, startingRole }: { mode: 'login' | 'register'; startingRole?: 'student' | 'manager' }) {
  const [query] = useSearchParams()
  const { account, token, loading, error: profileError, setToken } = useSession()
  const [role, setRole] = useState(startingRole ?? 'student')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const registering = mode === 'register'
  const requested = query.get('next') ?? ''
  const next = /^\/(hostels|roommates)\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\/?$/i.test(requested) ? requested : ''
  const alternate = (registering ? '/login' : '/register') + (next ? `?${new URLSearchParams({ next })}` : '')

  if (account) return <Navigate to={account.role === 'student' && next ? next : `/${account.role}`} replace />

  return <div className="auth-wrap"><div className="panel padded">
    <Heading title={registering ? 'Create an account' : 'Welcome back'} />
    <form className="stack" onSubmit={async event => {
      event.preventDefault()
      setBusy(true)
      setError('')
      try {
        const fields = Object.fromEntries(new FormData(event.currentTarget))
        const { token } = await apiRequest<{ token: string }>(`auth/${mode}/`, payload('POST', fields))
        setToken(token)
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Sign-in could not be completed.')
      } finally {
        setBusy(false)
      }
    }}>
      <Field label="Email address"><input name="email" type="email" autoComplete="username" required /></Field>
      <Field label="Password"><input name="password" type="password" autoComplete={registering ? 'new-password' : 'current-password'} minLength={registering ? 8 : undefined} maxLength={128} required /></Field>
      {registering && <>
        <Field label="Full name"><input name="full_name" autoComplete="name" maxLength={150} required /></Field>
        <Field label="Username"><input name="username" maxLength={64} required /></Field>
        <Field label="Account role"><select name="role" value={role} onChange={event => setRole(event.target.value === 'manager' ? 'manager' : 'student')}><option value="student">Student</option><option value="manager">Hostel Manager</option></select></Field>
        {role === 'manager' && <Field label="Business name"><input name="business_name" autoComplete="organization" maxLength={160} required /></Field>}
      </>}
      <button className="btn primary" disabled={busy || loading}>{registering ? 'Create account' : 'Log in'}</button>
    </form>
    <div className="dashboard-gap"><Link className="text-link" to={alternate}>{registering ? 'Back to login' : 'Create an account'}</Link></div>
    {token && profileError && !error && <p className="notice error" role="alert">Could not load your account. {profileError.message}</p>}
    {error && <p className="notice error" role="alert">{error}</p>}
  </div></div>
}
