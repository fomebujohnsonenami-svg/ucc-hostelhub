import { useMemo, useState } from 'react'
import { Field } from '../common/UI'
import { coordinates } from '../../types/location'
import MapView from './MapView'

export type LocationInput = { latitude: string; longitude: string }

export default function LocationPicker({ value, onChange }: { value: LocationInput; onChange: (value: LocationInput) => void }) {
  const position = useMemo(() => coordinates(value.latitude, value.longitude), [value])
  const [locating, setLocating] = useState(false)
  const [message, setMessage] = useState('')
  const pins = useMemo(() => position ? [{ id: 'location', name: 'Selected hostel location', position }] : [], [position])

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setMessage('Location access is unavailable. Place the pin on the map instead.')
      return
    }
    setLocating(true)
    setMessage('')
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      onChange({ latitude: coords.latitude.toFixed(6), longitude: coords.longitude.toFixed(6) })
      setMessage(`Pin placed using your location (estimated accuracy: ${Math.round(coords.accuracy)} m). Adjust it if needed before saving.`)
      setLocating(false)
    }, () => {
      setMessage('Could not get your location. You can still place the pin on the map.')
      setLocating(false)
    }, { enableHighAccuracy: true, timeout: 10000 })
  }

  return <fieldset className="stack">
    <legend className="location-legend">Hostel location</legend>
    <p className="muted">If you’re at the hostel, use your current location. You can also click the map, drag the marker, or enter both coordinates.</p>
    <div><button type="button" className="btn outline" disabled={locating} onClick={useCurrentLocation}>{locating ? 'Finding your location…' : 'Use my current location'}</button></div>
    {message && <p className="muted" role="status">{message}</p>}
    <MapView label="Hostel location picker" pins={pins} center={position ?? undefined} onPosition={point => onChange({ latitude: point.lat.toFixed(6), longitude: point.lng.toFixed(6) })} />
    <div className="two-grid">
      <Field label="Latitude"><input type="number" min="-90" max="90" step="0.000001" value={value.latitude} onChange={event => onChange({ ...value, latitude: event.target.value })} /></Field>
      <Field label="Longitude"><input type="number" min="-180" max="180" step="0.000001" value={value.longitude} onChange={event => onChange({ ...value, longitude: event.target.value })} /></Field>
    </div>
    {(value.latitude || value.longitude) && <div><button type="button" className="text-link" onClick={() => onChange({ latitude: '', longitude: '' })}>Clear location</button></div>}
  </fieldset>
}
