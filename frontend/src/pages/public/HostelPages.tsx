import { ArrowLeft, Grid2X2, List, Map as MapIcon, MapPin, Navigation, Search, SlidersHorizontal } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { Badge, Empty, Field, Heading } from '../../components/common/UI'
import HostelCard, { HostelPhoto, SaveButton } from '../../components/hostels/HostelCard'
import PremiumBadge from '../../components/premium/PremiumBadge'
import DiscoveryMap from '../../components/hostels/DiscoveryMap'
import MapView from '../../components/maps/MapView'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import { Paging, Result } from '../../components/common/ApiUI'
import ContactButton from '../../components/common/ContactButton'
import ReportButton from '../../components/common/ReportButton'
import type { ApiPage } from '../../services/api'
import { ApiError } from '../../services/api'
import { approvedHostel, asHostel } from '../../services/hostels'
import type { PublicListing } from '../../services/hostels'
import type { Hostel } from '../../types/hostel'
import { directions } from '../../types/location'
import { areas, beds, dateLabel, money, price, roomTypes } from '../../utils/catalogue'

export function HostelDirectory({ student = false, saved = false }: { student?: boolean; saved?: boolean }) {
  const { token, saved: savedIds } = useSession()
  const [query, setQuery] = useSearchParams()
  const requestedView = query.get('view')
  const view = requestedView === 'map' && !saved ? 'map' : requestedView === 'list' ? 'list' : 'grid'
  function setView(nextView: 'grid' | 'list' | 'map') {
    const next = new URLSearchParams(query)
    if (nextView === 'grid') next.delete('view')
    else next.set('view', nextView)
    setQuery(next)
  }
  function clearFilters() {
    setQuery(view === 'grid' ? {} : { view })
  }
  const [filtersOpen, setFiltersOpen] = useState(false)
  const number = Math.max(1, Number(query.get('page')) || 1)
  const base = student ? '/student/hostels' : '/hostels'
  const q = query.get('q') ?? ''
  const area = query.get('area') ?? ''
  const min = query.get('min') ?? ''
  const max = query.get('max') ?? ''
  const room = query.get('room') ?? ''
  const available = query.get('available') === 'yes'
  const features = query.getAll('amenity')
  const sort = query.get('sort') ?? 'latest'
  const invalid = min !== '' && max !== '' && Number(min) > Number(max)
  const params = new URLSearchParams(query)
  params.delete('view')
  for (const [key, value] of params) if (!value.trim()) params.delete(key)
  const criterion = saved ? `saved-hostels/?page=${number}` : `hostels/?${params}`
  const page = useApi<ApiPage<PublicListing>>(invalid ? undefined : criterion, saved ? token : undefined)
  const promotionParams = new URLSearchParams(params)
  promotionParams.set('featured', 'yes')
  promotionParams.set('page_size', '3')
  promotionParams.delete('page')
  const promoted = useApi<ApiPage<PublicListing>>(!saved && number === 1 && view !== 'map' && !invalid ? `hostels/?${promotionParams}` : undefined)
  const { refresh } = page
  useEffect(() => { if (saved && savedIds) refresh() }, [saved, savedIds, refresh])
  const amenityOptions = useApi<string[]>('amenities/').data ?? []
  const results = page.data?.results.map(asHostel) ?? []
  const filters = useApi<{ areas: string[]; room_types: string[] }>(saved ? undefined : "hostel-filters/")
  const locations = [...new Set([...areas, area, ...(filters.data?.areas ?? [])].filter(Boolean))]
  const roomOptions = [...new Set([...roomTypes, room, ...(filters.data?.room_types ?? [])].filter(Boolean))]
  function change(key: string, value: string) {
    setQuery(previous => {
      const next = new URLSearchParams(previous)
      if (key !== 'page') next.delete('page')
      if (value) next.set(key, value)
      else next.delete(key)
      return next
    }, { replace: true })
  }

  return <div className={student ? '' : 'wrap section'}>
    <Heading title={saved ? 'Saved Hostels' : 'Find Hostels'} text={saved ? 'Keep track of the hostels you want to compare.' : 'Search and compare student accommodation around UCC.'} />
    {!saved && <><div className="row discovery-toolbar"><label className="search-input panel"><Search size={18} /><span className="sr-only">Search hostels</span><input value={q} onChange={event => change('q', event.target.value)} placeholder="Search by hostel name or location" /></label><button className="btn outline filter-toggle" aria-expanded={filtersOpen} aria-controls="hostel-filters" onClick={() => setFiltersOpen(!filtersOpen)}><SlidersHorizontal size={16} /> Filters</button></div>
      <div className={filtersOpen ? 'panel filter-panel open' : 'panel filter-panel'} id="hostel-filters">
        <div className="filter-grid"><Field label="Location"><select value={area} onChange={event => change('area', event.target.value)}><option value="">All areas</option>{locations.map(item => <option key={item}>{item}</option>)}</select></Field>
          <Field label="Minimum price (GH₵)"><input type="number" step=".01" min="0" value={min} onChange={event => change('min', event.target.value)} placeholder="Any" /></Field>
          <Field label="Maximum price (GH₵)"><input type="number" step=".01" min="0" value={max} onChange={event => change('max', event.target.value)} placeholder="Any" /></Field>
          <Field label="Room type"><select value={room} onChange={event => change('room', event.target.value)}><option value="">Any type</option>{roomOptions.map(item => <option key={item}>{item}</option>)}</select></Field></div>
        <fieldset className="checks"><legend>Amenities</legend>{amenityOptions.map(item => <label key={item}><input type="checkbox" checked={features.includes(item)} onChange={event => {
          const checked = event.target.checked
          setQuery(previous => {
            const next = new URLSearchParams(previous)
            next.delete('page')
            if (checked) next.append('amenity', item)
            else next.delete('amenity', item)
            return next
          })
        }} />{item}</label>)}</fieldset>
        <div className="row between"><label className="row"><input type="checkbox" checked={available} onChange={event => change('available', event.target.checked ? 'yes' : '')} /> Available beds only</label><button className="text-link" onClick={clearFilters}>Clear filters</button></div>
      </div></>}
    <Result loading={page.loading} error={page.error} />
    <div className="row between results-bar"><p role="status">{invalid ? 'Minimum price must be less than or equal to maximum price.' : `${page.data?.count ?? 0} ${page.data?.count === 1 ? 'hostel' : 'hostels'}`}</p><div className="row">
      {!saved && <select aria-label="Sort hostels" value={sort} onChange={event => change('sort', event.target.value)}><option value="latest">Latest update</option><option value="low">Price low to high</option><option value="high">Price high to low</option></select>}
      <button className="icon-btn" aria-label="Grid view" aria-pressed={view === 'grid'} onClick={() => setView('grid')}><Grid2X2 size={18} /></button><button className="icon-btn" aria-label="List view" aria-pressed={view === 'list'} onClick={() => setView('list')}><List size={18} /></button>
      {!saved && <button className={view === 'map' ? 'btn primary' : 'btn outline'} aria-pressed={view === 'map'} onClick={() => setView('map')}><MapIcon size={17} /> Map View</button>}
    </div></div>
    {view === 'map' && !invalid && !page.loading && !page.error && <div className="discovery-map-results"><DiscoveryMap hostels={results} base={base} /></div>}
    {!saved && view !== 'map' && Boolean(promoted.data?.results.length) && <section className="panel padded dashboard-gap">
      <div className="section-heading"><h2>Promoted hostels</h2><PremiumBadge>Manager Premium</PremiumBadge></div>
      <div className="row">{promoted.data?.results.map(item => <Link key={item.id} className="btn outline" to={`${base}/${item.id}`}>{item.name} · {item.area}</Link>)}</div>
    </section>}
    {!invalid && !page.loading && !page.error && view !== 'map'  && (results.length ? <div className={view === 'list' ? 'list-stack' : 'cards-grid'}>{results.map(hostel => <HostelCard key={hostel.id} hostel={hostel} list={view === 'list'} base={base} />)}</div>
      : <Empty title={saved ? 'No saved hostels yet' : 'No hostels match your filters'} text={saved ? 'Tap the heart on a listing to save it here.' : 'Try a wider price range or fewer amenities.'} action={saved ? <Link className="btn primary" to={base}>Browse hostels</Link> : <button className="btn outline" onClick={clearFilters}>Reset filters</button>} />)}
    <Paging page={page.data} number={number} change={page => change('page', String(page))} />
  </div>
}

export function HostelDetails({ student = false }: { student?: boolean }) {
  const { id } = useParams()
  const [photo, setPhoto] = useState(0)
  const base = student ? '/student/hostels' : '/hostels'
  const [remote, setRemote] = useState<{ id: string; hostel?: Hostel; error?: boolean }>()
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    if (!id) return
    const controller = new AbortController()
    approvedHostel(id, controller.signal).then(hostel => {
      if (!controller.signal.aborted) setRemote({ id, hostel })
    }).catch(error => {
      if (!controller.signal.aborted) setRemote({ id, error: !(error instanceof ApiError && error.status === 404) })
    })
    return () => controller.abort()
  }, [id, retry])
  const container = student ? '' : 'wrap section'
  const result = remote?.id === id ? remote : undefined
  const hostel = result?.hostel
  if (!hostel) {
    if (!result) return <div className={container}><p role="status">Loading hostel details…</p></div>
    return <div className={container}><Empty title={result.error ? 'Could not load the hostel' : 'Hostel unavailable'} action={result.error ? <button className="btn outline" onClick={() => setRetry(value => value + 1)}>Try again</button> : <Link className="btn outline" to={base}>Back to hostels</Link>} /></div>
  }
  const active = photo < hostel.images.length ? photo : 0
  const destination = hostel.location ? directions(hostel.location) : null
  const lowestRoom = hostel.rooms.find(room => room.price === price(hostel))
  return <div className={student ? '' : 'wrap section'}>
    <Link className="text-link back-link" to={base}><ArrowLeft size={17} /> Back to Hostels</Link>
    <div className="gallery"><div className="gallery-main panel"><HostelPhoto hostel={hostel} index={active} /></div>
      {hostel.images.length > 1 && <div className="gallery-thumbs">{hostel.images.map((image, index) => <button key={`${image}-${index}`} aria-label={`Show photo ${index + 1}`} aria-pressed={active === index} onClick={() => setPhoto(index)}><HostelPhoto hostel={hostel} index={index} decorative /></button>)}</div>}
    </div>
    <div className="detail-grid"><div className="stack"><Heading title={hostel.name} text={hostel.address} action={hostel.featured && <PremiumBadge>Featured</PremiumBadge>} />
      <section className="panel padded"><h2>About this hostel</h2><p>{hostel.description}</p><h3>Amenities</h3><div className="row">{hostel.amenities.map(item => <Badge key={item}>{item}</Badge>)}</div></section>
      <section className="panel padded"><h2>Rooms & Prices</h2>{hostel.rooms.length ? <div className="stack">{hostel.rooms.map(room => <div className="row between room-line" key={room.id}><strong>{room.type}</strong><span>{money(room.price)} / {room.billingPeriod ?? 'semester'}</span><div><Badge success={room.beds > 0 && !room.stale}>{room.beds} beds reported</Badge>{room.availabilityUpdated && <p className="small-text">Confirmed {dateLabel(room.availabilityUpdated)}{room.stale ? ' · Reconfirmation needed' : ''}</p>}</div></div>)}</div> : <p>No room types have been added.</p>}</section>
      <section className="panel padded"><h2>Location &amp; Directions</h2>
        <p className="row"><MapPin size={17} aria-hidden="true" />{hostel.address} · {hostel.area}</p>
        {hostel.location && destination ? <div className="stack">
          <MapView key={hostel.id} label={`Location of ${hostel.name}`} center={hostel.location} pins={[{ id: hostel.id, name: hostel.name, position: hostel.location }]} />
          <div><a className="btn outline" href={destination} target="_blank" rel="noreferrer"><Navigation size={16} /> Get Directions</a></div>
        </div> : <p className="muted">This listing has no confirmed coordinates yet. Use the address to identify the area.</p>}
      </section>
    </div><aside className="panel padded detail-aside"><p className="price">{lowestRoom ? <>{money(lowestRoom.price)} <small>/ {lowestRoom.billingPeriod ?? 'semester'}</small></> : 'Price unavailable'}</p><h3>Availability</h3><Badge success={beds(hostel) > 0}>{beds(hostel)} beds reported</Badge><p className="muted">Availability is reported by the hostel manager. Confirm with the manager before making plans.</p>
      <div className="stack"><ContactButton target="hostel" id={hostel.id} label="Contact Manager" /><SaveButton hostel={hostel} /><ReportButton target="hostel" id={hostel.id} /></div>
    </aside></div>
  </div>
}
