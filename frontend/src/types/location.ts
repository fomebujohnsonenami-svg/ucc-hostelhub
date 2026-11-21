export type Coordinates = { lat: number; lng: number }

export function coordinates(latitude: string | number | null, longitude: string | number | null): Coordinates | null {
  if (latitude === null || longitude === null || String(latitude).trim() === '' || String(longitude).trim() === '') return null
  const lat = Number(latitude)
  const lng = Number(longitude)
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? { lat, lng } : null
}

export function directions(location: Coordinates) {
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${location.lat},${location.lng}`)}`
}
