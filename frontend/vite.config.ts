import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

function isPublicSupabaseKey(key: string) {
  if (key.startsWith('sb_publishable_')) return true
  const parts = key.split('.')
  if (parts.length !== 3) return false
  try {
    const claims = JSON.parse(Buffer.from(parts[1], 'base64url').toString('utf8'))
    return claims?.role === 'anon'
  } catch {
    return false
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const key = env.VITE_SUPABASE_PUBLISHABLE_KEY?.trim()
  if (key && !isPublicSupabaseKey(key)) {
    throw new Error('VITE_SUPABASE_PUBLISHABLE_KEY must be a publishable or legacy anon key.')
  }
  return {
    plugins: [react(), tailwindcss()],
    server: { port: 5173, strictPort: true },
  }
})
