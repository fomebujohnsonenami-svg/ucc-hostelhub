import type { Coordinates } from './location'

export type Role = 'student' | 'manager' | 'admin'
export type Room = { id: string; type: string; price: number; rooms: number; beds: number; billingPeriod?: string; stale?: boolean; availabilityUpdated?: string }
export type Hostel = {
  id: string; name: string; area: string; address: string; description: string
  images: string[]; amenities: string[]; rooms: Room[]; updated: string
  featured: boolean
  location: Coordinates | null
}
