import { coordinates } from '../types/location'
import type { Coordinates } from '../types/location'

export type WalkingRoute = {
  points: Coordinates[]
  metres: number
  seconds: number
}

const walkingEndpoint = 'https://routing.openstreetmap.de/routed-foot/route/v1/driving'

export async function walkingRoute(origin: Coordinates, destination: Coordinates, signal: AbortSignal): Promise<WalkingRoute> {
  const stops = [origin, destination].map(({ lat, lng }) => `${lng.toFixed(6)},${lat.toFixed(6)}`).join(';')
  const response = await fetch(`${walkingEndpoint}/${stops}?overview=full&geometries=geojson`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(12000)]),
    credentials: 'omit',
  })
  if (!response.ok) throw new Error('Routing service unavailable')

  const data: { code?: string; routes?: { distance: number; duration: number; geometry?: { coordinates?: unknown } }[] } = await response.json()
  const route = data.code === 'Ok' ? data.routes?.[0] : undefined
  const geometry = route?.geometry?.coordinates
  if (!route || !Number.isFinite(route.distance) || !Number.isFinite(route.duration)
      || route.distance < 0 || route.duration < 0 || !Array.isArray(geometry)) {
    throw new Error('No walking route returned')
  }
  const points = geometry.map(point => Array.isArray(point) && typeof point[0] === 'number' && typeof point[1] === 'number'
    ? coordinates(point[1], point[0]) : null)
  if (points.length < 2 || points.some(point => point === null)) throw new Error('Invalid route geometry')
  return { points: points.filter(point => point !== null), metres: route.distance, seconds: route.duration }
}
