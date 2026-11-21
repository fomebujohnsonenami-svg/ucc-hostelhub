import { useMemo } from 'react'
import { Field } from '../common/UI'
import { coordinates } from '../../types/location'
import MapView from './MapView'

export type LocationInput = { latitude: string; longitude: string }

export default function LocationPicker({ value, onChange }: { value: LocationInput; onChange: (value: LocationInput) => void }) {
  const position = useMemo(() => coordinates(value.latitude, value.longitude), [value])
  const pins = useMemo(() => position ? [{ id: 'location', name: 'Selected hostel location', position }] : [], [position])

  return <fieldset className="stack">
    <legend className="location-legend">Hostel location</legend>
    <p className="muted">Click the map or drag the marker. You can also enter both coordinates directly.</p>
    <MapView label="Hostel location picker" pins={pins} center={position ?? undefined} onPosition={point => onChange({ latitude: point.lat.toFixed(6), longitude: point.lng.toFixed(6) })} />
    <div className="two-grid">
      <Field label="Latitude"><input type="number" min="-90" max="90" step="0.000001" value={value.latitude} onChange={event => onChange({ ...value, latitude: event.target.value })} /></Field>
      <Field label="Longitude"><input type="number" min="-180" max="180" step="0.000001" value={value.longitude} onChange={event => onChange({ ...value, longitude: event.target.value })} /></Field>
    </div>
    {(value.latitude || value.longitude) && <div><button type="button" className="text-link" onClick={() => onChange({ latitude: '', longitude: '' })}>Clear location</button></div>}
  </fieldset>
}
