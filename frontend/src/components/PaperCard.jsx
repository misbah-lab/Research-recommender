import { useState } from 'react'
import { ThumbsUp, ThumbsDown, ChevronDown, ChevronUp } from 'lucide-react'
import axios from 'axios'

function ScoreRing({ score }) {
  const r = 20
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 75 ? '#2d8a4e' : score >= 50 ? '#c8441a' : '#7a7065'

  return (
    <div className="relative flex-shrink-0 flex items-center justify-center" style={{ width: 52, height: 52 }}>
      <svg width="52" height="52" viewBox="0 0 52 52">
        <circle cx="26" cy="26" r={r} fill="none" stroke="rgba(13,13,13,0.08)" strokeWidth="4" />
        <circle cx="26" cy="26" r={r} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 26 26)"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      </svg>
      <span className="absolute font-mono text-xs font-bold" style={{ color }}>{score}%</span>
    </div>
  )
}

export default function PaperCard({ paper, rank }) {
  const [expanded, setExpanded] = useState(false)
  const [feedback, setFeedback] = useState(null)

  const pdfUrl = paper.pdf_url || `https://arxiv.org/pdf/${paper.id}`
  const cats = paper.categories?.split(' ').filter(Boolean).slice(0, 3) || []

  function sendFeedback(relevant) {
    setFeedback(relevant)
    axios.post('https://researchlens-backend-feuy.onrender.com/feedback', { paper_id: paper.id, relevant }).catch(() => {})
  }

  return (
    <div className="paper-card rounded-xl p-5" style={{
      background: 'var(--card)',
      border: '1px solid rgba(13,13,13,0.08)',
      boxShadow: '0 2px 12px rgba(13,13,13,0.04)'
    }}>
      <div className="flex gap-4 items-start">
        <span className="font-mono text-xs mt-1 flex-shrink-0 w-6 text-right" style={{ color: 'var(--muted)' }}>
          #{rank}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-1">
            <div>
              <h3 className="font-display text-base font-bold leading-snug" style={{ color: 'var(--ink)' }}>
                {paper.title}
              </h3>
              {paper.year && (
                <span className="font-mono text-sm font-semibold" style={{ color: 'var(--muted)' }}>
                  {paper.year}
                </span>
              )}
            </div>
            <ScoreRing score={Math.round(paper.match_score)} />
          </div>

          <div className="flex flex-wrap items-center gap-3 mb-3 mt-2 text-sm" style={{ color: 'var(--muted)' }}>
            <span className="font-mono text-xs">{paper.id?.replace(/^abs-/, '').replace(/v\d+$/, '') || paper.id}</span>
              {paper.authors && (
              <span className="truncate max-w-xs">· {paper.authors.slice(0, 80)}{paper.authors.length > 80 ? '…' : ''}</span>
            )}
          </div>

          {cats.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {cats.map((c, i) => (
  <span key={`${c}-${i}`} className="font-mono text-xs px-2 py-0.5 rounded"
    style={{ background: 'var(--highlight)', color: 'var(--accent)', border: '1px solid rgba(200,68,26,0.2)' }}>
    {c}
  </span>
))}
             
            </div>
          )}

          <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--muted)', lineHeight: 1.65 }}>
            {expanded ? paper.abstract : paper.abstract?.slice(0, 200) + (paper.abstract?.length > 200 ? '…' : '')}
          </p>

          <div className="flex items-center gap-3 flex-wrap">
            <button onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs transition-opacity hover:opacity-70"
              style={{ color: 'var(--accent)' }}>
              {expanded ? <><ChevronUp size={13} /> Less</> : <><ChevronDown size={13} /> Read more</>}
            </button>

            <a href={pdfUrl} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg transition-all hover:opacity-80"
              style={{ background: 'var(--accent)', color: '#fff', fontWeight: 500 }}>
              ↓ Download PDF
            </a>

            <div className="flex-1" />

            <div className="flex items-center gap-2">
              <span className="text-xs" style={{ color: 'var(--muted)' }}>Relevant?</span>
              <button onClick={() => sendFeedback(true)}
                className="p-1.5 rounded transition-all"
                style={{
                  background: feedback === true ? '#e8f5ec' : 'transparent',
                  color: feedback === true ? '#2d8a4e' : 'var(--muted)'
                }}>
                <ThumbsUp size={14} />
              </button>
              <button onClick={() => sendFeedback(false)}
                className="p-1.5 rounded transition-all"
                style={{
                  background: feedback === false ? '#fff0ec' : 'transparent',
                  color: feedback === false ? 'var(--accent)' : 'var(--muted)'
                }}>
                <ThumbsDown size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}