const inputCls =
  'w-full bg-ink-900 border border-line rounded-lg px-3 py-2 text-sm text-text placeholder-faint ' +
  'focus:outline-none focus:border-accent-line focus:ring-1 focus:ring-accent-line transition-colors'

export function Input({ className = '', ...props }) {
  return <input className={`${inputCls} ${className}`} {...props} />
}

export function TextArea({ className = '', ...props }) {
  return <textarea className={`${inputCls} resize-y ${className}`} {...props} />
}

export function Select({ className = '', children, ...props }) {
  return (
    <select className={`${inputCls} ${className}`} {...props}>
      {children}
    </select>
  )
}

export function Label({ children, className = '' }) {
  return <label className={`block text-xs font-medium text-dim mb-1.5 ${className}`}>{children}</label>
}
