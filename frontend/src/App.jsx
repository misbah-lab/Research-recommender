import { useState } from 'react'
import Header from './components/Header.jsx'
import SearchPage from './pages/SearchPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'

export default function App() {
  const [results, setResults] = useState(null)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      {!results
        ? <SearchPage setResults={setResults} setQuery={setQuery} setLoading={setLoading} loading={loading} />
        : <ResultsPage results={results} query={query} onBack={() => setResults(null)} setResults={setResults} setLoading={setLoading} loading={loading} setQuery={setQuery} />
      }
    </div>
  )
}
