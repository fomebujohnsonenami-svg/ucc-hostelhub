import { useState } from 'react'
import { useSession } from '../../contexts/SessionContext'
import { apiRequest, payload } from '../../services/api'
import { Field, Modal } from './UI'

export default function ReportButton({ target, id }: { target: 'hostel' | 'roommate' | 'message'; id: string }) {
  const { token } = useSession()
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  if (!token) return null
  return <>{sent ? <span role="status">Report submitted.</span> : <button className="text-link" onClick={() => setOpen(true)}>Report {target}</button>}
  {open && <Modal title={`Report ${target}`} close={() => setOpen(false)}><form className="stack" onSubmit={async event => {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    try {
      await apiRequest('reports/', payload('POST', { target_type: target, target_id: id, reason: data.get('reason') }), token)
      setOpen(false)
      setSent(true)
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not report content.') }
    finally { setBusy(false) }
  }}><Field label="Reason"><textarea name="reason" rows={4} required maxLength={1500} /></Field>{error && <p role="alert">{error}</p>}
  <button className="btn primary" disabled={busy}>Submit report</button></form></Modal>}</>
}
