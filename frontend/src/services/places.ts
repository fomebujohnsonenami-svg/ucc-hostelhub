import { coordinates } from '../types/location'
import type { Coordinates } from '../types/location'

export type Place = { label: string; position: Coordinates }

type PlaceFeature = {
  geometry?: { coordinates?: unknown }
  properties?: {
    name?: string
    street?: string
    district?: string
    city?: string
    state?: string
    countrycode?: string
  }
}

export async function searchPlaces(query: string, signal: AbortSignal): Promise<Place[]> {
  const url = new URL('https://photon.komoot.io/api/')
  url.search = new URLSearchParams({
    q: query, limit: '5', lat: '5.115', lon: '-1.289', bbox: '-3.27,4.73,1.20,11.18',
  }).toString()
  const response = await fetch(url, {
    credentials: 'omit',
    signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]),
  })
  if (!response.ok) throw new Error('Place search unavailable')
  const data: { features?: PlaceFeature[] } = await response.json()
  if (!Array.isArray(data.features)) throw new Error('Invalid place results')

  return data.features.flatMap(({ geometry, properties }) => {
    const point = geometry?.coordinates
    if (!properties || (properties.countrycode && properties.countrycode.toUpperCase() !== 'GH')
        || !Array.isArray(point) || typeof point[0] !== 'number' || typeof point[1] !== 'number') return []
    const position = coordinates(point[1], point[0])
    const { name, street, district, city, state } = properties
    const label = [...new Set([name, street, district, city, state].filter(Boolean))].join(', ')
    return position && label ? [{ position, label }] : []
  })
}
