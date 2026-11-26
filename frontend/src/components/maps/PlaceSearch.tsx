import { useEffect, useRef, useState } from 'react'
import { MapPin } from 'lucide-react'
import { searchPlaces } from '../../services/places'
import type { Place } from '../../services/places'

export default function PlaceSearch({ onSelect }: { onSelect: (place: Place) => void }) {
  const [term, setTerm] = useState('')
  const [results, setResults] = useState<Place[]>()
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const request = useRef<AbortController | null>(null)

  useEffect(() => () => request.current?.abort(), [])

  async function search() {
    const query = term.trim()
    if (loading || query.length < 3) return
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    setMessage('')
    setResults(undefined)
    try {
      const places = await searchPlaces(query, controller.signal)
      if (!controller.signal.aborted) {
        setResults(places)
        setMessage(places.length ? 'Select a result to place a pin.' : 'No places found. Try adding a nearby landmark or town.')
      }
    } catch {
      if (!controller.signal.aborted) setMessage('Place search is unavailable. Try again in a moment.')
    } finally {
      if (!controller.signal.aborted) setLoading(false)
    }
  }

  // This also appears inside the manager's listing form.
  return <div className="stack" role="search" aria-label="Search places in Ghana">
    <div className="row discovery-toolbar">
      <label className="search-input panel">
        <MapPin size={17} aria-hidden="true" />
        <span className="sr-only">Place, address, or landmark in Ghana</span>
        <input type="search" value={term} maxLength={160} placeholder="Place, address, or landmark in Ghana"
          onChange={event => setTerm(event.target.value)} onKeyDown={event => {
            if (event.key === 'Enter' && !event.nativeEvent.isComposing) {
              event.preventDefault()
              void search()
            }
          }} />
      </label>
      <button type="button" className="btn outline" disabled={loading || term.trim().length < 3} onClick={() => void search()}>
        {loading ? 'Searching…' : 'Find a place'}
      </button>
    </div>
    {message && <p className="muted" role="status">{message}</p>}
    {!!results?.length && <ul className="stack" aria-label="Place results">{results.map(({ label, position }) =>
      <li key={`${label}:${position.lat}:${position.lng}`}>
        <button type="button" className="btn outline" onClick={() => {
          onSelect({ label, position })
          setResults(undefined)
          setMessage(`Pin placed at ${label}.`)
        }}>{label}</button>
      </li>)}</ul>}
  </div>
}
