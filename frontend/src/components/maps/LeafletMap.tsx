import { maplibreGL } from '@maplibre/maplibre-gl-leaflet'
import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { divIcon, latLngBounds } from 'leaflet'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Coordinates } from '../../types/location'

setWorkerUrl(workerUrl)

const ucc: Coordinates = { lat: 5.115, lng: -1.289 }
const rasterUrl: string = import.meta.env.VITE_MAP_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const attribution: string = import.meta.env.VITE_MAP_TILE_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
const openFreeMapStyle = 'https://tiles.openfreemap.org/styles/liberty'
const openFreeMapAttribution = '<a href="https://openfreemap.org/">OpenFreeMap</a> · <a href="https://openmaptiles.org/">OpenMapTiles</a> · &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
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

function RouteLine({ points }: { points: Coordinates[] }) {
  const map = useMap()
  useEffect(() => {
    map.fitBounds(latLngBounds(points), { padding: [32, 32], maxZoom: 16 })
  }, [map, points])
  return <Polyline positions={points} pathOptions={{ color: '#6236C5', weight: 5 }} />
}

function FocusLocation({ position }: { position: Coordinates }) {
  const map = useMap()
  useEffect(() => {
    map.setView(position, 16)
  }, [map, position])
  return null
}

function PickLocation({ center, onPosition }: { center?: Coordinates; onPosition: (position: Coordinates) => void }) {
  const map = useMapEvents({ click: event => onPosition(event.latlng.wrap()) })
  useEffect(() => {
    if (center && !map.getBounds().contains(center)) map.setView(center, 16)
  }, [center, map])
  return null
}

function OpenFreeMapLayer({ onReady, onUnavailable }: { onReady: () => void; onUnavailable: () => void }) {
  const map = useMap()
  useEffect(() => {
    const context = document.createElement('canvas').getContext('webgl2')
    if (!context) {
      onUnavailable()
      return
    }
    context.getExtension('WEBGL_lose_context')?.loseContext()

    const layer = maplibreGL({
      style: openFreeMapStyle,
      attributionControl: { customAttribution: openFreeMapAttribution },
    }).addTo(map)
    const vectorMap = layer.getMaplibreMap()
    vectorMap.once('load', onReady)
    vectorMap.on('error', onUnavailable)
    return () => {
      vectorMap.off('load', onReady)
      vectorMap.off('error', onUnavailable)
      layer.remove()
    }
  }, [map, onReady, onUnavailable])
  return null
}

export default function LeafletMap({ pins, label, center, fit = false, focus, route, onPosition }: {
  pins: MapPin[]; label: string; center?: Coordinates; fit?: boolean; focus?: Coordinates; route?: Coordinates[]; onPosition?: (position: Coordinates) => void
}) {
  const [tileState, setTileState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [useRaster, setUseRaster] = useState(Boolean(import.meta.env.VITE_MAP_TILE_URL))
  const onVectorReady = useCallback(() => setTileState('ready'), [])
  const onVectorUnavailable = useCallback(() => {
    setTileState('loading')
    setUseRaster(true)
  }, [])
  const tileEvents = useMemo(() => ({
    tileload: () => setTileState(current => current === 'loading' ? 'ready' : current),
    tileerror: () => setTileState('error'),
  }), [])

  return <section className="map-frame" aria-label={label}>
    <MapContainer className="hostel-map" center={center ?? ucc} zoom={center ? 16 : 14} scrollWheelZoom={false} worldCopyJump>
      {useRaster ? <TileLayer url={rasterUrl} attribution={attribution} maxZoom={19} eventHandlers={tileEvents} /> :
        <OpenFreeMapLayer onReady={onVectorReady} onUnavailable={onVectorUnavailable} />}
      {route && <RouteLine points={route} />}
      {fit && !focus && <ViewBounds pins={pins} />}
      {focus && <FocusLocation position={focus} />}
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
