const TONES = {
  neutral: 'bg-surface-2 text-dim border-line',
  accent: 'bg-accent-dim text-accent border-accent-line',
  danger: 'bg-danger-dim text-danger border-danger/30',
  ok: 'bg-ok-dim text-ok border-ok/30',
}

export default function Badge({ tone = 'neutral', className = '', children, ...props }) {
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${TONES[tone]} ${className}`}
      {...props}
    >
      {children}
    </span>
  )
}
