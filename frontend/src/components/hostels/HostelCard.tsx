import PremiumBadge from '../premium/PremiumBadge'
import { BedDouble, Heart, MapPin } from 'lucide-react'
import { Link } from 'react-router'
import { useState } from 'react'
import { useSession } from '../../contexts/SessionContext'
import { apiRequest, payload } from '../../services/api'
import { beds, dateLabel, money, price } from '../../utils/catalogue'
import type { Hostel } from '../../types/hostel'
import { Badge } from '../common/UI'

export function SaveButton({ hostel, compact = false }: { hostel: Hostel; compact?: boolean }) {
  const { account, token, saved: ids, savedError, refreshSaved } = useSession()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const saved = ids?.includes(hostel.id) ?? false
  const label = saved ? `Remove ${hostel.name} from favourites` : `Save ${hostel.name} to favourites`
  const style = compact ? 'icon-btn save-icon' : 'btn outline'
  if (!account) return <Link className={style} aria-label="Sign in to save hostels" to="/login"><Heart size={18} aria-hidden="true" />{!compact && 'Sign in to save'}</Link>
  if (account.role !== 'student' || !token) return null
  return <><button type="button" className={style} aria-pressed={saved} aria-label={label} disabled={busy || !ids} onClick={async () => {
    setBusy(true)
    setError('')
    try {
      await apiRequest(`saved-hostels/${hostel.id}/`, payload(saved ? 'DELETE' : 'PUT'), token)
      refreshSaved?.()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Could not change saved state.')
    } finally { setBusy(false) }
  }}><Heart size={18} fill={saved ? 'currentColor' : 'none'} aria-hidden="true" />{!compact && (saved ? 'Saved to Favourites' : 'Save to Favourites')}</button>
  {(error || savedError) && <span className="save-error" role="alert">{error || savedError?.message}</span>}</>
}

export function HostelPhoto({ hostel, index = 0, decorative = false }: { hostel: Hostel; index?: number; decorative?: boolean }) {
  const source = hostel.images[index]
  const [failedSource, setFailedSource] = useState<string>()
  return source && source !== failedSource
    ? <img src={source} alt={decorative ? '' : `${hostel.name} photo ${index + 1}`} loading="lazy" onError={() => setFailedSource(source)} />
    : <div className="image-empty" aria-hidden={decorative}><BedDouble aria-hidden="true" />{source ? 'Photo unavailable' : 'No photos yet'}</div>
}

export default function HostelCard({ hostel, base = '/hostels', href, list = false }: { hostel: Hostel; base?: string; href?: string; list?: boolean }) {
  const lowest = price(hostel)
  const period = hostel.rooms.find(room => room.price === lowest)?.billingPeriod ?? 'semester'
  const vacancies = beds(hostel)
  return <article className={list ? 'panel hostel-card list-card' : 'panel hostel-card'}>
    <div className="hostel-photo"><HostelPhoto hostel={hostel} /><SaveButton hostel={hostel} compact /></div>
    <div className="card-body">{hostel.featured && <PremiumBadge>Featured</PremiumBadge>}<h3><Link to={href ?? `${base}/${hostel.id}`}>{hostel.name}</Link></h3>
      <p className="row muted"><MapPin size={15} aria-hidden="true" />{hostel.area}, UCC</p>
      <p className="price">{lowest === null ? 'Price unavailable' : <>{money(lowest)} <small>/ {period}</small></>}</p>
      <div className="row"><Badge success={vacancies > 0}>{vacancies} {vacancies === 1 ? 'bed' : 'beds'} reported</Badge>{hostel.rooms.length > 0 && <Badge>{[...new Set(hostel.rooms.map(room => room.type))].join(', ')}</Badge>}</div>
      {hostel.rooms.some(room => room.stale) && <p className="notice small-text">Availability needs reconfirmation.</p>}
      <p className="muted small-text">{hostel.amenities.join(' · ') || 'Amenities unavailable'}</p>
      <div className="row between card-bottom"><small className="muted">Updated {dateLabel(hostel.updated)}</small><Link className="text-link" to={href ?? `${base}/${hostel.id}`}>View details <span aria-hidden="true">→</span></Link></div>
    </div>
  </article>
}
