import type { ReactNode } from 'react'
import { useManagerSession } from '../hooks/useManagerSession'
import { useApi } from '../hooks/useApi'
import { SessionContext } from './SessionContext'
import type { Account } from './SessionContext'

export default function SessionProvider({ children }: { children: ReactNode }) {
  const session = useManagerSession()
  const token = session?.access_token
  const profile = useApi<Account>(token ? 'me/' : undefined, token)
  const saved = useApi<string[]>(profile.data?.role === 'student' ? 'saved-hostels/ids/' : undefined, token)
  return <SessionContext.Provider value={{
    token, account: profile.data, loading: session === undefined || profile.loading, error: profile.error, refresh: profile.refresh, saved: saved.data, savedError: saved.error, refreshSaved: saved.refresh,
  }}>{children}</SessionContext.Provider>
}
