'use client';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-gray-800">
        <span className="text-lg font-bold tracking-tight text-green-400">PoP Intelligence</span>
        <div className="flex items-center gap-6">
          <a href="#how-it-works" className="text-sm text-gray-400 hover:text-white transition-colors">How it Works</a>
          <a href="#features" className="text-sm text-gray-400 hover:text-white transition-colors">Features</a>
          <Link href="/dashboard"
            className="bg-green-600 hover:bg-green-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
            ⚡ Launch Dashboard
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 py-24">
        <div className="inline-flex items-center gap-2 bg-green-950 text-green-400 text-xs font-semibold px-4 py-1.5 rounded-full mb-8 border border-green-800">
          ⚡ AI-Powered Trend Intelligence
        </div>

        <h1 className="text-5xl sm:text-6xl font-extrabold leading-tight max-w-3xl mb-6">
          Discover{' '}
          <span className="text-green-400">product opportunities</span>
          {' '}built around your market.
        </h1>

        <p className="text-lg text-gray-400 max-w-xl mb-10 leading-relaxed">
          Tell us what consumers are searching for. PoP Intelligence surfaces the trending ingredients and formats you should be sourcing or developing — ranked by growth, relevance, and market gap.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <Link href="/dashboard"
            className="bg-green-600 hover:bg-green-500 text-white px-8 py-3.5 rounded-xl text-base font-semibold transition-colors">
            ⚡ View Opportunities
          </Link>
          <a href="#how-it-works"
            className="text-gray-400 hover:text-white text-sm transition-colors">
            ↓ See How It Works
          </a>
        </div>

        {/* Stats bar */}
        <div className="mt-20 flex flex-wrap justify-center gap-10 text-center">
          <div>
            <div className="text-3xl font-bold text-white">50+</div>
            <div className="text-sm text-gray-500 mt-1">Trends tracked weekly</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-white">3</div>
            <div className="text-sm text-gray-500 mt-1">Live data sources</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-white">Google Trends, iHerb, Amazon</div>
            <div className="text-sm text-gray-500 mt-1">Signal coverage</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-white">Real-time</div>
            <div className="text-sm text-gray-500 mt-1">AI rationale per opportunity</div>
          </div>
        </div>
      </main>

      {/* How it works */}
      <section id="how-it-works" className="px-8 py-20 border-t border-gray-800 max-w-5xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-center mb-12">How It Works</h2>
        <div className="grid sm:grid-cols-3 gap-8">
          {[
            {
              step: '01',
              title: 'We scan the signals',
              desc: 'Google Trends, iHerb bestsellers, and Amazon rankings are scraped and unified into a single trend feed.',
            },
            {
              step: '02',
              title: 'AI scores each opportunity',
              desc: 'Every trend is scored on growth momentum, PoP relevance, competitive gap, and cross-source validation.',
            },
            {
              step: '03',
              title: 'Buyers act with confidence',
              desc: 'Each card shows whether to distribute an existing product or develop a new PoP line — with AI-sourced rationale.',
            },
          ].map(({ step, title, desc }) => (
            <div key={step} className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <div className="text-green-400 font-mono text-sm mb-3">{step}</div>
              <h3 className="font-semibold text-white mb-2">{title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-8 py-20 border-t border-gray-800 max-w-5xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-center mb-12">Features</h2>
        <div className="grid sm:grid-cols-2 gap-6">
          {[
            { icon: '📈', title: 'Live Trend Scoring', desc: 'Composite scores from growth rate, search volume, and commercial validation.' },
            { icon: '🔬', title: 'Develop vs. Distribute', desc: 'Instantly know whether to extend a PoP line or source an existing product.' },
            { icon: '💬', title: 'Dive Deeper Chatbot', desc: 'Ask the AI about suppliers, formulations, competitors — per trend card.' },
            { icon: '⚙️', title: 'Live Weight Tuning', desc: 'Shift scoring weights in real time and watch rankings re-order instantly.' },
          ].map(({ icon, title, desc }) => (
            <div key={title} className="flex gap-4 bg-gray-900 rounded-xl p-5 border border-gray-800">
              <div className="text-2xl">{icon}</div>
              <div>
                <div className="font-semibold text-white mb-1">{title}</div>
                <div className="text-sm text-gray-400 leading-relaxed">{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="text-center px-8 py-20 border-t border-gray-800">
        <h2 className="text-3xl font-bold mb-4">Ready to find your next product?</h2>
        <p className="text-gray-400 mb-8">Ranked opportunities for Prince of Peace buyers — updated weekly.</p>
        <Link href="/dashboard"
          className="bg-green-600 hover:bg-green-500 text-white px-8 py-3.5 rounded-xl text-base font-semibold transition-colors">
          ⚡ Launch Dashboard
        </Link>
      </section>

      <footer className="text-center text-xs text-gray-600 py-6 border-t border-gray-800">
        PoP Intelligence · Built at Hack the Coast 2026 · Prince of Peace CPG
      </footer>
    </div>
  );
}
