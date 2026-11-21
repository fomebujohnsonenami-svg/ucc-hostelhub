import { createContext, useContext } from 'react'
import type { Role } from '../types/hostel'

export type Account = { id: string; full_name: string; username: string; role: Role; phone: string }
type State = { token?: string; account?: Account; loading: boolean; error?: Error; refresh: () => void; saved?: string[]; savedError?: Error; refreshSaved?: () => void }
export const SessionContext = createContext<State>({ loading: true, refresh: () => undefined })
export function useSession() { return useContext(SessionContext) }
