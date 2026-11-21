import { BedDouble, Building2, CalendarDays, Crown, MessageSquare, Plus } from 'lucide-react'
import { Link } from 'react-router'
import PremiumBadge from '../../components/premium/PremiumBadge'
import { Heading } from '../../components/common/UI'
import { Result } from '../../components/common/ApiUI'
import type { Conversation } from '../../components/messaging/Messages'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import type { ApiPage } from '../../services/api'

export default function ManagerPage() {
  const { token } = useSession()
  const data = useApi<{ hostels: number; rooms: number; beds: number; inquiries: number }>('dashboard/manager/', token)
  const recent = useApi<ApiPage<Conversation>>('conversations/?page_size=5', token, 5000)
  const stats = [[Building2, 'My Hostels', 'hostels'], [BedDouble, 'Total Rooms', 'rooms'], [BedDouble, 'Available Beds Reported', 'beds'], [MessageSquare, 'Student Inquiries', 'inquiries']] as const
  return <><Heading title="Manager Dashboard" text="Manage hostel listings, availability, and student inquiries." />
    <Result loading={data.loading} error={data.error}>
      <div className="action-grid">{stats.map(([Icon, label, key]) => <div className="panel action-card" key={key}><span className="tile-icon"><Icon size={20} /></span><strong className="stat-value">{data.data?.[key] ?? '—'}</strong><small>{label}</small></div>)}</div>
    </Result>
    <div className="two-grid dashboard-gap"><section className="panel padded"><h2>Recent Inquiries</h2>
      <Result loading={recent.loading} error={recent.error}>{recent.data?.results.length === 0 && <p>No inquiries yet.</p>}{recent.data?.results.map(item =>
        <Link className="simple-row" key={item.id} to={`/manager/messages/${item.id}`}>{item.name}{item.unread > 0 && <span className="count">{item.unread} unread</span>}</Link>)}</Result>
    </section><section className="panel padded"><h2>Quick Actions</h2><div className="stack">
      <Link className="quick-link" to="/manager/hostels/new"><Plus size={17} /> Add New Hostel</Link>
      <Link className="quick-link" to="/manager/availability"><CalendarDays size={17} /> Update Availability</Link>
      <Link className="quick-link" to="/manager/messages"><MessageSquare size={17} /> View Messages</Link>
      <Link className="quick-link" to="/manager/subscription"><Crown size={17} /> Hostel Promotion <PremiumBadge /></Link>
    </div></section></div>
  </>
}
