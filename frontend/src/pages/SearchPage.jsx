import { useState, useEffect } from 'react'
import { Search, Sparkles, ChevronDown } from 'lucide-react'
import axios from 'axios'

const EXAMPLE_QUERIES = [
  "transformer attention mechanism for NLP",
  "graph neural network molecule prediction",
  "reinforcement learning robotics control",
  "federated learning privacy preserving",
  "diffusion models image generation",
]

export default function SearchPage({ setResults, setQuery, setLoading, loading }) {
  const [input, setInput] = useState('')
  const [topN, setTopN] = useState(10)
  const [domain, setDomain] = useState('')
  const [domains, setDomains] = useState([])
  const [error, setError] = useState('')
  const [placeholder, setPlaceholder] = useState(EXAMPLE_QUERIES[0])

  useEffect(() => {
    let i = 0
    const interval = setInterval(() => {
      i = (i + 1) % EXAMPLE_QUERIES.length
      setPlaceholder(EXAMPLE_QUERIES[i])
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    axios.get('/api/domains').then(r => setDomains(r.data.domains)).catch(() => {})
  }, [])

  async function handleSearch(e) {
    e.preventDefault()
    if (!input.trim()) return
    setError('')
    setLoading(true)
    setQuery(input.trim())
    try {
      const res = await axios.post('/api/recommend', {
        query: input.trim(),
        top_n: topN,
        domain_filter: domain || null
      })
      setResults(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Backend not reachable. Is the server running?')
    } finally {
      setLoading(false)
    }
  }
  const domainLabels = {
    'cs.AI': 'Artificial Intelligence',
    'cs.LG': 'Machine Learning',
    'cs.CV': 'Computer Vision',
    'cs.CL': 'Natural Language Processing',
    'cs.NE': 'Neural Networks',
    'cs.RO': 'Robotics',
    'cs.IR': 'Information Retrieval',
    'stat.ML': 'Statistics / ML',
    'math.OC': 'Optimization',
    'quant-ph': 'Quantum Computing',
    'q-bio': 'Biology',
    'eess.IV': 'Image Processing',
    'eess.SP': 'Signal Processing',
    'econ.EM': 'Economics',
    'Review': 'Review Articles',
    'JournalArticle': 'Journal Article',
    'Conference': 'Conference Paper',
  }

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-6 py-20">
      {/* Hero */}
      <div className="text-center mb-14 max-w-2xl">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-6 font-mono text-xs"
          style={{ background: 'var(--highlight)', color: 'var(--accent)', border: '1px solid var(--accent)' }}>
          <Sparkles size={12} />
          Semantic Search · Sentence Transformers · FAISS
        </div>
        <h1 className="font-display text-5xl md:text-6xl font-bold leading-tight mb-5"
          style={{ color: 'var(--ink)', letterSpacing: '-1px' }}>
          Find the papers<br />
          <em style={{ color: 'var(--accent)' }}>that matter.</em>
        </h1>
        <p className="text-lg" style={{ color: 'var(--muted)', fontWeight: 300 }}>
          Describe your research interest in plain language. We'll match it semantically across hundreds of thousands of arXiv papers.
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="w-full max-w-2xl">
        <div className="relative mb-4">
          <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--muted)' }} />
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={`e.g. "${placeholder}"`}
            className="w-full pl-12 pr-4 py-4 rounded-xl text-base outline-none"
            style={{
              background: 'var(--card)',
              border: '1.5px solid rgba(13,13,13,0.12)',
              color: 'var(--ink)',
              fontFamily: 'DM Sans, sans-serif',
              boxShadow: '0 4px 24px rgba(13,13,13,0.06)'
            }}
          />
        </div>

        {/* Controls row */}
        <div className="flex flex-wrap gap-3 mb-5">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'var(--highlight)' }}>
            <span className="text-sm font-mono" style={{ color: 'var(--muted)' }}>Top</span>
            <select value={topN} onChange={e => setTopN(+e.target.value)}
              className="font-mono text-sm bg-transparent outline-none" style={{ color: 'var(--ink)' }}>
              {[5, 10, 15, 20].map(n => <option key={n}>{n}</option>)}
            </select>
            <span className="text-sm font-mono" style={{ color: 'var(--muted)' }}>results</span>
          </div>

          {domains.length > 0 && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'var(--highlight)' }}>
              <span className="text-sm font-mono" style={{ color: 'var(--muted)' }}>Domain</span>
              <select value={domain} onChange={e => setDomain(e.target.value)}
                className="font-mono text-sm bg-transparent outline-none" style={{ color: 'var(--ink)' }}>
                <option value="">All</option>
                {domains.map(d => <option key={d} value={d}>{domainLabels[d] || d}</option>)}
              </select>
            </div>
          )}
        </div>

        <button type="submit" disabled={loading}
          className="w-full py-4 rounded-xl font-display text-lg font-bold transition-all"
          style={{
            background: loading ? 'var(--muted)' : 'var(--accent)',
            color: '#fff',
            letterSpacing: '0.01em',
            cursor: loading ? 'not-allowed' : 'pointer',
            boxShadow: loading ? 'none' : '0 4px 20px rgba(200,68,26,0.35)'
          }}>
          {loading ? 'Searching…' : 'Find Papers'}
        </button>

        {error && (
          <div className="mt-4 p-3 rounded-lg font-mono text-sm text-center"
            style={{ background: '#fff0ec', color: 'var(--accent)', border: '1px solid var(--accent)' }}>
            ⚠ {error}
          </div>
        )}
      </form>

      {/* Example chips */}
      <div className="mt-10 flex flex-wrap gap-2 justify-center max-w-xl">
        <span className="text-sm" style={{ color: 'var(--muted)' }}>Try:</span>
        {EXAMPLE_QUERIES.slice(0, 4).map(q => (
          <button key={q} onClick={() => setInput(q)}
            className="text-sm px-3 py-1.5 rounded-full transition-all hover:opacity-80"
            style={{ background: 'var(--highlight)', color: 'var(--muted)', border: '1px solid rgba(13,13,13,0.1)' }}>
            {q}
          </button>
        ))}
      </div>
    </main>
  )
}
