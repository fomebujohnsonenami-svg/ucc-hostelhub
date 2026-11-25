import { useState } from 'react'
import type { ReactNode } from 'react'
import { useApi } from '../hooks/useApi'
import { SessionContext } from './SessionContext'
import type { Account } from './SessionContext'

export default function SessionProvider({ children }: { children: ReactNode }) {
  const [token, updateToken] = useState(() => sessionStorage.getItem('ucc-session') ?? undefined)
  function setToken(next?: string) {
    if (next) sessionStorage.setItem('ucc-session', next)
    else sessionStorage.removeItem('ucc-session')
    updateToken(next)
  }
  const profile = useApi<Account>(token ? 'me/' : undefined, token)
  const saved = useApi<string[]>(profile.data?.role === 'student' ? 'saved-hostels/ids/' : undefined, token)
  return <SessionContext.Provider value={{
    token, setToken, account: profile.data, loading: profile.loading, error: profile.error, refresh: profile.refresh, saved: saved.data, savedError: saved.error, refreshSaved: saved.refresh,
  }}>{children}</SessionContext.Provider>
}
