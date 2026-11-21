import { Crown } from 'lucide-react'

export default function PremiumBadge({ children = 'Premium' }: { children?: string }) {
  return <span className="premium-badge"><Crown size={14} aria-hidden="true" />{children}</span>
}
