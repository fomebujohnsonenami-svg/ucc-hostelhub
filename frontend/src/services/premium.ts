export type Plan = {
  audience: 'student' | 'manager'
  name: string
  price: string
  billing_period: 'month'
  features: string[]
}

export type Catalogue = { access_mode: 'presentation' | 'launch_preview'; payments_available: false; plans: Plan[] }
export const showPresentationUI = import.meta.env.VITE_PRESENTATION_MODE === 'true'
