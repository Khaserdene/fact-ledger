const VARIANTS = {
  primary: 'bg-accent text-ink-950 font-semibold hover:bg-accent-bright disabled:hover:bg-accent',
  ghost: 'bg-surface text-dim border border-line hover:bg-surface-2 hover:text-text',
  danger: 'bg-transparent text-danger border border-danger/30 hover:bg-danger-dim',
  ok: 'bg-ok/15 text-ok border border-ok/30 hover:bg-ok/25',
}

export default function Button({ variant = 'ghost', size = 'md', className = '', ...props }) {
  const sizeCls = size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
  return (
    <button
      className={`rounded-lg font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${sizeCls} ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  )
}
