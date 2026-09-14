import Badge from '../ui/Badge'
import { User, Building2, Briefcase, Landmark, Flag, GraduationCap, MapPin, HandCoins, Shapes, LandPlot, ScrollText } from 'lucide-react'

export const ENTITY_TYPES = {
  person: { label: 'Хүн', Icon: User, color: '#38e0ff' },
  org: { label: 'Байгууллага', Icon: Building2, color: '#7deeff' },
  company: { label: 'Компани', Icon: Briefcase, color: '#5eead4' },
  fund: { label: 'Сан', Icon: HandCoins, color: '#a5f3d0' },
  state: { label: 'Төрийн байгууллага', Icon: Landmark, color: '#c4b5fd' },
  party: { label: 'Нам', Icon: Flag, color: '#ffb224' },
  school: { label: 'Сургууль', Icon: GraduationCap, color: '#93c5fd' },
  location: { label: 'Байршил', Icon: MapPin, color: '#fda4af' },
  government: { label: 'Засгийн газар', Icon: LandPlot, color: '#f472b6' },
  parliament: { label: 'УИХ-ын тойрог', Icon: ScrollText, color: '#a78bfa' },
  other: { label: 'Бусад', Icon: Shapes, color: '#7c93a3' },
}

// График дээр гаргах дараалал
export const TYPE_ORDER = ['person', 'government', 'parliament', 'party', 'org', 'company', 'fund', 'state', 'school', 'location', 'other']

export function entityType(type) {
  return ENTITY_TYPES[type] || ENTITY_TYPES.other
}

export default function EntityBadge({ type, showLabel = true }) {
  const t = entityType(type)
  return (
    <Badge tone={type === 'person' ? 'accent' : 'neutral'}>
      <t.Icon size={12} />
      {showLabel && t.label}
    </Badge>
  )
}
