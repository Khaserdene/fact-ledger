import Badge from '../ui/Badge'
import { User, Building2, Briefcase, Landmark, Flag, GraduationCap, MapPin, HandCoins, Shapes, LandPlot, ScrollText, FolderGit2 } from 'lucide-react'

export const ENTITY_TYPES = {
  case: { label: 'Мөрдлөгийн хэрэг', Icon: FolderGit2, color: '#f43f5e' },
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
export const TYPE_ORDER = ['case', 'person', 'government', 'parliament', 'party', 'org', 'company', 'fund', 'state', 'school', 'location', 'other']

export const PARTY_COLORS = {
  'Монгол Ардын Нам': {
    name: 'Монгол Ардын Нам',
    short: 'МАН',
    color: '#ef4444', // Red
    bg: 'rgba(239, 68, 68, 0.15)',
    border: 'rgba(239, 68, 68, 0.4)',
  },
  'Ардчилсан Нам': {
    name: 'Ардчилсан Нам',
    short: 'АН',
    color: '#3b82f6', // Blue
    bg: 'rgba(59, 130, 246, 0.15)',
    border: 'rgba(59, 130, 246, 0.4)',
  },
  'Монгол Ардын Хувьсгалт Нам': {
    name: 'Монгол Ардын Хувьсгалт Нам',
    short: 'МАХН',
    color: '#f97316', // Orange
    bg: 'rgba(249, 115, 22, 0.15)',
    border: 'rgba(249, 115, 22, 0.4)',
  },
  'ХҮН нам': {
    name: 'ХҮН нам',
    short: 'ХҮН',
    color: '#a855f7', // Purple
    bg: 'rgba(168, 85, 247, 0.15)',
    border: 'rgba(168, 85, 247, 0.4)',
  },
  'Иргэний Зориг Ногоон Нам': {
    name: 'Иргэний Зориг Ногоон Нам',
    short: 'ИЗНН',
    color: '#10b981', // Emerald / Green
    bg: 'rgba(16, 185, 129, 0.15)',
    border: 'rgba(16, 185, 129, 0.4)',
  },
  'Бусад / Нам бус': {
    name: 'Бусад / Нам бус',
    short: 'Нам бус',
    color: '#64748b', // Slate
    bg: 'rgba(100, 116, 139, 0.15)',
    border: 'rgba(100, 116, 139, 0.4)',
  },
}

export function getPartyInfo(partyName) {
  if (!partyName) return PARTY_COLORS['Бусад / Нам бус']
  for (const [key, val] of Object.entries(PARTY_COLORS)) {
    if (partyName.includes(key) || key.includes(partyName)) return val
  }
  return {
    name: partyName,
    short: partyName.length > 6 ? partyName.slice(0, 4) : partyName,
    color: '#eab308',
    bg: 'rgba(234, 179, 8, 0.15)',
    border: 'rgba(234, 179, 8, 0.4)',
  }
}

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
