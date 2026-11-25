import { createContext, useContext } from 'react'
import type { Role } from '../types/hostel'

export type Account = { id: string; full_name: string; username: string; role: Role; phone: string }
type State = { setToken: (token?: string) => void; token?: string; account?: Account; loading: boolean; error?: Error; refresh: () => void; saved?: string[]; savedError?: Error; refreshSaved?: () => void }
export const SessionContext = createContext<State>({ setToken: () => undefined, loading: true, refresh: () => undefined })
export function useSession() { return useContext(SessionContext) }
