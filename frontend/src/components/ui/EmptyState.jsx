export default function EmptyState({ icon: Icon, title, children }) {
  return (
    <div className="text-center py-14">
      <div className="mb-3 flex justify-center text-faint">
        {Icon ? (
          <Icon size={36} strokeWidth={1.25} />
        ) : (
          <span className="text-3xl opacity-40">◌</span>
        )}
      </div>
      {title && <p className="text-dim font-medium mb-1 font-mono">{title}</p>}
      <div className="text-faint text-sm">{children}</div>
    </div>
  )
}
