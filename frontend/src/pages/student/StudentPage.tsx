import { ArrowRight, BedDouble, Heart, MessageSquare, Users } from 'lucide-react'
import { Link } from 'react-router'
import { Empty, Heading } from '../../components/common/UI'
import { Result } from '../../components/common/ApiUI'
import HostelCard from '../../components/hostels/HostelCard'
import HostelSearch from '../../components/hostels/HostelSearch'
import type { Conversation } from '../../components/messaging/Messages'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import type { ApiPage } from '../../services/api'
import { asHostel } from '../../services/hostels'
import type { PublicListing } from '../../services/hostels'

type Dashboard = { saved: number; conversations: number; recommended: PublicListing[] }

export default function StudentPage() {
  const { account, token, saved } = useSession()
  const dashboard = useApi<Dashboard>('dashboard/student/', token)
  const conversations = useApi<ApiPage<Conversation>>('conversations/?page_size=3', token, 5000)
  const actions = [
    [BedDouble, 'Find Hostels', 'Browse accommodation around UCC', '/student/hostels'],
    [Users, 'Find Roommate', 'Meet fellow students', '/student/roommates'],
    [MessageSquare, 'My Messages', dashboard.data ? `${dashboard.data.conversations} active conversations` : 'Open your conversations', '/student/messages'],
    [Heart, 'Saved Hostels', saved ? `${saved.length} saved` : dashboard.data ? `${dashboard.data.saved} saved` : 'Open your favourites', '/student/saved'],
  ] as const
  return <><Heading title={`Welcome, ${account?.full_name.split(' ')[0] ?? 'student'}`} text="Find a hostel or roommate around UCC." />
    <HostelSearch destination="/student/hostels" /><div className="action-grid">{actions.map(([Icon, title, description, path]) =>
      <Link className="panel action-card" to={path} key={path}><span className="tile-icon"><Icon size={20} /></span><strong>{title}</strong><small>{description}</small></Link>)}</div>
    <div className="section-heading compact"><h2>Recommended Hostels for You</h2><Link className="text-link" to="/student/hostels">View all <ArrowRight size={16} /></Link></div>
    <Result loading={dashboard.loading} error={dashboard.error}>
      {dashboard.data?.recommended.length === 0 && <Empty title="No listed hostels" />}
      <div className="cards-grid">{dashboard.data?.recommended.map(item => <HostelCard key={item.id} hostel={asHostel(item)} base="/student/hostels" />)}</div>
    </Result>
    <section className="panel padded dashboard-gap"><div className="row between"><h2>Recent Conversations</h2><Link className="text-link" to="/student/messages">View all</Link></div>
      <Result loading={conversations.loading} error={conversations.error}>{conversations.data?.results.length === 0 && <p>No conversations yet.</p>}
        {conversations.data?.results.map(item => <Link className="simple-row" key={item.id} to={`/student/messages/${item.id}`}>{item.name}{item.unread > 0 && <BadgeCount unread={item.unread} />}</Link>)}
      </Result>
    </section>
  </>
}

function BadgeCount({ unread }: { unread: number }) { return <span className="count" aria-label={`${unread} unread`}>{unread}</span> }
