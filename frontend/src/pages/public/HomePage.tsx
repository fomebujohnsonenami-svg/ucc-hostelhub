import { ArrowRight, BedDouble, Building2, Check, CirclePlay, Crown, GraduationCap, Heart, MapPin, MessageSquare, Search, Users } from 'lucide-react'
import { Link } from 'react-router'
import HostelCard from '../../components/hostels/HostelCard'
import HostelSearch from '../../components/hostels/HostelSearch'
import { Badge, Empty } from '../../components/common/UI'
import { useApi } from '../../hooks/useApi'
import type { ApiPage } from '../../services/api'
import { asHostel } from '../../services/hostels'
import type { PublicListing } from '../../services/hostels'
import { Result } from '../../components/common/ApiUI'
import { beds } from '../../utils/catalogue'

const highlights = [[GraduationCap, 'For UCC students', 'Explore accommodation near campus'], [Building2, 'Hostel listings', 'Compare rooms and semester prices'], [Users, 'Roommate finder', 'Find students with similar preferences'], [MapPin, 'Around UCC', 'Amamoma, Kwaprow, Apewosika and more']] as const
const questions = [
  ['How do I find a hostel near UCC?', 'Use the hostel directory to filter by area, price, room type, amenities and available beds.'],
  ['How do I contact a hostel manager?', 'Open a hostel listing and select Contact Manager to start a conversation.'],
  ['Can I look for a roommate?', 'Yes. Browse roommate profiles and filter them by area, budget, year and lifestyle preferences.'],
  ['Can I pay for a room through Hostel Hub?', 'Payments are coming soon.'],
]

export default function HomePage() {
  const listings = useApi<ApiPage<PublicListing>>('hostels/?featured=yes&page_size=3')
  const recent = useApi<ApiPage<PublicListing>>(listings.data?.count === 0 ? 'hostels/?page_size=3' : undefined)
  const featured = (listings.data?.count ? listings.data : recent.data)?.results.map(asHostel) ?? []
  const first = featured[0]
  return <>
    <section className="hero">
      <div className="hero-photo" aria-hidden="true" />
      <div className="wrap hero-inner">
        <div className="hero-copy"><Badge>For UCC Students</Badge><h1>Find, Explore and Secure Hostels Around UCC</h1>
          <p>Discover student hostels, check room availability, find compatible roommates, and connect directly with hostel managers—all in one place.</p>
          <div className="row hero-actions"><Link className="btn primary" to="/hostels">Find a Hostel <ArrowRight size={17} /></Link><Link className="btn outline" to="/hostels?view=map"><MapPin size={18} /> Explore Hostel Map</Link><Link className="btn outline" to="/#how-it-works"><CirclePlay size={18} /> How It Works</Link></div>
        </div>
        {first && <div className="hero-callouts"><div className="hero-location"><MapPin size={24} /> <span>Near UCC<br /><small>{first.area}</small></span></div><div className="hero-availability"><BedDouble size={24} /><span>{first.name}<br /><Badge success={beds(first) > 0}>{beds(first)} beds reported</Badge></span></div></div>}
      </div>
    </section>
    <div className="highlight-strip"><div className="wrap highlights">{highlights.map(([Icon, title, text]) => <div className="highlight" key={title}><span className="tile-icon"><Icon size={22} /></span><div><strong>{title}</strong><small>{text}</small></div></div>)}</div></div>
    <section className="wrap section"><div className="section-heading"><div><h2>Find your next hostel</h2><p>Start with a hostel name or location.</p></div></div><HostelSearch />
      <div className="section-heading featured-heading"><div><h2>{listings.data?.count === 0 ? 'Recently updated hostels' : 'Featured hostels'}</h2><p>Explore student accommodation around UCC.</p></div><Link className="text-link" to="/hostels">View all hostels <ArrowRight size={17} /></Link></div>
      <Result loading={listings.loading || recent.loading} error={listings.error ?? recent.error}>{featured.length ? <div className="cards-grid">{featured.map(hostel => <HostelCard key={hostel.id} hostel={hostel} />)}</div> : recent.data && <Empty title="No hostels available" />}</Result>
    </section>
    <section className="section tinted" id="how-it-works"><div className="wrap"><div className="section-heading"><div><h2>How It Works</h2><p>Find accommodation or make your hostel easier to discover.</p></div></div><div className="two-grid">
      <article className="panel info-card"><span className="tile-icon"><GraduationCap /></span><h3>For students</h3><ol><li>Search hostels near UCC.</li><li>Compare prices, availability and amenities.</li><li>Message a manager to ask about a room.</li></ol><Link className="text-link" to="/hostels"><Search size={17} /> Browse hostels</Link></article>
      <article className="panel info-card"><span className="tile-icon"><Building2 /></span><h3>For hostel managers</h3><ol><li>Create a manager profile.</li><li>Add hostel photos and room types.</li><li>Keep availability current and respond to inquiries.</li></ol><Link className="text-link" to="/register?role=manager">Create a manager profile <ArrowRight size={17} /></Link></article>
    </div></div></section>
    <section className="wrap section two-grid"><article className="panel info-card"><span className="tile-icon"><Heart /></span><h3>Student benefits</h3><ul>{['Save favourite hostels as you compare', 'Find roommates with shared preferences', 'Keep hostel inquiries in one place'].map(item => <li key={item}><Check />{item}</li>)}</ul><Link className="text-link" to="/roommates">Find a roommate <ArrowRight size={17} /></Link></article>
      <article className="panel info-card"><span className="tile-icon"><MessageSquare /></span><h3>Hostel manager benefits</h3><ul>{['Update room prices and available beds', 'Organize photos and listing details', 'Manage student messages from your dashboard'].map(item => <li key={item}><Check />{item}</li>)}</ul><Link className="text-link" to="/manager">Explore manager dashboard <ArrowRight size={17} /></Link></article></section>
    <section className="wrap" id="pricing"><div className="premium-banner"><div><Badge>Coming Soon</Badge><h2>Premium hostel listings</h2><p>Explore plans for promoting your hostel around UCC.</p></div><Link className="btn light" to="/pricing"><Crown size={18} /> View Premium Plans</Link></div></section>
    <section className="wrap section faq"><h2>Frequently asked questions</h2>{questions.map(([question, answer]) => <details className="panel" key={question}><summary>{question}</summary><p>{answer}</p></details>)}</section>
  </>
}
