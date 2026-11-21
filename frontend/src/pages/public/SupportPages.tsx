import { useState } from 'react'
import { Link } from 'react-router'
import { Field, Heading } from '../../components/common/UI'
import { useSession } from '../../contexts/SessionContext'
import { apiRequest, checkHealth, payload } from '../../services/api'

export function HelpPage({ workspace = false }: { workspace?: boolean }) {
  const [health, setHealth] = useState('')
  return <div className={workspace ? '' : 'wrap section'}><Heading title="Help & Support" />
    <div className="panel padded form-width"><h2>Finding accommodation</h2><p>Use the directory to narrow your search or open a listing to contact the manager. Confirm reported availability before making plans.</p><Link to="/hostels" className="text-link">Open hostel directory</Link>
      <h2>Account access</h2><p>Sign in with your account to save listings or start a conversation.</p><Link to="/login" className="text-link">Open login</Link>
      <h2>API connection</h2><button className="btn outline" disabled={health === 'Checking API connection…'} onClick={() => {
        setHealth('Checking API connection…')
        void checkHealth(AbortSignal.timeout(5000)).then(() => setHealth('API connection verified.')).catch(() => setHealth('Could not verify the API connection.'))
      }}>Check Django connection</button><p role="status">{health}</p>
    </div></div>
}

export function ProfileSettings() {
  const { token, account, refresh } = useSession()
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  return <><Heading title="Profile Settings" text="Your phone number is private." />
    <form className="panel padded form-width stack" onSubmit={async event => {
      event.preventDefault()
      const data = new FormData(event.currentTarget)
      setBusy(true); setError(''); setNotice('')
      try { await apiRequest('me/', payload('PATCH', Object.fromEntries(data)), token); refresh(); setNotice('Profile saved.') }
      catch (error) { setError(error instanceof Error ? error.message : 'Profile could not be saved.') }
      finally { setBusy(false) }
    }}>
      <Field label="Full name"><input name="full_name" required maxLength={150} defaultValue={account?.full_name} /></Field>
      <Field label="Username"><input name="username" required maxLength={64} defaultValue={account?.username} /></Field>
      <Field label="Phone"><input name="phone" type="tel" maxLength={32} defaultValue={account?.phone} /></Field>
      {error && <p role="alert" className="notice error">{error}</p>}{notice && <p role="status" className="notice">{notice}</p>}
      <div><button className="btn primary" disabled={busy}>Save changes</button></div>
    </form></>
}
