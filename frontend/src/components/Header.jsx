import { BookOpen } from 'lucide-react'

export default function Header() {
  return (
    <header className="border-b border-ink/10 px-8 py-4 flex items-center justify-between sticky top-0 z-50"
      style={{ background: 'rgba(245,240,232,0.85)', backdropFilter: 'blur(12px)' }}>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'var(--accent)' }}>
          <BookOpen size={16} color="#fff" />
        </div>
        <span className="font-display text-xl font-bold tracking-tight" style={{ color: 'var(--ink)' }}>
          Research<span style={{ color: 'var(--accent)' }}>Lens</span>
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs px-2 py-1 rounded" style={{ background: 'var(--highlight)', color: 'var(--muted)' }}>
          arXiv · Deep Learning
        </span>
      </div>
    </header>
  )
}
