export default function Tabs({ tabs, active, onChange, className = '' }) {
  return (
    <div className={`glass flex gap-1 p-1 ${className}`}>
      {tabs.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={`flex-1 text-sm font-medium py-2 px-3 rounded-[10px] transition-all ${
            active === t.key
              ? 'bg-surface-3 text-text shadow-sm'
              : 'text-faint hover:text-dim'
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}
