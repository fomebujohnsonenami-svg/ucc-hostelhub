import { Building2, ClipboardCheck, ShieldCheck, Users } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { Badge, Empty, Field, Heading, Modal } from '../../components/common/UI'
import { Paging, Result } from '../../components/common/ApiUI'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import { apiRequest, payload } from '../../services/api'
import type { ApiPage } from '../../services/api'
import type { Account } from '../../contexts/SessionContext'

type Section = 'users' | 'listings' | 'verification' | 'moderation'
const config = {
  users: { title: 'User Management', endpoint: 'users', icon: Users },
  listings: { title: 'Hostel Listing Moderation', endpoint: 'listings', icon: Building2 },
  verification: { title: 'Manager Verification', endpoint: 'managers', icon: ShieldCheck },
  moderation: { title: 'Content Moderation', endpoint: 'reports', icon: ClipboardCheck },
}
type Listing = { id: string; name: string; area: string; address: string; description: string; manager_name: string; verification_status: string; publication_status: string }
type Manager = { id: string; full_name: string; business_name: string; verification_status: string; verification_notes: string }
type Report = { id: string; target_type: string; target_id: string; reason: string; status: string }
type RecordTypes = Account | Listing | Manager | Report
type Action = { title: string; id: string; method: string; body: Record<string, string>; notes?: string }

export default function AdminPage({ section }: { section?: Section }) {
  return section ? <Records section={section} key={section} /> : <Dashboard />
}

function Dashboard() {
  const { token } = useSession()
  const stats = useApi<Record<Section, number>>('dashboard/admin/', token)
  return <><Heading title="Administrator Dashboard" text="Manage published listings, manager accounts, and reported content." /><Result loading={stats.loading} error={stats.error}>
    <div className="action-grid">{(Object.keys(config) as Section[]).map(section => {
      const { icon: Icon, title } = config[section]
      return <Link className="panel action-card" key={section} to={`/admin/${section}`}><span className="tile-icon"><Icon size={20} /></span><strong className="stat-value">{stats.data?.[section] ?? '—'}</strong><small>{title}</small></Link>
    })}</div></Result></>
}

function Records({ section }: { section: Section }) {
  const { token } = useSession()
  const [page, setPage] = useState(1)
  const [action, setAction] = useState<Action>()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const { title, endpoint } = config[section]
  const path = `admin/${endpoint}/`
  const data = useApi<ApiPage<RecordTypes>>(`${path}?page=${page}`, token)

  function review(next: Action) { setAction(next); setError(''); setNotice('') }
  function body(record: RecordTypes) {
    if ('manager_name' in record) return <><h2>{record.name}</h2><p>{record.area} · {record.address} · {record.manager_name}</p><p>{record.description}</p>
      <Badge>{record.publication_status}</Badge>
      {record.publication_status === 'published' && <div className="row dashboard-gap">
        <button className="btn outline" onClick={() => review({ title: 'Suspend listing', id: record.id, method: 'POST', body: { action: 'suspend' } })}>Suspend</button>
      </div>}</>
    if ('business_name' in record) return <><h2>{record.business_name}</h2><p>{record.full_name}</p><Badge>{record.verification_status}</Badge>
      <div className="row dashboard-gap"><button className="btn outline" onClick={() => review({ title: 'Verify manager', id: record.id, method: 'PATCH', body: { verification_status: 'verified' }, notes: record.verification_notes })}>Verify manager</button>
      <button className="btn outline" onClick={() => review({ title: 'Reject manager verification', id: record.id, method: 'PATCH', body: { verification_status: 'rejected' }, notes: record.verification_notes })}>Reject verification</button></div></>
    if ('target_type' in record) return <><h2>Reported {record.target_type}</h2><p className="small-text">{record.target_id}</p><p>{record.reason}</p><Badge>{record.status}</Badge>
      {record.target_type === 'hostel' && <div className="row dashboard-gap"><Link className="text-link" to={`/hostels/${record.target_id}`}>View published listing</Link></div>}
      <div className="row dashboard-gap">{record.status !== 'resolved' && record.target_type !== 'profile' && <button className="btn outline" onClick={() => review({ title: 'Remove reported content', id: record.id, method: 'PATCH', body: { action: 'remove' } })}>Remove content</button>}{['reviewing', 'resolved', 'dismissed'].filter(status => status !== record.status).map(status =>
        <button className="btn outline" key={status} onClick={() => review({ title: `Mark report ${status}`, id: record.id, method: 'PATCH', body: { status } })}>Mark {status}</button>)}</div></>
    return <><h2>{record.full_name}</h2><p>{record.username}</p><Badge>{record.role}</Badge></>
  }

  return <><Heading title={title} /><Result loading={data.loading} error={data.error}>
    {notice && <p className="notice" role="status">{notice}</p>}
    {data.data?.results.length === 0 && <Empty title="No records" />}
    <div className="stack">{data.data?.results.map(record => <article className="panel padded" key={record.id}>{body(record)}</article>)}</div>
    <Paging page={data.data} number={page} change={setPage} />
  </Result>
  {action && <Modal title={action.title} close={() => { if (!busy) setAction(undefined) }}>
    <form className="stack" onSubmit={async event => {
      event.preventDefault()
      const form = new FormData(event.currentTarget)
      setBusy(true); setError('')
      try {
        const values = action.notes === undefined ? action.body : { ...action.body, verification_notes: form.get('notes') }
        await apiRequest(`${path}${action.id}/`, payload(action.method, values), token)
        setNotice('Review updated.'); data.refresh(); setAction(undefined)
      } catch (error) { setError(error instanceof Error ? error.message : 'Review could not be updated.') }
      finally { setBusy(false) }
    }}>
      {action.notes !== undefined && <Field label="Verification notes"><textarea name="notes" defaultValue={action.notes} maxLength={2000} rows={4} /></Field>}
      {error && <p role="alert" className="notice error">{error}</p>}
      <div className="row"><button type="button" className="btn outline" disabled={busy} onClick={() => setAction(undefined)}>Cancel</button><button className="btn primary" disabled={busy}>Confirm</button></div>
    </form>
  </Modal>}</>
}
