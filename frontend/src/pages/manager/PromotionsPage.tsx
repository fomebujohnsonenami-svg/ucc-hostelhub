import { useState } from 'react'
import { Link } from 'react-router'
import { Heading, Empty } from '../../components/common/UI'
import { Paging, Result } from '../../components/common/ApiUI'
import PaymentPreview from '../../components/premium/PaymentPreview'
import PremiumBadge from '../../components/premium/PremiumBadge'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import { apiRequest, payload } from '../../services/api'
import type { ApiPage } from '../../services/api'

type Promotion = { id: string; name: string; area: string; eligible: boolean; featured: boolean; inquiries: number }
const endpoint = 'manager/promotions/'

export default function PromotionsPage() {
  const { token } = useSession()
  const [upgradeOpen, setUpgradeOpen] = useState(false)
  const [number, setNumber] = useState(1)
  const [pending, setPending] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const promotions = useApi<ApiPage<Promotion>>(`${endpoint}?page=${number}`, token)

  async function toggle(listing: Promotion) {
    setPending(listing.id); setNotice(''); setError('')
    try {
      await apiRequest(`${endpoint}${listing.id}/`, payload('PATCH', { featured: !listing.featured }), token)
      promotions.refresh()
      setNotice(listing.featured ? 'Listing removed from featured placement.' : 'Listing added to featured placement.')
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not update placement.') }
    finally { setPending('') }
  }

  return <><Heading title="Hostel Promotion" action={<PremiumBadge>Manager Premium</PremiumBadge>} text="Feature approved listings and see how many inquiry conversations each hostel has received." />
    <section className="premium-banner"><div><h2>Premium promotion preview</h2><p>Featured placement and inquiry analytics are available now. Payments are coming soon.</p></div><div className="row"><button className="btn light" onClick={() => setUpgradeOpen(true)}>Upgrade to Premium</button><Link className="btn light" to="/pricing">View premium plans</Link></div></section>
    {upgradeOpen && <PaymentPreview close={() => setUpgradeOpen(false)} />}
    <div className="stack dashboard-gap"><Result loading={promotions.loading} error={promotions.error}>
      {notice && <p role="status" className="notice">{notice}</p>}{error && <p role="alert" className="notice error">{error}</p>}
      {promotions.data?.results.length === 0 && <Empty title="No listings to promote" action={<Link className="btn primary" to="/manager/hostels/new">Add a hostel</Link>} />}
      {promotions.data?.results.map(listing => <article key={listing.id} className="panel padded row between">
        <div><h2>{listing.name}</h2><p>{listing.area} · {listing.inquiries} {listing.inquiries === 1 ? 'inquiry' : 'inquiries'}</p>
          {listing.eligible && listing.featured ? <PremiumBadge>Featured</PremiumBadge> : !listing.eligible && <small>Approval and publication are required for featured placement.</small>}</div>
        {(listing.eligible || listing.featured) && <button className="btn outline" aria-pressed={listing.featured} disabled={Boolean(pending)} onClick={() => void toggle(listing)}>{listing.featured ? 'Remove from featured' : 'Feature listing'}</button>}
      </article>)}
      <Paging page={promotions.data} number={number} change={setNumber} />
    </Result></div>
  </>
}
