import type { Hostel } from '../types/hostel'
import { coordinates } from '../types/location'
import type { Coordinates } from '../types/location'
import { apiGet, apiRequest, apiUrl } from './api'

type LocationFields = { latitude: string | null; longitude: string | null }
export type ManagerListing = LocationFields & {
  id: string; name: string; address: string; area: string; description: string
  publication_status: string; verification_status: string; amenities: string[]; images: string[]; room_types: ApiRoom[]
}
export type ApiRoom = { id: string; name: string; price_per_bed: string; total_rooms: number; available_beds: number; billing_period: string; capacity: number; total_capacity: number; availability_stale: boolean; availability_updated_at: string }
export type PublicListing = LocationFields & {
  id: string; name: string; address: string; area: string; description: string
  updated_at: string; featured: boolean; amenities: string[]; images: string[]
  room_types: ApiRoom[]
}

export function asHostel(data: PublicListing): Hostel {
  return {
    id: data.id, name: data.name, address: data.address, area: data.area,
    description: data.description, featured: data.featured, updated: data.updated_at, amenities: data.amenities,
    images: data.images.map(apiUrl), location: coordinates(data.latitude, data.longitude),
    rooms: data.room_types.map(room => ({
      id: room.id, type: room.name, price: Number(room.price_per_bed), rooms: room.total_rooms,
      beds: room.available_beds, billingPeriod: room.billing_period, stale: room.availability_stale, availabilityUpdated: room.availability_updated_at,
    })),
  }
}

export async function approvedHostel(id: string, signal: AbortSignal) {
  return asHostel(await apiGet<PublicListing>(`hostels/${encodeURIComponent(id)}/`, signal))
}

type ListingInput = Pick<ManagerListing, 'name' | 'address' | 'area' | 'description' | 'amenities'>
export function saveManagerHostel(id: string | undefined, token: string, details: ListingInput, location: Coordinates | null) {
  return apiRequest<ManagerListing>(id ? `manager/hostels/${encodeURIComponent(id)}/` : 'manager/hostels/', {
    method: id ? 'PATCH' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...details,
      latitude: location?.lat.toFixed(6) ?? null,
      longitude: location?.lng.toFixed(6) ?? null,
    }),
  }, token)
}
