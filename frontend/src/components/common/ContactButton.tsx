import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useSession } from '../../contexts/SessionContext'
import { apiRequest, payload } from '../../services/api'
import PremiumBadge from '../premium/PremiumBadge'

export default function ContactButton({ target, id, label }: { target: 'hostel' | 'roommate'; id: string; label: string }) {
  const { account, token } = useSession()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const destination = `/${target === 'hostel' ? 'hostels' : 'roommates'}/${encodeURIComponent(id)}`
  const login = `/login?${new URLSearchParams({ next: destination })}`
  if (!account) return <div className="row"><Link className="btn primary" to={login}>{label}</Link><PremiumBadge>Student Premium</PremiumBadge></div>
  if (account.role !== 'student' || !token) return null
  return <div><div className="row"><button className="btn primary" disabled={busy} onClick={async () => {
    setBusy(true)
    setError('')
    try {
      const conversation = await apiRequest<{ id: string }>('conversations/', payload('POST', { [target]: id }), token)
      void navigate(`/student/messages/${conversation.id}`)
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not start conversation.') }
    finally { setBusy(false) }
  }}>{label}</button><PremiumBadge>Student Premium</PremiumBadge></div>{error && <p className="notice error" role="alert">{error}</p>}</div>
}
