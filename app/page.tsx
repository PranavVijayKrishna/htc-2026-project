'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';

type Lang = 'en' | 'zh';

const LP = {
  en: {
    goodAfternoon: 'Good afternoon',
    trends: 'Trends', sources: 'Sources', avgScore: 'Avg Score',
    heroTitle: <>AI-Powered Product<br />Intelligence for<br /><span className="text-[#7C3AED]">CPG Buyers</span></>,
    heroSubtitle: 'SourceIQ discovers which health and wellness trends Prince of Peace should source or develop — ranked by AI across Google Trends, iHerb, and Amazon, updated weekly.',
    viewDashboard: 'View Dashboard',
    seeHow: 'See How It Works',
    noLogin: 'No login required',
    liveData: 'Live data from trusted sources',
    process: 'Process',
    howItWorks: 'How It Works',
    steps: [
      { step: '01', title: 'Scan the signals', desc: 'Google Trends, iHerb bestsellers, and Amazon rankings are scraped and unified into a single trend feed.' },
      { step: '02', title: 'AI scores each opportunity', desc: 'Every trend is scored on growth, PoP relevance, competitive gap, and cross-source validation.' },
      { step: '03', title: 'Buyers act with confidence', desc: 'Each card tells you whether to distribute an existing product or develop a new PoP line.' },
    ],
    capabilities: 'Capabilities',
    features: 'Features',
    featureList: [
      { title: 'Live Trend Scoring',    desc: 'Composite scores from growth rate, search volume, and commercial validation — updated every pipeline run.' },
      { title: 'Develop vs. Distribute', desc: 'Instantly know whether to extend a PoP product line or source an existing product from a supplier.' },
      { title: 'Learn More Chatbot',   desc: 'Ask the AI about suppliers, formulations, or competitors — one chat panel per trend card.' },
      { title: 'Live Weight Tuning',    desc: 'Shift scoring weights in real time and watch opportunity rankings re-order instantly.' },
    ],
    cta: 'Ready to find your next product?',
    ctaSub: 'Ranked opportunities for Prince of Peace buyers — updated weekly.',
    footer: 'SourceIQ · Hack the Coast 2026 · Prince of Peace CPG',
    switchLang: '中文',
  },
  zh: {
    goodAfternoon: '下午好',
    trends: '趋势', sources: '来源', avgScore: '平均分',
    heroTitle: <>面向消费品买家的<br />AI产品智能分析<br /><span className="text-[#7C3AED]">实时趋势发现</span></>,
    heroSubtitle: 'SourceIQ发现太平王应采购或开发的健康与保健趋势——通过AI跨谷歌趋势、iHerb和亚马逊排名，每周更新。',
    viewDashboard: '查看仪表板',
    seeHow: '了解工作原理',
    noLogin: '无需登录',
    liveData: '来自可信来源的实时数据',
    process: '流程',
    howItWorks: '工作原理',
    steps: [
      { step: '01', title: '扫描信号', desc: '抓取谷歌趋势、iHerb畅销榜和亚马逊排名，统一汇聚成单一趋势数据流。' },
      { step: '02', title: 'AI评分每个机会', desc: '每个趋势按增长、PoP相关性、竞争差距和跨来源验证进行评分。' },
      { step: '03', title: '买家信心决策', desc: '每张卡片告诉您是分销现有产品还是开发新的PoP产品线。' },
    ],
    capabilities: '能力',
    features: '功能',
    featureList: [
      { title: '实时趋势评分', desc: '综合增长率、搜索量和商业验证的综合得分——每次管道运行后更新。' },
      { title: '开发与分销', desc: '即时了解是扩展PoP产品线还是从供应商采购现有产品。' },
      { title: '深入了解聊天机器人', desc: '向AI询问供应商、配方或竞争对手——每个趋势卡片一个聊天面板。' },
      { title: '实时权重调整', desc: '实时调整评分权重，即时重新排序机会排名。' },
    ],
    cta: '准备好发现您的下一款产品了吗？',
    ctaSub: '为太平王买家提供的排名机会——每周更新。',
    footer: 'SourceIQ · 黑客海岸 2026 · 太平王消费品',
    switchLang: 'EN',
  },
};

function DashboardPreview({ lang }: { lang: Lang }) {
  const t = LP[lang];
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const h = new Date().getHours();
    if (lang === 'zh') {
      setGreeting(h >= 5 && h < 12 ? '早上好！' : h < 18 ? '下午好！' : '晚上好！');
    } else {
      setGreeting(h >= 5 && h < 12 ? 'Good morning!' : h < 18 ? 'Good afternoon!' : 'Good evening!');
    }
  }, [lang]);

  const trends = [
    { term: 'SPERMIDINE',  score: 9.2, bars: [0.88, 0.72, 0.80, 0.65, 1.00] },
    { term: 'UROLITHIN A', score: 8.7, bars: [0.82, 0.68, 0.75, 0.58, 1.00] },
  ];
  const barColors = ['#F59E0B', '#14B8A6', '#8B5CF6', '#F97316', '#22C55E'];
  const barLabels = ['Trend Growth', 'Brand Fit', 'Market Gap', 'Validation', 'Freshness'];

  return (
    <div className="bg-white rounded-2xl p-5 w-full max-w-md border border-gray-100 glow-breathe">
      <div className="text-xs text-gray-400 font-medium mb-4">{greeting}</div>
      <div className="grid grid-cols-3 gap-2 mb-4">
        {[['50+', t.trends], ['3', t.sources], ['8.4', t.avgScore]].map(([v, l]) => (
          <div key={l} className="bg-gray-50 rounded-xl p-3 text-center border border-gray-100">
            <div className="text-lg font-extrabold text-gray-900">{v}</div>
            <div className="text-[10px] text-gray-400 mt-0.5">{l}</div>
          </div>
        ))}
      </div>
      <div className="space-y-2">
        {trends.map(({ term, score, bars }) => (
          <div key={term} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-bold text-gray-900 uppercase tracking-wide">{term}</span>
              <span className="bg-amber-400 text-black text-xs font-extrabold px-2 py-0.5 rounded-lg">{score}</span>
            </div>
            {bars.map((val, i) => (
              <div key={i} className="flex items-center gap-2 mb-1">
                <span className="text-[10px] text-gray-400 w-12">{barLabels[i]}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-1">
                  <div className="h-1 rounded-full" style={{ width: `${val * 100}%`, backgroundColor: barColors[i] }} />
                </div>
                <span className="text-[10px] font-mono" style={{ color: barColors[i] }}>{val.toFixed(2)}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const [lang, setLang] = useState<Lang>('en');

  useEffect(() => {
    const saved = localStorage.getItem('sourceiq_lang') as Lang | null;
    if (saved === 'en' || saved === 'zh') setLang(saved);
  }, []);

  const toggleLang = () => {
    const next: Lang = lang === 'en' ? 'zh' : 'en';
    setLang(next);
    localStorage.setItem('sourceiq_lang', next);
  };

  const t = LP[lang];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#EEF2FF] via-[#F8FAFF] to-[#F0F4FF] text-[#111827] flex flex-col">

      {/* Nav */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-8 py-4">
          <Link href="/" className="flex items-center" title="SourceIQ Home">
            <span className="text-2xl font-black text-[#7C3AED] tracking-tight">SourceIQ</span>
          </Link>

          <div className="hidden sm:flex items-center gap-8">
            <a href="#how-it-works" className="text-sm text-gray-500 hover:text-gray-900 transition-colors" title="How SourceIQ works">How It Works</a>
            <a href="#features" className="text-sm text-gray-500 hover:text-gray-900 transition-colors" title="SourceIQ features">Features</a>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleLang}
              title={lang === 'en' ? 'Switch to Chinese' : '切换到英文'}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-200 bg-white hover:border-[#4F46E5] hover:text-[#4F46E5] text-gray-500 transition-colors">
              {t.switchLang}
            </button>
            <Link href="/dashboard" title="Open the opportunity dashboard"
              className="bg-[#4F46E5] hover:bg-[#4338CA] text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
              {t.viewDashboard}
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 max-w-7xl mx-auto px-8 py-16 flex items-center gap-16 w-full">
        <div className="flex-1 max-w-xl">
          <div className="flex items-center gap-5 mb-8 text-sm text-gray-400 font-medium">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
              Google Trends
            </span>
            <span className="text-gray-200">|</span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
              iHerb
            </span>
            <span className="text-gray-200">|</span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-orange-400 inline-block" />
              Amazon
            </span>
          </div>

          <h1 className="text-[clamp(2.4rem,5vw,3.6rem)] font-extrabold leading-[1.1] tracking-tight mb-6">
            {t.heroTitle}
          </h1>

          <p className="text-lg text-gray-500 mb-8 leading-relaxed">{t.heroSubtitle}</p>

          <div className="flex items-center gap-4 mb-3 flex-wrap">
            <Link href="/dashboard" title="Open the opportunity dashboard"
              className="bg-[#4F46E5] hover:bg-[#4338CA] text-white px-8 py-3.5 rounded-xl text-base font-semibold transition-colors">
              {t.viewDashboard}
            </Link>
            <a href="#how-it-works" title="Learn how SourceIQ works"
              className="border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 px-8 py-3.5 rounded-xl text-base font-semibold transition-colors">
              {t.seeHow}
            </a>
          </div>
          <p className="text-xs text-gray-400">{t.noLogin}</p>
        </div>

        <div className="flex-1 hidden lg:flex justify-center items-center">
          <DashboardPreview lang={lang} />
        </div>
      </main>


      {/* How it works */}
      <section id="how-it-works" className="py-20 px-8">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-bold tracking-[0.2em] uppercase text-[#4F46E5] mb-3 text-center">{t.process}</p>
          <h2 className="text-3xl font-extrabold mb-12 text-center text-[#111827]">{t.howItWorks}</h2>
          <div className="grid sm:grid-cols-3 gap-6">
            {t.steps.map(({ step, title, desc }) => (
              <div key={step} className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm hover:shadow-md hover:border-[#4F46E5]/30 transition-all">
                <div className="text-[#4F46E5] font-mono text-xs tracking-widest font-bold mb-4">{step}</div>
                <h3 className="font-bold text-[#111827] mb-2">{title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-8 bg-white/60">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-bold tracking-[0.2em] uppercase text-[#4F46E5] mb-3 text-center">{t.capabilities}</p>
          <h2 className="text-3xl font-extrabold mb-12 text-center text-[#111827]">{t.features}</h2>
          <div className="grid sm:grid-cols-2 gap-5">
            {t.featureList.map(({ title, desc }) => (
              <div key={title} className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm hover:shadow-md hover:border-[#4F46E5]/30 transition-all">
                <div className="font-bold text-[#111827] mb-1">{title}</div>
                <div className="text-sm text-gray-500 leading-relaxed">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-8 text-center">
        <h2 className="text-4xl font-extrabold mb-4 text-[#111827]">{t.cta}</h2>
        <p className="text-gray-500 mb-8">{t.ctaSub}</p>
        <Link href="/dashboard" title="Open the opportunity dashboard"
          className="bg-[#4F46E5] hover:bg-[#4338CA] text-white font-semibold px-10 py-4 rounded-xl text-base transition-colors">
          {t.viewDashboard}
        </Link>
      </section>

      <footer className="text-center text-xs text-gray-400 py-6 border-t border-gray-100 bg-white/40 tracking-widest uppercase">
        {t.footer}
      </footer>
    </div>
  );
}
