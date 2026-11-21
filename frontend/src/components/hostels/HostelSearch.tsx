import { MapPin, Search } from 'lucide-react'
import { useNavigate } from 'react-router'
import { areas } from '../../utils/catalogue'

export default function HostelSearch({ destination = '/hostels' }: { destination?: string }) {
  const navigate = useNavigate()
  return <form className="search-strip panel" onSubmit={event => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const query = new URLSearchParams()
    for (const key of ['q', 'area']) {
      const value = String(form.get(key) ?? '').trim()
      if (value) query.set(key, value)
    }
    void navigate(`${destination}${query.size ? `?${query}` : ''}`)
  }}>
    <label className="search-input"><Search size={19} aria-hidden="true" /><span className="sr-only">Search hostels</span><input name="q" placeholder="Search by hostel name or location" /></label>
    <label className="search-input search-area"><MapPin size={19} aria-hidden="true" /><span className="sr-only">Location</span><select name="area"><option value="">All UCC areas</option>{areas.map(area => <option key={area}>{area}</option>)}</select></label>
    <button className="btn primary" type="submit">Search Hostels</button>
  </form>
}
