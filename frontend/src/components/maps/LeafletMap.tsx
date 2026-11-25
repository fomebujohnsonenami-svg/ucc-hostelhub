import { divIcon, latLngBounds } from 'leaflet'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import type { Coordinates } from '../../types/location'

const ucc: Coordinates = { lat: 5.115, lng: -1.289 }
const tileUrl: string = import.meta.env.VITE_MAP_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const attribution: string = import.meta.env.VITE_MAP_TILE_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
const markerIcon = divIcon({
  className: 'hostel-pin',
  html: '<span aria-hidden="true"></span>',
  iconSize: [28, 36],
  iconAnchor: [14, 32],
  popupAnchor: [0, -29],
})

export type MapPin = { id: string; name: string; position: Coordinates; content?: ReactNode }

function ViewBounds({ pins }: { pins: MapPin[] }) {
  const map = useMap()
  useEffect(() => {
    if (pins.length) map.fitBounds(latLngBounds(pins.map(pin => pin.position)), { padding: [32, 32], maxZoom: 16 })
    else map.setView(ucc, 14)
  }, [map, pins])
  return null
}

function PickLocation({ center, onPosition }: { center?: Coordinates; onPosition: (position: Coordinates) => void }) {
  const map = useMapEvents({ click: event => onPosition(event.latlng.wrap()) })
  useEffect(() => {
    if (center && !map.getBounds().contains(center)) map.setView(center, 16)
  }, [center, map])
  return null
}

export default function LeafletMap({ pins, label, center, fit = false, onPosition }: {
  pins: MapPin[]; label: string; center?: Coordinates; fit?: boolean; onPosition?: (position: Coordinates) => void
}) {
  const [tileState, setTileState] = useState<'loading' | 'ready' | 'error'>('loading')
  const tileEvents = useMemo(() => ({
    tileload: () => setTileState(current => current === 'loading' ? 'ready' : current),
    tileerror: () => setTileState('error'),
  }), [])

  return <section className="map-frame" aria-label={label}>
    <MapContainer className="hostel-map" center={center ?? ucc} zoom={center ? 16 : 14} scrollWheelZoom={false} worldCopyJump>
      <TileLayer url={tileUrl} attribution={attribution} maxZoom={19} eventHandlers={tileEvents} />
      {fit && <ViewBounds pins={pins} />}
      {onPosition && <PickLocation center={center} onPosition={onPosition} />}
      {pins.map(pin => <Marker key={pin.id} position={pin.position} icon={markerIcon} title={pin.name} alt={pin.name}
        draggable={Boolean(onPosition)} eventHandlers={onPosition ? { dragend: event => onPosition(event.target.getLatLng().wrap()) } : undefined}>
        {pin.content && <Popup maxWidth={250}>{pin.content}</Popup>}
      </Marker>)}
    </MapContainer>
    {tileState === 'loading' && <p className="map-note" role="status">Loading map tiles…</p>}
    {tileState === 'error' && <p className="map-note" role="status">Some map tiles are unavailable. Listing details and coordinate fields are still available.</p>}
  </section>
}
