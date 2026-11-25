import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL?.trim()
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY?.trim()
function managerClient() {
  if (!url || !key) return null
  try {
    // Supabase can fall back to the configured Site URL after OAuth.
    // Keep the authorization code intact so the client can exchange it.
    const callback = new URL(window.location.href)
    const params = callback.searchParams
    const fragment = new URLSearchParams(callback.hash.slice(1))
    if (callback.pathname === '/' &&
        (params.has('code') || params.has('error_code') || fragment.has('error_code'))) {
      callback.pathname = '/login'
      params.set('auth_return', '1')
      window.history.replaceState(window.history.state, '', callback)
    }
    return createClient(url, key, { auth: { flowType: 'pkce' } })
  } catch {
    return null
  }
}

export const supabase = managerClient()
