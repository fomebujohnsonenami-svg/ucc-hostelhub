import { Component, lazy, Suspense } from 'react'
import type { ComponentProps, ReactNode } from 'react'
import type LeafletMap from './LeafletMap'

const InteractiveMap = lazy(() => import('./LeafletMap'))

class MapBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    return this.state.failed ? <p className="map-note" role="status">The map could not load. You can still use listing details or enter coordinates manually.</p> : this.props.children
  }
}

export default function MapView(props: ComponentProps<typeof LeafletMap>) {
  return <MapBoundary><Suspense fallback={<p className="map-note" role="status">Loading map…</p>}><InteractiveMap {...props} /></Suspense></MapBoundary>
}
