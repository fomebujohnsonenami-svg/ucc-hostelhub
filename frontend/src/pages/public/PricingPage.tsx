import { useState } from 'react'
import { Link } from 'react-router'
import { Check, Clock3 } from 'lucide-react'
import { Empty, Heading } from '../../components/common/UI'
import { Result } from '../../components/common/ApiUI'
import PaymentPreview from '../../components/premium/PaymentPreview'
import PremiumBadge from '../../components/premium/PremiumBadge'
import { useApi } from '../../hooks/useApi'
import { showPresentationUI } from '../../services/premium'
import type { Catalogue, Plan } from '../../services/premium'
import { money } from '../../utils/catalogue'

const freeFeatures = {
  student: ['Browse, search and filter hostel listings', 'View photos, availability, locations and directions', 'Save favourite hostels', 'Browse roommate profiles and manage your own', 'Manage account settings'],
  manager: ['Create and edit hostel listings', 'Upload photos and set hostel locations', 'Manage room types, prices and availability', 'View and reply to student inquiries', 'Access the manager dashboard'],
}

export default function PricingPage({ student = false }: { student?: boolean }) {
  const catalogue = useApi<Catalogue>('subscription-plans/')
  const [selected, setSelected] = useState<Plan>()
  const plans = catalogue.data?.plans.filter(plan => !student || plan.audience === 'student')
  const notice = showPresentationUI && catalogue.data?.access_mode === 'presentation' ? 'University presentation mode is active.' : 'Launch preview'
  return <div className="wrap section pricing-page">
    <Heading title={student ? "Student Premium" : "Premium plans"} text={student ? "Message hostel managers and potential roommates." : "Explore messaging for students and listing promotion for hostel managers."} />
    <div className="notice pricing-notice"><strong>{notice}</strong><p>Premium features are open during the preview. Payments are coming soon.</p></div>
    <Result loading={catalogue.loading} error={catalogue.error}>
      {catalogue.error && <button className="btn outline" onClick={catalogue.refresh}>Retry loading plans</button>}
      {plans?.length === 0 && <Empty title="No plans are available to display" />}
      <div className="two-grid pricing-grid">{plans?.map(plan => <article className="panel padded pricing-card" key={plan.audience}>
        <div><PremiumBadge>{plan.audience === 'student' ? 'Student Premium' : 'Manager Premium'}</PremiumBadge><h2>{plan.name}</h2>
          <p className="plan-price"><strong>{money(Number(plan.price))}</strong> <small>/ month</small></p>
          <h3>Premium benefits</h3><ul>{plan.features.map(item => <li key={item}><Check size={16} aria-hidden="true" />{item}</li>)}</ul></div>
        <div><h3>Always free</h3><ul>{freeFeatures[plan.audience].map(item => <li key={item}><Check size={16} aria-hidden="true" />{item}</li>)}</ul>
          <div className="row"><button className="btn outline" onClick={() => setSelected(plan)}><Clock3 size={16} /> Upgrade to Premium</button>
            <Link className="btn primary" to={plan.audience === 'student' ? (student ? '/student/messages' : '/hostels') : '/manager/subscription'}>{plan.audience === 'student' ? (student ? 'Open messages' : 'Explore hostels') : 'Open promotion tools'}</Link></div></div>
      </article>)}</div>
    </Result>
    {selected && <PaymentPreview plan={selected} close={() => setSelected(undefined)} />}
  </div>
}
