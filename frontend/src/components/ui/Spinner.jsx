export default function Spinner({ label = 'Ачаалж байна…' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-faint text-sm">
      <span className="inline-block w-4 h-4 border-2 border-line-strong border-t-accent rounded-full animate-spin" />
      {label}
    </div>
  )
}
