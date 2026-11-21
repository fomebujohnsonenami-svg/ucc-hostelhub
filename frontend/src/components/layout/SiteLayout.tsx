import { BedDouble, Building2, CircleHelp, ClipboardCheck, Crown, Heart, House, LogOut, Menu, MessageSquare, Settings, ShieldCheck, Users, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router'
import { useSession } from '../../contexts/SessionContext'
import { supabase } from '../../services/supabase'
import ThemeToggle from './ThemeToggle'
import type { Role } from '../../types/hostel'

const publicLinks = [
  ['/', 'Home'], ['/hostels', 'Hostels'], ['/roommates', 'Find Roommate'],
  ['/#how-it-works', 'How It Works'], ['/pricing', 'Pricing'],
]
const roleNavigation = {
  student: [['', 'Dashboard', House], ['/hostels', 'Find Hostels', Building2], ['/roommates', 'Find Roommate', Users], ['/messages', 'Messages', MessageSquare], ['/saved', 'Saved Hostels', Heart], ['/profile', 'Profile Settings', Settings]],
  manager: [['', 'Dashboard', House], ['/hostels', 'My Hostels', Building2], ['/availability', 'Availability', BedDouble], ['/messages', 'Messages', MessageSquare], ['/subscription', 'Hostel Promotion', Crown], ['/profile', 'Profile Settings', Settings]],
  admin: [['', 'Dashboard', House], ['/users', 'User Management', Users], ['/listings', 'Listing Review', Building2], ['/verification', 'Manager Verification', ShieldCheck], ['/moderation', 'Content Moderation', ClipboardCheck]],
} as const

export function Brand() {
  return <Link className="brand" to="/"><span className="brand-mark"><House strokeWidth={2.6} aria-hidden="true" /></span>UCC Hostel Hub</Link>
}

export default function SiteLayout({ role }: { role?: Role }) {
  const [open, setOpen] = useState(false)
  const drawer = useRef<HTMLDialogElement>(null)
  const location = useLocation()
  const navigate = useNavigate()
  const { account, token, loading, error } = useSession()
  const [logoutError, setLogoutError] = useState(false)

  useEffect(() => {
    if (location.hash) {
      const timer = window.setTimeout(() => document.getElementById(location.hash.slice(1))?.scrollIntoView(), 50)
      return () => window.clearTimeout(timer)
    }
    window.scrollTo(0, 0)
  }, [location.pathname, location.hash])

  function closeMenu() { drawer.current?.close(); setOpen(false) }

  async function logout() {
    const result = await supabase?.auth.signOut({ scope: 'local' })
    if (result?.error) { setLogoutError(true); return }
    closeMenu()
    void navigate('/')
  }

  if (!role) return <>
    <a className="skip" href="#main">Skip to content</a>
    <header className="public-header">
      <div className="wrap nav-bar">
        <Brand />
        <div id="public-nav" className={open ? 'public-nav open' : 'public-nav'}>
          <nav aria-label="Main navigation">{publicLinks.map(([to, label]) => to.includes('#') ? <Link key={to} to={to} onClick={closeMenu}>{label}</Link> : <NavLink end key={to} to={to} onClick={closeMenu}>{label}</NavLink>)}</nav>
          <div className="row">{account ? <Link className="btn primary" to={`/${account.role}`} onClick={closeMenu}>My dashboard</Link> : <><Link className="btn outline" to="/login" onClick={closeMenu}>Log in</Link><Link className="btn primary" to="/register" onClick={closeMenu}>Get Started</Link></>}</div>
        </div>
        <ThemeToggle />
        <button className="icon-btn public-menu" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} aria-controls="public-nav" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      </div>
    </header>
    <main id="main" tabIndex={-1}><Outlet /></main>
    <footer className="footer"><div className="wrap footer-grid"><div><Brand /><p>Student accommodation around the University of Cape Coast, Ghana.</p></div><nav aria-label="Footer navigation">{publicLinks.slice(1).map(([to, label]) => <Link key={to} to={to}>{label}</Link>)}</nav><div><strong>Contact & support</strong><p>Cape Coast, Ghana</p><Link to="/help">Visit the help centre</Link></div></div></footer>
  </>

  const menu = <><Brand /><p className="sidebar-role">{role}</p><nav aria-label={`${role} navigation`}>
    {roleNavigation[role].map(([path, label, Icon]) => <NavLink key={path} end={!path} to={`/${role}${path}`} onClick={closeMenu}><Icon size={18} aria-hidden="true" />{label}</NavLink>)}
  </nav><div className="sidebar-end"><Link to={`/${role}/help`} onClick={closeMenu}><CircleHelp size={18} aria-hidden="true" />Help & Support</Link><button onClick={() => void logout()}><LogOut size={18} aria-hidden="true" />Logout</button></div></>
  return <div className="dashboard-shell">
    <a className="skip" href="#main">Skip to content</a>
    <aside className="sidebar">{menu}</aside>
    <dialog className="sidebar-drawer" ref={drawer} aria-label="Dashboard navigation" onClose={() => setOpen(false)} onCancel={closeMenu}><div className="drawer-content"><button className="icon-btn drawer-close" aria-label="Close menu" onClick={closeMenu}><X /></button>{menu}</div></dialog>
    <div className="dashboard-body">
      <header className="dashboard-top"><button className="icon-btn drawer-toggle" aria-label="Open dashboard menu" aria-expanded={open} onClick={() => { drawer.current?.showModal(); setOpen(true) }}><Menu /></button><ThemeToggle /><span className="avatar small" title={account?.full_name ?? role}>{(account?.role === role ? account.full_name : role).slice(0, 2).toUpperCase()}</span></header>
      <main className="dashboard-content" id="main" tabIndex={-1}>
        {logoutError && <p role="alert" className="notice error">Sign-out failed. Try again.</p>}
        {loading ? <p role="status">Checking your session…</p> : account?.role === role ? <Outlet /> :
          <div className="panel padded"><p>{account ? 'This workspace is for a different account role.' : token && error ? 'Your application profile could not be loaded.' : 'Sign in to access this workspace.'}</p>
            <Link className="btn primary" to={account ? `/${account.role}` : '/login'}>{account ? 'Open your dashboard' : 'Sign in'}</Link></div>}
      </main>
    </div>
  </div>
}
