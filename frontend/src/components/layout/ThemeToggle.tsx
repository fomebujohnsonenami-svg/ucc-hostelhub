import { Moon, Sun } from 'lucide-react'
import { useState } from 'react'

export default function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === 'dark')
  const Icon = dark ? Sun : Moon
  const label = dark ? 'Switch to light mode' : 'Switch to dark mode'

  return <button type="button" className="icon-btn theme-toggle" aria-label={label} title={label} onClick={() => {
    const theme = dark ? 'light' : 'dark'
    document.documentElement.dataset.theme = theme
    setDark(!dark)
    try { localStorage.setItem('ucc-hostelhub-theme', theme) } catch { /* The theme still applies for this visit. */ }
  }}><Icon size={18} aria-hidden="true" /></button>
}
