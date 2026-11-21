import { ArrowLeft, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import { apiRequest, payload } from '../../services/api'
import type { ApiPage } from '../../services/api'
import { Empty, Heading } from '../common/UI'
import { Paging, Result } from '../common/ApiUI'
import ReportButton from '../common/ReportButton'
import PremiumBadge from '../premium/PremiumBadge'
import { showPresentationUI } from '../../services/premium'
import type { Catalogue } from '../../services/premium'

export type Conversation = { id: string; name: string; unread: number; conversation_type: string; updated_at: string }
type Message = { id: string; body: string; sent: boolean; created_at: string }
const polling = 5000

export default function Messages({ role }: { role: 'student' | 'manager' }) {
  const { token } = useSession()
  const { id } = useParams()
  const [page, setPage] = useState(1)
  const list = useApi<ApiPage<Conversation>>(`conversations/?page=${page}`, token, polling)
  const base = `/${role}/messages`
  const premium = useApi<Catalogue>(role === 'student' && showPresentationUI ? 'subscription-plans/' : undefined)
  return <><Heading title="Messages" text="Conversations are private to their participants." action={role === 'student' && <PremiumBadge>Student Premium</PremiumBadge>} />
    {role === 'student' && <div className="notice premium-notice row between">
      <p>Premium Feature — Messaging is available to everyone during our launch preview.{premium.data?.access_mode === 'presentation' && ' University presentation mode is active.'}</p>
      <Link className="text-link" to="/pricing">View Premium Plans</Link>
    </div>}
    <div className={id ? 'panel message-layout has-thread' : 'panel message-layout'}>
      <div className="conversation-list"><h2>Conversations</h2><Result loading={list.loading} error={list.error}>
        {list.data?.results.length === 0 && <p>No conversations yet.</p>}
        {list.data?.results.map(item => <Link key={item.id} className={item.id === id ? 'conversation active' : 'conversation'} aria-current={item.id === id ? 'page' : undefined} to={`${base}/${item.id}`}>
          <span className="avatar small" aria-hidden="true">{item.name.slice(0, 2).toUpperCase()}</span><span><strong>{item.name}</strong><small>{item.conversation_type === 'hostel' ? 'Hostel inquiry' : 'Roommate inquiry'}</small></span>
          {item.unread > 0 && <span className="count" aria-label={`${item.unread} unread`}>{item.unread}</span>}
        </Link>)}
        <Paging page={list.data} number={page} change={setPage} />
      </Result></div>
      {id && token ? <Thread key={id} id={id} token={token} base={base} onRead={list.refresh} /> : <div className="thread-placeholder"><Empty title="Select a conversation" text="Choose a conversation to read or send a message." /></div>}
    </div>
  </>
}

function Thread({ id, token, base, onRead }: { id: string; token: string; base: string; onRead: () => void }) {
  const [page, setPage] = useState(1)
  const [draft, setDraft] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [readError, setReadError] = useState(false)
  const thread = useRef<HTMLDivElement>(null)
  const lastRead = useRef('')
  const path = `conversations/${id}/`
  const detail = useApi<Conversation>(path, token)
  const messages = useApi<ApiPage<Message>>(`${path}messages/?page=${page}`, token, page === 1 ? polling : undefined)
  const newest = messages.data?.results[0]?.id

  useEffect(() => {
    if (page !== 1 || !newest || lastRead.current === newest) return
    const controller = new AbortController()
    void apiRequest(`${path}read/`, { ...payload('POST', { message: newest }), signal: controller.signal }, token).then(() => {
      if (controller.signal.aborted) return
      lastRead.current = newest
      setReadError(false)
      onRead()
    }).catch(() => { if (!controller.signal.aborted) setReadError(true) })
    return () => controller.abort()
  }, [page, newest, path, token, onRead, messages.data])

  useEffect(() => {
    if (page === 1 && thread.current) thread.current.scrollTop = thread.current.scrollHeight
  }, [newest, page])

  return <div className="thread">
    <div className="thread-head"><Link className="icon-btn thread-back" to={base} aria-label="Back to conversations"><ArrowLeft size={18} /></Link><h2>{detail.data?.name ?? 'Conversation'}</h2></div>
    <div className="message-scroll" ref={thread}><Result loading={messages.loading} error={messages.error}>
      {readError && <p role="status">Read status could not be updated. Retrying.</p>}
      <Paging page={messages.data} number={page} change={setPage} />
      {messages.data?.results.length === 0 && <Empty title="Start the conversation" />}
      {[...(messages.data?.results ?? [])].reverse().map(message => <article key={message.id} className={message.sent ? 'bubble sent' : 'bubble'}>
        <p>{message.body}</p><small>{message.sent ? 'You' : detail.data?.name ?? 'Participant'} · <time dateTime={message.created_at}>{new Date(message.created_at).toLocaleString()}</time></small>
        {!message.sent && <div><ReportButton target="message" id={message.id} /></div>}
      </article>)}
    </Result></div>
    {detail.error && <p className="notice error" role="alert">{detail.error.message}</p>}
    {detail.data && <form className="composer" onSubmit={async event => {
      event.preventDefault()
      if (!draft.trim() || busy) return
      setBusy(true); setError('')
      try {
        await apiRequest(`${path}messages/`, payload('POST', { body: draft }), token)
        setDraft(''); setPage(1); messages.refresh()
      } catch (error) { setError(error instanceof Error ? error.message : 'Message could not be sent.') }
      finally { setBusy(false) }
    }}><label className="sr-only" htmlFor="message-draft">Message</label><textarea id="message-draft" rows={2} maxLength={2000} value={draft} onChange={event => setDraft(event.target.value)} placeholder="Write a message…" />
      <button className="btn primary" disabled={busy || !draft.trim()}><Send size={17} /> Send</button>
      {error && <p role="alert" className="notice error">{error}</p>}
    </form>}
  </div>
}
