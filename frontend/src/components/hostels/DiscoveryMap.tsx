import { useMemo } from 'react'
import { Link } from 'react-router'
import type { Hostel } from '../../types/hostel'
import { beds, money } from '../../utils/catalogue'
import MapView from '../maps/MapView'
import { HostelPhoto } from './HostelCard'

export default function DiscoveryMap({ hostels, base }: { hostels: Hostel[]; base: string }) {
  const pins = useMemo(() => hostels.flatMap(hostel => {
    if (!hostel.location) return []
    const semester = hostel.rooms.filter(room => room.billingPeriod === 'semester')
    const price = semester.length ? Math.min(...semester.map(room => room.price)) : null
    return [{
      id: hostel.id, name: hostel.name, position: hostel.location,
      content: <article className="hostel-map-popup">
        <div className="map-popup-photo"><HostelPhoto hostel={hostel} /></div>
        <h3>{hostel.name}</h3>
        <p>{hostel.area}</p>
        <p>{price === null ? 'Semester price unavailable' : `${money(price)} / semester`}</p>
        <p>{beds(hostel)} beds reported{hostel.rooms.some(room => room.stale) ? ' · Reconfirmation needed' : ''}</p>
        <Link className="btn primary" to={`${base}/${hostel.id}`}>View Details</Link>
      </article>,
    }]
  }), [hostels, base])
  return <>
    <MapView pins={pins} label="Hostels around the University of Cape Coast" fit />
    <p className="map-note" role="status">{hostels.length === 0 ? 'No hostels match your filters.' :
      pins.length === 0 ? 'No matching hostels have a confirmed map location. You can still browse the matching cards.' :
      `${pins.length} of ${hostels.length} matching hostels shown on the map.`}</p>
  </>
}
