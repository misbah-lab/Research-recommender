import { useState } from 'react'
import { ArrowLeft, Search } from 'lucide-react'
import PaperCard from '../components/PaperCard.jsx'
import axios from 'axios'

export default function ResultsPage({ results, query, onBack, setResults, setLoading, loading, setQuery }) {
  const [input, setInput] = useState(query)
  const [topN, setTopN] = useState(10)
  const [sortBy, setSortBy] = useState('match')

  const sortedResults = [...results].sort((a, b) => {
    if (sortBy === 'year') {
      const ay = parseInt(a.year) || 0
      const by = parseInt(b.year) || 0
      return by - ay
    }
    return b.match_score - a.match_score
  })

  async function handleSearch(e) {
    e.preventDefault()
    if (!input.trim()) return
    setLoading(true)
    setQuery(input.trim())
    try {
      const res = await axios.post('/api/recommend', { query: input.trim(), top_n: topN })
      setResults(res.data)
    } catch (err) {
      alert('Search failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10">
      {/* Top bar */}
      <div className="flex items-center gap-4 mb-8">
        <button onClick={onBack} className="flex items-center gap-2 text-sm transition-opacity hover:opacity-70"
          style={{ color: 'var(--muted)' }}>
          <ArrowLeft size={16} /> Back
        </button>

        <form onSubmit={handleSearch} className="flex-1 flex gap-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--muted)' }} />
            <input value={input} onChange={e => setInput(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-lg text-sm outline-none"
              style={{
                background: 'var(--card)',
                border: '1.5px solid rgba(13,13,13,0.12)',
                color: 'var(--ink)',
                fontFamily: 'DM Sans, sans-serif'
              }} />
          </div>
          <select value={topN} onChange={e => setTopN(+e.target.value)}
            className="px-3 py-2.5 rounded-lg text-sm font-mono outline-none"
            style={{ background: 'var(--highlight)', color: 'var(--ink)' }}>
            {[5, 10, 15, 20].map(n => <option key={n} value={n}>Top {n}</option>)}
          </select>
          <button type="submit"
            className="px-5 py-2.5 rounded-lg text-sm font-display font-bold"
            style={{ background: 'var(--accent)', color: '#fff' }}>
            {loading ? '…' : 'Search'}
          </button>
        </form>
      </div>

      {/* Results header */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <h2 className="font-display text-2xl font-bold" style={{ color: 'var(--ink)' }}>
          {results.length} papers found
        </h2>
        <span className="font-mono text-sm" style={{ color: 'var(--muted)' }}>
          for "{query}"
        </span>

        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs" style={{ color: 'var(--muted)' }}>Sort by</span>
          <button onClick={() => setSortBy('match')}
            className="text-xs px-3 py-1.5 rounded-lg font-mono transition-all"
            style={{
              background: sortBy === 'match' ? 'var(--accent)' : 'var(--highlight)',
              color: sortBy === 'match' ? '#fff' : 'var(--muted)'
            }}>
            % Match
          </button>
          <button onClick={() => setSortBy('year')}
            className="text-xs px-3 py-1.5 rounded-lg font-mono transition-all"
            style={{
              background: sortBy === 'year' ? 'var(--accent)' : 'var(--highlight)',
              color: sortBy === 'year' ? '#fff' : 'var(--muted)'
            }}>
            Latest
          </button>
        </div>
      </div>

      {/* Cards */}
      <div className="flex flex-col gap-4">
        {sortedResults.map((paper, i) => (
          <PaperCard key={paper.id} paper={paper} rank={i + 1} />
        ))}
      </div>
    </main>
  )
}