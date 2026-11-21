import type { ReactNode } from 'react'
import type { ApiPage } from '../../services/api'

export function Result({ loading, error, children }: { loading?: boolean; error?: Error; children?: ReactNode }) {
  return <>{loading && <p role="status">Loading…</p>}{error && <p className="notice error" role="alert">{error.message}</p>}{children}</>
}

export function Paging<T>({ page, number, change }: { page?: ApiPage<T>; number: number; change: (page: number) => void }) {
  if (!page || (!page.previous && !page.next)) return null
  return <nav className="row between" aria-label="Results pages">
    <button className="btn outline" disabled={!page.previous} onClick={() => change(number - 1)}>Previous page</button>
    <span>Page {number}</span>
    <button className="btn outline" disabled={!page.next} onClick={() => change(number + 1)}>Next page</button>
  </nav>
}
