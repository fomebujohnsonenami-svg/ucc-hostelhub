import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL?.trim()
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY?.trim()
function managerClient() {
  if (!url || !key) return null
  try {
    return createClient(url, key)
  } catch {
    return null
  }
}

export const supabase = managerClient()
