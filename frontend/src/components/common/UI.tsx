import { cloneElement, useEffect, useId, useRef } from 'react'
import type { ReactElement, ReactNode } from 'react'
import { Inbox, X } from 'lucide-react'

export function Heading({ title, text, action }: { title: string; text?: string; action?: ReactNode }) {
  return <div className="page-heading"><div><h1>{title}</h1>{text && <p>{text}</p>}</div>{action}</div>
}

export function Empty({ title, text, action }: { title: string; text?: string; action?: ReactNode }) {
  return <div className="panel empty"><Inbox aria-hidden="true" /><h2>{title}</h2>{text && <p>{text}</p>}{action}</div>
}

export function Badge({ children, success = false }: { children: ReactNode; success?: boolean }) {
  return <span className={success ? 'badge success' : 'badge'}>{children}</span>
}

export function Skeleton() {
  return <div className="cards-grid" role="status" aria-label="Loading">{[1, 2, 3].map(value => <div className="skeleton panel" key={value} />)}</div>
}

export function Field({ label, children }: { label: string; children: ReactElement<{ id?: string }> }) {
  const generated = useId()
  const id = children.props.id ?? generated
  return <div className="field"><label htmlFor={id}>{label}</label>{cloneElement(children, { id })}</div>
}

export function Modal({ title, children, close }: { title: string; children: ReactNode; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    return () => element?.close()
  }, [])
  return <dialog className="dialog panel" ref={dialog} aria-label={title} onCancel={event => { event.preventDefault(); close() }}>
    <div className="row between"><h2>{title}</h2><button className="icon-btn" aria-label="Close dialog" onClick={close}><X size={19} /></button></div>
    {children}
  </dialog>
}
