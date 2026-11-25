import { useEffect, useRef, useState } from 'react'
import { Navigation } from 'lucide-react'
import MapView from './MapView'
import { directions } from '../../types/location'
import type { Coordinates } from '../../types/location'
import { walkingRoute } from '../../services/routing'
import type { WalkingRoute } from '../../services/routing'

export default function HostelDirections({ name, destination }: { name: string; destination: Coordinates }) {
  const request = useRef<AbortController | null>(null)
  const [stage, setStage] = useState<'locating' | 'routing'>()
  const [error, setError] = useState('')
  const [route, setRoute] = useState<(WalkingRoute & { origin: Coordinates })>()

  useEffect(() => () => request.current?.abort(), [])

  function showRoute() {
    setError('')
    if (!navigator.geolocation) {
      setError('Location access is unavailable. You can open the hostel in Google Maps.')
      return
    }
    const controller = new AbortController()
    request.current?.abort()
    request.current = controller
    setStage('locating')
    setRoute(undefined)
    navigator.geolocation.getCurrentPosition(async ({ coords }) => {
      if (controller.signal.aborted) return
      const origin = { lat: coords.latitude, lng: coords.longitude }
      setStage('routing')
      try {
        const result = await walkingRoute(origin, destination, controller.signal)
        if (!controller.signal.aborted) setRoute({ ...result, origin })
      } catch {
        if (!controller.signal.aborted) setError('Could not find a walking route. Try again or open Google Maps.')
      } finally {
        if (!controller.signal.aborted) setStage(undefined)
      }
    }, failure => {
      if (controller.signal.aborted) return
      setError(failure.code === 1 ? 'Location permission was denied. Allow it in your browser or open Google Maps.'
        : 'Your location could not be determined. Try again or open Google Maps.')
      setStage(undefined)
    }, { enableHighAccuracy: true, timeout: 10000 })
  }

  const pins = [{ id: 'hostel', name, position: destination }]
  if (route) pins.push({ id: 'visitor', name: 'Your location', position: route.origin })
  const distance = route && (route.metres < 1000 ? `${Math.round(route.metres)} m` : `${(route.metres / 1000).toFixed(1)} km`)

  return <div className="stack">
    <MapView label={`Location of ${name}`} center={destination} pins={pins} route={route?.points} />
    <div className="row">
      <button type="button" className="btn primary" disabled={Boolean(stage)} onClick={showRoute}>
        <Navigation size={16} aria-hidden="true" /> {stage === 'locating' ? 'Finding your location…' :
          stage === 'routing' ? 'Finding a route…' : route ? 'Update walking route' : 'Get walking directions'}
      </button>
      <a className="btn outline" href={directions(destination)} target="_blank" rel="noreferrer">Open in Google Maps</a>
    </div>
    <small className="muted">Requesting directions shares your location with the routing service.</small>
    {route && <p className="notice" role="status">
      <strong>About {Math.max(1, Math.round(route.seconds / 60))} min walking</strong> · {distance}.
      Estimated by <a href="https://routing.openstreetmap.de/" target="_blank" rel="noreferrer">OSRM</a>.
    </p>}
    {error && <p className="notice error" role="alert">{error}</p>}
  </div>
}
