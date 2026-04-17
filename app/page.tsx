'use client';
import { useState, useEffect } from 'react';

interface Recommendation {
  term: string;
  score: number;
  growth_pct: number;
  angle: string;
  pop_line: string;
  concept: string;
  why_relevant: string;
  confidence: number;
  sources_seen: string[];
  components: {
    growth: number;
    relevance: number;
    cross_signal: number;
    competition_gap: number;
    recency: number;
  };
}

const API_URL = 'https://htc-2026-project.onrender.com/api/recommendations';

export default function Dashboard() {
  const [data, setData] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedAngle, setSelectedAngle] = useState('all');
  const [minScore, setMinScore] = useState(0);
  const [selected, setSelected] = useState<Recommendation | null>(null);

  useEffect(() => {
    fetch(API_URL)
      .then(r => r.json())
      .then(json => {
        setData(Array.isArray(json) ? json : json.recommendations ?? []);
        setLoading(false);
      })
      .catch(() => {
        setError('Could not load recommendations. Please try again.');
        setLoading(false);
      });
  }, []);

  const filtered = data.filter(item => {
    if (selectedAngle !== 'all' && item.angle !== selectedAngle) return false;
    if (item.score < minScore) return false;
    return true;
  });

  const getSources = (sources: string[]) =>
    Array.isArray(sources) ? sources : [];

  if (selected) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-6">
        <button onClick={() => setSelected(null)} className="mb-6 text-sm text-gray-400 hover:text-white flex items-center gap-2">
          ← Back to Dashboard
        </button>
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            {selected.pop_line && <span className="text-sm bg-gray-800 px-3 py-1 rounded-full">{selected.pop_line}</span>}
            <span className={`text-sm px-3 py-1 rounded-full font-semibold ${selected.angle === 'develop' ? 'bg-purple-900 text-purple-200' : 'bg-blue-900 text-blue-200'}`}>
              {selected.angle === 'develop' ? '🔬 Develop under PoP' : '📦 Distribute'}
            </span>
          </div>
          <h1 className="text-3xl font-bold mb-1">{selected.term}</h1>
          {selected.concept && <p className="text-gray-400 mb-4">{selected.concept}</p>}

          <div className="bg-gray-900 rounded-xl p-5 mb-4 flex gap-6 flex-wrap">
            <div>
              <div className="text-4xl font-bold text-green-400">{selected.score.toFixed(1)} <span className="text-lg text-gray-400">/ 10</span></div>
              <div className="text-gray-400 text-sm">Opportunity Score</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-400">+{selected.growth_pct.toFixed(0)}%</div>
              <div className="text-gray-400 text-sm">Growth</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-yellow-400">{(selected.confidence * 100).toFixed(0)}%</div>
              <div className="text-gray-400 text-sm">Confidence</div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-xl p-5 mb-4">
            <h2 className="font-semibold mb-2 text-gray-300">Why this matters for PoP</h2>
            <p className="text-gray-100 leading-relaxed">{selected.why_relevant}</p>
          </div>

          <div className="bg-gray-900 rounded-xl p-5 mb-4">
            <h2 className="font-semibold mb-3 text-gray-300">Score Breakdown</h2>
            {Object.entries(selected.components).map(([key, val]) => (
              <div key={key} className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400 capitalize">{key.replace('_', ' ')}</span>
                  <span className="text-white">{(Number(val) * 10).toFixed(1)}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div className="bg-green-400 h-1.5 rounded-full" style={{ width: `${Number(val) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>

          <div className="bg-gray-900 rounded-xl p-5 mb-4">
            <h2 className="font-semibold mb-3 text-gray-300">Signal Sources</h2>
            <div className="flex gap-2 flex-wrap">
              {getSources(selected.sources_seen).map(s => (
                <span key={s} className="bg-gray-700 px-3 py-1 rounded-full text-sm">{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-1">Product Opportunity Dashboard</h1>
          <p className="text-gray-400">AI-powered trend intelligence for Prince of Peace buyers</p>
        </div>

        <div className="bg-gray-900 rounded-xl p-4 mb-6 flex flex-wrap gap-4 items-center">
          <div>
            <div className="text-xs text-gray-400 mb-1">Opportunity Type</div>
            <select value={selectedAngle} onChange={e => setSelectedAngle(e.target.value)}
              className="bg-gray-800 text-white text-sm px-3 py-1.5 rounded-lg border border-gray-700">
              <option value="all">All</option>
              <option value="distribute">Distribute</option>
              <option value="develop">Develop</option>
            </select>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Min Score: {minScore}</div>
            <input type="range" min={0} max={10} step={0.5} value={minScore}
              onChange={e => setMinScore(Number(e.target.value))}
              className="w-32 accent-green-400" />
          </div>
          <div className="ml-auto text-sm text-gray-400">
            {loading ? 'Loading...' : `${filtered.length} opportunities`}
          </div>
        </div>

        {loading && (
          <div className="text-center py-16 text-gray-500">
            <div className="text-4xl mb-3">⏳</div>
            <div className="text-lg">Loading opportunities...</div>
          </div>
        )}

        {error && (
          <div className="text-center py-16 text-red-400">
            <div className="text-4xl mb-3">⚠️</div>
            <div className="text-lg">{error}</div>
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <div className="text-4xl mb-3">🔍</div>
            <div className="text-lg font-medium mb-1">No results found</div>
            <div className="text-sm">Try lowering the minimum score or selecting a different type</div>
          </div>
        )}

        {!loading && !error && (
          <div className="flex flex-col gap-4">
            {filtered.map((item, i) => (
              <div key={i} onClick={() => setSelected(item)}
                className="bg-gray-900 hover:bg-gray-800 cursor-pointer rounded-xl p-5 transition-colors border border-gray-800 hover:border-gray-600">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {item.pop_line && <span className="text-xs bg-gray-800 px-2 py-0.5 rounded-full text-gray-300">{item.pop_line}</span>}
                      <span className="text-xs text-blue-300">+{item.growth_pct.toFixed(0)}% growth</span>
                    </div>
                    <h2 className="text-xl font-bold">{item.term}</h2>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-400">{item.score.toFixed(1)}</div>
                    <div className="text-xs text-gray-500">/ 10</div>
                  </div>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed mb-3">{item.why_relevant}</p>
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex gap-2 flex-wrap">
                    {getSources(item.sources_seen).map(s => (
                      <span key={s} className="text-xs bg-gray-700 px-2 py-0.5 rounded-full text-gray-300">{s}</span>
                    ))}
                  </div>
                  <span className={`text-sm px-3 py-1 rounded-full font-semibold ${item.angle === 'develop' ? 'bg-purple-900 text-purple-200' : 'bg-blue-900 text-blue-200'}`}>
                    {item.angle === 'develop' ? '🔬 Develop under PoP' : '📦 Distribute'}
                  </span>
                </div>
                {item.concept && <div className="mt-3 text-xs text-green-400 font-medium">→ {item.concept}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}