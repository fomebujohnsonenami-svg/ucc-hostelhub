import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router'
import { Badge, Empty, Field, Heading, Modal } from '../../components/common/UI'
import { Paging, Result } from '../../components/common/ApiUI'
import LocationPicker from '../../components/maps/LocationPicker'
import type { LocationInput } from '../../components/maps/LocationPicker'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import { apiRequest, apiUrl, payload } from '../../services/api'
import type { ApiPage } from '../../services/api'
import { saveManagerHostel } from '../../services/hostels'
import type { ApiRoom, ManagerListing } from '../../services/hostels'
import MapView from '../../components/maps/MapView'
import { coordinates } from '../../types/location'
import { dateLabel, money } from '../../utils/catalogue'

const base = 'manager/hostels/'
const url = '/manager/hostels'
function errorText(error: unknown) { return error instanceof Error ? error.message : 'The operation could not be completed.' }

export function ManagerListings({ availability = false }: { availability?: boolean }) {
  const { token } = useSession()
  const { state } = useLocation()
  const [page, setPage] = useState(1)
  const listings = useApi<ApiPage<ManagerListing>>(`${base}?page=${page}`, token)
  const [remove, setRemove] = useState<ManagerListing>()
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  async function mutate(hostel: ManagerListing, action: string) {
    setBusy(true); setError(''); setNotice('')
    try {
      if (action === 'delete') await apiRequest(`${base}${hostel.id}/`, payload('DELETE', { confirm: true }), token)
      else await apiRequest(`${base}${hostel.id}/publication/`, payload('POST', { action }), token)
      setRemove(undefined)
      setNotice(action === 'delete' ? 'Listing deleted.' : 'Publication status updated.')
      if (action === 'delete' && page > 1 && listings.data?.results.length === 1) setPage(page - 1)
      else listings.refresh()
    } catch (error) { setError(errorText(error)) } finally { setBusy(false) }
  }

  return <><Heading title={availability ? 'Availability' : 'My Hostels'} text={availability ? 'Confirm the number of beds your hostel is offering.' : 'Manage your hostel listings, rooms, photos, and publication.'} action={!availability && <Link className="btn primary" to={`${url}/new`}>Add Hostel</Link>} />
    <Result loading={listings.loading} error={listings.error}>
      {(notice || state?.notice) && <p role="status" className="notice">{notice || state.notice}</p>}
      {error && <p role="alert" className="notice error">{error}</p>}
      {listings.data?.results.length === 0 && <Empty title="No hostels yet" />}
      <div className="stack">{listings.data?.results.map(hostel => {
        const action = hostel.publication_status === 'published' ? 'unpublish' : hostel.verification_status !== 'rejected' && ['draft', 'pending'].includes(hostel.publication_status) ? 'publish' : null
        return <article className="panel padded" key={hostel.id}><div className="row between">
          <div><h2>{hostel.name}</h2><p>{hostel.area}</p><Badge>{hostel.publication_status === 'hidden' ? 'Suspended' : hostel.publication_status === 'pending' ? 'Ready to publish' : hostel.publication_status}</Badge></div>
          <div className="row">{availability ? <Link className="btn primary" to={`${url}/${hostel.id}/availability`}>Update Availability</Link> : <>
            <Link className="btn outline" to={`${url}/${hostel.id}/edit`}>Edit Hostel</Link>
            <Link className="btn outline" to={`${url}/${hostel.id}/rooms`}>Room Types</Link>
            <Link className="btn outline" to={`${url}/${hostel.id}/photos`}>Photos</Link>
            {action && <button className="btn outline" disabled={busy} onClick={() => void mutate(hostel, action)}>{action === 'publish' ? 'Publish' : 'Unpublish'}</button>}
            <Link className="text-link" to={`${url}/${hostel.id}/preview`}>Preview listing</Link>
            <button className="btn outline" disabled={busy} onClick={() => setRemove(hostel)}>Delete</button>
          </>}</div></div></article>
      })}</div>
      <Paging page={listings.data} number={page} change={setPage} />
    </Result>
    {remove && <Modal title="Delete hostel?" close={() => { if (!busy) setRemove(undefined) }}><p>Delete {remove.name}, its rooms and photos?</p>
      {error && <p role="alert">{error}</p>}<div className="row"><button className="btn outline" disabled={busy} onClick={() => setRemove(undefined)}>Cancel</button><button className="btn destructive" disabled={busy} onClick={() => void mutate(remove, 'delete')}>Delete hostel</button></div></Modal>}
  </>
}

export function ManagerHostelPage({ mode }: { mode: 'new' | 'edit' | 'rooms' | 'availability' | 'photos' | 'preview' }) {
  const { id } = useParams()
  const { token } = useSession()
  const listing = useApi<ManagerListing>(id ? `${base}${id}/` : undefined, token)
  return <Result loading={listing.loading} error={listing.error}>
    {token && mode === 'new' && <ListingEditor token={token} />}
    {token && listing.data && (mode === 'edit' ? <ListingEditor key={id} hostel={listing.data} token={token} /> : mode === 'preview' ? <ListingPreview hostel={listing.data} token={token} /> : mode === 'photos' ?
      <PhotoEditor hostel={listing.data} token={token} refresh={listing.refresh} /> :
      <RoomEditor hostel={listing.data} token={token} refresh={listing.refresh} availability={mode === 'availability'} />)}
  </Result>
}

function ListingEditor({ hostel, token }: { hostel?: ManagerListing; token: string }) {
  const [location, setLocation] = useState<LocationInput>({ latitude: hostel?.latitude ?? '', longitude: hostel?.longitude ?? '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const amenities = useApi<string[]>('amenities/')
  const navigate = useNavigate()
  return <><Heading title={hostel ? 'Edit Hostel' : 'Add Hostel'} text={hostel ? undefined : "Your listing goes live when you save it. You can add photos later."} /><form className="panel padded stack form-width" onSubmit={async event => {
    event.preventDefault()
    if (busy) return
    const point = coordinates(location.latitude, location.longitude)
    if ((location.latitude || location.longitude) && !point) { setError('Enter both coordinates within range or clear both.'); return }
    const data = new FormData(event.currentTarget)
    setBusy(true); setError('')
    try {
      const saved = await saveManagerHostel(hostel?.id, token, {
        name: String(data.get('name')), area: String(data.get('area')), address: String(data.get('address')),
        description: String(data.get('description')), amenities: amenities.data ? data.getAll('amenities').map(String) : hostel?.amenities ?? [],
      }, point)
      void navigate(hostel ? url : `${url}/${saved.id}/rooms`, { state: { notice: hostel ? 'Listing saved.' : 'Listing published. Add room types and prices below.' } })
    } catch (error) { setError(errorText(error)) } finally { setBusy(false) }
  }}>
    <Field label="Hostel name"><input name="name" required maxLength={160} defaultValue={hostel?.name} /></Field>
    <div className="two-grid"><Field label="Area"><input name="area" required maxLength={100} defaultValue={hostel?.area} /></Field>
      <Field label="Address or landmark"><input name="address" required maxLength={250} defaultValue={hostel?.address} /></Field></div>
    <Field label="Description"><textarea name="description" required maxLength={5000} rows={5} defaultValue={hostel?.description} /></Field>
    <Result loading={amenities.loading} error={amenities.error}><fieldset className="checks"><legend>Amenities</legend>{amenities.data?.map(item =>
      <label key={item}><input type="checkbox" name="amenities" value={item} defaultChecked={hostel?.amenities.includes(item)} />{item}</label>)}</fieldset></Result>
    <LocationPicker value={location} onChange={setLocation} />
    {error && <p className="notice error" role="alert">{error}</p>}
    <div className="row"><button className="btn primary" disabled={busy}>{busy ? 'Saving…' : 'Save Hostel'}</button><Link className="btn outline" to={url}>Cancel</Link></div>
  </form></>
}

function RoomEditor({ hostel, token, refresh, availability }: { hostel: ManagerListing; token: string; refresh: () => void; availability: boolean }) {
  const { state } = useLocation()
  const [selected, setSelected] = useState<ApiRoom | 'new' | null>(null)
  const [remove, setRemove] = useState<ApiRoom>()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const path = `${base}${hostel.id}/rooms/`
  const room = selected === 'new' ? null : selected

  async function mutate(endpoint: string, method: string, values: unknown) {
    setBusy(true); setError(''); setNotice('')
    try {
      await apiRequest(endpoint, payload(method, values), token)
      setNotice(method === 'DELETE' ? 'Room type deleted.' : availability ? 'Availability confirmed.' : 'Room type saved.')
      refresh(); setRemove(undefined); setSelected(null)
    } catch (error) { setError(errorText(error)) } finally { setBusy(false) }
  }
  return <><Heading title={availability ? 'Update Availability' : 'Manage Room Types'} text={hostel.name} action={!availability && <button className="btn primary" onClick={() => { setSelected('new'); setError('') }}>Add Room Type</button>} />
    {(notice || state?.notice) && <p role="status" className="notice">{notice || state.notice}</p>}
    {!hostel.room_types.length && <Empty title="No room types yet" action={availability && <Link className="btn outline" to={`${url}/${hostel.id}/rooms`}>Manage room types</Link>} />}
    <div className="stack">{hostel.room_types.map(item => <article className="panel padded row between" key={item.id}><div><h2>{item.name}</h2>
      <p>{money(Number(item.price_per_bed))} / {item.billing_period} · {item.available_beds} of {item.total_capacity} beds reported</p>
      <p>Confirmed {dateLabel(item.availability_updated_at)}{item.availability_stale && ' · Reconfirmation needed'}</p></div>
      <div className="row"><button className="btn outline" onClick={() => { setSelected(item); setError('') }}>{availability ? 'Update beds' : 'Edit room'}</button>
      {!availability && <button className="btn outline" onClick={() => { setRemove(item); setError('') }}>Delete room</button>}</div></article>)}</div>
    {selected && <Modal title={availability ? 'Confirm availability' : room ? 'Edit room type' : 'Add room type'} close={() => { if (!busy) setSelected(null) }}>
      <form className="stack" onSubmit={event => {
        event.preventDefault()
        const data = new FormData(event.currentTarget)
        const available_beds = Number(data.get('beds'))
        const fields = availability ? { available_beds } : { available_beds, name: data.get('name'), capacity: Number(data.get('capacity')), total_rooms: Number(data.get('rooms')), price_per_bed: data.get('price') }
        void mutate(room ? `${path}${room.id}/` : path, room ? 'PATCH' : 'POST', fields)
      }}>
        {!availability && <><Field label="Room type"><input name="name" required maxLength={100} defaultValue={room?.name} /></Field>
          <Field label="Beds per room"><input name="capacity" type="number" min="1" required defaultValue={room?.capacity} /></Field>
          <Field label="Total rooms"><input name="rooms" type="number" min="0" required defaultValue={room?.total_rooms} /></Field>
          <Field label={room && room.billing_period !== 'semester' ? `Price per ${room.billing_period} (GHS)` : 'Price per semester (GHS)'}><input name="price" type="number" min="0" step=".01" required defaultValue={room?.price_per_bed} /></Field></>}
        <Field label="Available beds"><input name="beds" type="number" min="0" max={availability ? room?.total_capacity : undefined} required defaultValue={room?.available_beds ?? 0} /></Field>
        {error && <p role="alert" className="notice error">{error}</p>}<button className="btn primary" disabled={busy}>Save changes</button>
      </form></Modal>}
    {remove && <Modal title="Delete room type?" close={() => { if (!busy) setRemove(undefined) }}><p>Delete {remove.name} and its availability?</p>
      {error && <p role="alert">{error}</p>}<div className="row"><button className="btn outline" disabled={busy} onClick={() => setRemove(undefined)}>Cancel</button><button className="btn destructive" disabled={busy} onClick={() => void mutate(`${path}${remove.id}/`, 'DELETE', { confirm: true })}>Delete room type</button></div></Modal>}
  </>
}

function PrivatePhoto({ path, token }: { path: string; token: string }) {
  const [result, setResult] = useState<{ image?: string; failed?: boolean }>({})
  useEffect(() => {
    const controller = new AbortController()
    let objectUrl: string | undefined
    void fetch(apiUrl(path), { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error()
      return response.blob()
    }).then(blob => {
      if (controller.signal.aborted) return
      objectUrl = URL.createObjectURL(blob)
      setResult({ image: objectUrl })
    }).catch(() => { if (!controller.signal.aborted) setResult({ failed: true }) })
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [path, token])
  return result.image ? <img src={result.image} alt="Hostel photo" /> : <p>{result.failed ? 'Photo unavailable' : 'Loading photo…'}</p>
}

function PhotoEditor({ hostel, token, refresh }: { hostel: ManagerListing; token: string; refresh: () => void }) {
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [remove, setRemove] = useState('')
  const [busy, setBusy] = useState(false)
  const path = `hostels/${hostel.id}/images/`
  async function operation(options: RequestInit, endpoint: string, message: string) {
    setBusy(true); setError(''); setNotice('')
    try { await apiRequest(endpoint, options, token); refresh(); setRemove(''); setNotice(message) }
    catch (error) { setError(errorText(error)) } finally { setBusy(false) }
  }
  return <><Heading title="Hostel Photo Management" text={hostel.name} />
    <form className="panel padded stack form-width" onSubmit={event => {
      event.preventDefault()
      const form = event.currentTarget
      const data = new FormData(form)
      const image = data.get('image')
      if (!(image instanceof File) || image.size > 5 * 1024 * 1024) { setError('Choose an image up to 5 MiB.'); return }
      void operation({ method: 'POST', body: data }, path, 'Photo uploaded.')
      form.reset()
    }}><Field label="Photo (JPEG, PNG, or WebP)"><input name="image" type="file" accept="image/jpeg,image/png,image/webp" required /></Field>
    <div><button className="btn primary" disabled={busy}>Upload photo</button></div></form>
    {error && <p role="alert" className="notice error">{error}</p>}{notice && <p role="status" className="notice">{notice}</p>}
    {!hostel.images.length && <Empty title="No photos yet" />}
    <div className="cards-grid dashboard-gap">{hostel.images.map((id, index) => <article className="panel hostel-card" key={id}>
      <div className="hostel-photo"><PrivatePhoto path={`${path}${id}/`} token={token} /></div><div className="card-body"><button className="btn outline" disabled={busy} onClick={() => setRemove(id)}>Delete photo {index + 1}</button></div>
    </article>)}</div>
    {remove && <Modal title="Delete photo?" close={() => { if (!busy) setRemove('') }}><p>Remove the selected photo?</p>{error && <p role="alert">{error}</p>}
      <div className="row"><button className="btn outline" disabled={busy} onClick={() => setRemove('')}>Cancel</button><button className="btn destructive" disabled={busy} onClick={() => void operation(payload('DELETE'), `${path}${remove}/`, 'Photo deleted.')}>Delete photo</button></div></Modal>}
  </>
}


function ListingPreview({ hostel, token }: { hostel: ManagerListing; token: string }) {
  const point = coordinates(hostel.latitude, hostel.longitude)
  return <><Heading title={hostel.name} text={`${hostel.address} · ${hostel.area}`} action={<Link className="btn outline" to={`${url}/${hostel.id}/edit`}>Edit Hostel</Link>} />
    <div className="stack">
      <section className="panel padded"><h2>Listing preview</h2><Badge>{hostel.publication_status === 'hidden' ? 'Suspended' : hostel.publication_status === 'pending' ? 'Ready to publish' : hostel.publication_status}</Badge><p>{hostel.description}</p>
        {hostel.amenities.length > 0 && <div className="row">{hostel.amenities.map(item => <Badge key={item}>{item}</Badge>)}</div>}</section>
      <section className="panel padded"><h2>Photos</h2>{hostel.images.length > 0 ? <div className="cards-grid">
        {hostel.images.map(id => <div key={id} className="hostel-photo"><PrivatePhoto path={`hostels/${hostel.id}/images/${id}/`} token={token} /></div>)}
      </div> : <p>No photos yet.</p>}</section>
      <section className="panel padded"><h2>Rooms &amp; availability</h2>{hostel.room_types.length ? hostel.room_types.map(room =>
        <p key={room.id}>{room.name} · {money(Number(room.price_per_bed))} / {room.billing_period} · {room.available_beds} beds reported</p>) : <p>No room types yet.</p>}</section>
      <section className="panel padded"><h2>Location</h2>{point ? <MapView label={`Location of ${hostel.name}`} center={point} pins={[{ id: hostel.id, name: hostel.name, position: point }]} /> : <p>No coordinates yet.</p>}</section>
    </div>
  </>
}
