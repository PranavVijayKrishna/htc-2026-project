'use client';
import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

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
  source_url?: string;
  image_url?: string;
  manufacturer?: string;
  distribution_details?: string;
  reviews_summary?: string;
  reviews_url?: string;
  components: {
    growth: number;
    relevance: number;
    cross_signal: number;
    competition_gap: number;
    recency: number;
  };
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

type SortKey  = 'score' | 'name' | 'growth' | 'confidence';
type ViewMode = 'list' | 'grid';
type Lang     = 'en' | 'zh';

const API_URL  = 'https://htc-2026-project.onrender.com/api/recommendations';
const CHAT_URL = 'https://htc-2026-project.onrender.com/api/chat';

const BARS = [
  { key: 'growth',          label: 'Trend Growth',    color: '#F59E0B' },
  { key: 'relevance',       label: 'Brand Fit',       color: '#14B8A6' },
  { key: 'competition_gap', label: 'Market Gap',      color: '#8B5CF6' },
  { key: 'cross_signal',    label: 'Validation',      color: '#F97316' },
  { key: 'recency',         label: 'Freshness',       color: '#22C55E' },
] as const;

const TR = {
  en: {
    dashTitle: 'Product Opportunities',
    dashSub: 'AI-powered trend intelligence for Prince of Peace buyers',
    type: 'Type', all: 'All', distribute: 'Distribute', develop: 'Develop',
    sortBy: 'Sort by', scoreOpt: 'Score (default)', nameOpt: 'Name (A–Z)',
    growthOpt: 'Growth Rate', confidenceOpt: 'Confidence',
    minScore: 'Min Score', loading: 'Loading...',
    learnMore: 'Learn More', backDash: '← Back to Dashboard',
    growthLabel: 'Growth Rate', actionLabel: 'Action',
    confidenceLabel: 'Confidence', popLineLabel: 'PoP Line',
    chatPlaceholder: 'Ask about suppliers, trends, competitors...',
    send: 'Send', aiBtn: 'Learn More with AI',
    whyMatters: 'Why this matters for PoP', scoreBreakdown: 'Score Breakdown',
    signalSources: 'Signal Sources', opportunityScore: 'Opportunity Score',
    growth: 'Growth', noResults: 'No results found',
    noResultsHint: 'Try lowering the minimum score or selecting a different type',
    couldNotLoad: 'Could not load data',
    chatHint: 'Ask about suppliers, formulation ideas, market size, or competitors.',
    navBack: '← Back', viewDashboard: 'View Dashboard',
    productImage: 'Product Image', manufacturer: 'Manufacturer',
    distribution: 'Distribution Details', reviewsSummary: 'Review Summary',
    viewReviews: 'View Detailed Reviews', noInfo: 'Not available',
    resultCount: (n: number) => `${n} result${n !== 1 ? 's' : ''}`,
    listView: 'List view', gridView: 'Grid view',
    developLabel: 'Develop under PoP', distributeLabel: 'Distribute',
    switchLang: '中文', openSource: 'View product source page',
    chatTitle: 'Ask anything about this opportunity',
  },
  zh: {
    dashTitle: '产品机会',
    dashSub: '为太平王消费品买家提供的AI趋势情报',
    type: '类型', all: '全部', distribute: '分销', develop: '开发',
    sortBy: '排序', scoreOpt: '得分（默认）', nameOpt: '名称（A-Z）',
    growthOpt: '增长率', confidenceOpt: '置信度',
    minScore: '最低分数', loading: '加载中...',
    learnMore: '了解更多', backDash: '← 返回仪表板',
    growthLabel: '增长率', actionLabel: '操作',
    confidenceLabel: '置信度', popLineLabel: 'PoP产品线',
    chatPlaceholder: '询问供应商、趋势、竞争对手...',
    send: '发送', aiBtn: '与AI深入探讨',
    whyMatters: '为何对太平王重要', scoreBreakdown: '得分细分',
    signalSources: '信号来源', opportunityScore: '机会得分',
    growth: '增长', noResults: '未找到结果',
    noResultsHint: '尝试降低最低分数或选择不同类型',
    couldNotLoad: '无法加载数据',
    chatHint: '询问供应商、配方创意、市场规模或竞争对手。',
    navBack: '← 返回', viewDashboard: '查看仪表板',
    productImage: '产品图片', manufacturer: '制造商',
    distribution: '分销详情', reviewsSummary: '评论摘要',
    viewReviews: '查看详细评论', noInfo: '暂无信息',
    resultCount: (n: number) => `${n} 条结果`,
    listView: '列表视图', gridView: '网格视图',
    developLabel: '在PoP下开发', distributeLabel: '分销',
    switchLang: 'EN', openSource: '查看产品来源页面',
    chatTitle: '询问有关此机会的任何问题',
  },
};

/* ─── lang hook ─────────────────────────────────────────────── */
function useLang(): [Lang, (l: Lang) => void] {
  const [lang, setLangState] = useState<Lang>('en');
  useEffect(() => {
    const saved = localStorage.getItem('sourceiq_lang') as Lang | null;
    if (saved === 'en' || saved === 'zh') setLangState(saved);
  }, []);
  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem('sourceiq_lang', l);
  };
  return [lang, setLang];
}

/* ─── shared nav ─────────────────────────────────────────────── */
function Nav({ lang, setLang, onBack }: { lang: Lang; setLang: (l: Lang) => void; onBack?: () => void }) {
  const t = TR[lang];
  return (
    <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-8 py-4">
        <Link href="/" className="flex items-center" title="SourceIQ Home">
          <span className="text-2xl font-black text-[#7C3AED] tracking-tight">SourceIQ</span>
        </Link>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setLang(lang === 'en' ? 'zh' : 'en')}
            title={lang === 'en' ? 'Switch to Chinese' : '切换到英文'}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-gray-200 bg-white hover:border-[#4F46E5] hover:text-[#4F46E5] text-gray-500 transition-colors">
            {t.switchLang}
          </button>
          {onBack ? (
            <button onClick={onBack} title={t.navBack}
              className="bg-[#4F46E5] hover:bg-[#4338CA] text-white text-sm font-semibold px-5 py-2 rounded-lg transition-colors">
              {t.navBack}
            </button>
          ) : (
            <Link href="/" title="Go to home page"
              className="bg-[#4F46E5] hover:bg-[#4338CA] text-white text-sm font-semibold px-5 py-2 rounded-lg transition-colors">
              {t.navBack}
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

/* ─── chat modal ─────────────────────────────────────────────── */
function ChatModal({ item, onClose, lang }: { item: Recommendation; onClose: () => void; lang: Lang }) {
  const t = TR[lang];
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: 'user', content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);
    try {
      const res  = await fetch(CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          term: item.term, angle: item.angle, growth_pct: item.growth_pct,
          category: item.pop_line, concept: item.concept, messages: newMessages,
        }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, could not connect. Please try again.' }]);
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/20 z-50 flex items-end sm:items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-lg flex flex-col border border-gray-100 shadow-2xl" style={{ height: '520px' }}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <div className="font-bold text-[#111827] uppercase tracking-wide">{item.term}</div>
            <div className="text-xs text-gray-400 mt-0.5">{t.chatTitle}</div>
          </div>
          <button onClick={onClose} title="Close chat" className="text-gray-300 hover:text-gray-600 text-xl leading-none transition-colors">&times;</button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-3">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 text-sm mt-10">
              <div className="w-10 h-10 rounded-full bg-[#EEF2FF] flex items-center justify-center mx-auto mb-3">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              {t.chatHint}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-[#4F46E5] text-white rounded-br-sm'
                  : 'bg-gray-100 text-[#111827] rounded-bl-sm'
              }`}>
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm text-gray-400">Thinking...</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="px-5 py-4 border-t border-gray-100 flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder={t.chatPlaceholder}
            className="flex-1 bg-gray-50 text-[#111827] text-sm px-4 py-2.5 rounded-xl border border-gray-200 focus:outline-none focus:border-[#4F46E5] transition-colors"
          />
          <button onClick={send} disabled={loading || !input.trim()} title={t.send}
            className="bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-colors">
            {t.send}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── skeleton ───────────────────────────────────────────────── */
function SkeletonCard({ grid }: { grid?: boolean }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-100 shadow-sm ${grid ? 'p-4' : 'p-4'}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="skel h-3 w-16 rounded-full mb-1.5" />
          <div className="skel h-5 w-32 mb-1" />
          <div className="skel h-3 w-48" />
        </div>
        <div className="skel h-10 w-12 rounded-xl ml-3" />
      </div>
      <div className="space-y-2 mb-3">
        {[1,2,3,4,5].map(i => (
          <div key={i}>
            <div className="flex justify-between mb-0.5">
              <div className="skel h-2 w-20" />
              <div className="skel h-2 w-8" />
            </div>
            <div className="skel h-1.5 w-full rounded-full" />
          </div>
        ))}
      </div>
      {!grid && (
        <div className="border-t border-gray-100 pt-2.5 grid grid-cols-2 gap-2">
          {[1,2,3,4].map(i => (
            <div key={i}>
              <div className="skel h-2 w-16 mb-1" />
              <div className="skel h-4 w-20" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── opportunity card ───────────────────────────────────────── */
function OpportunityCard({
  item, grid, onSelect, onChat, lang,
}: {
  item: Recommendation;
  grid: boolean;
  onSelect: () => void;
  onChat: (e: React.MouseEvent) => void;
  lang: Lang;
}) {
  const t = TR[lang];
  return (
    <div
      onClick={onSelect}
      title={`View details for ${item.term}`}
      className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-[#4F46E5]/30 transition-all cursor-pointer flex flex-col">
      <div className={grid ? 'p-3' : 'p-4'}>
        {/* Header */}
        <div className="flex items-start justify-between mb-1">
          <div className="flex-1 min-w-0 pr-3">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              {item.pop_line && (
                <span className="text-[10px] font-medium text-gray-400 bg-gray-50 border border-gray-100 px-2 py-0.5 rounded-full">
                  {item.pop_line}
                </span>
              )}
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                item.angle === 'develop' ? 'bg-[#EDE9FE] text-[#4F46E5]' : 'bg-[#DBEAFE] text-[#1D4ED8]'
              }`}>
                {item.angle === 'develop' ? t.developLabel : t.distributeLabel}
              </span>
            </div>
            {item.source_url ? (
              <a
                href={item.source_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={e => e.stopPropagation()}
                title={t.openSource}
                className={`font-extrabold text-[#4F46E5] hover:text-[#4338CA] uppercase tracking-wide leading-tight block transition-colors ${grid ? 'text-sm' : 'text-lg'}`}>
                {item.term}
              </a>
            ) : (
              <h2 className={`font-extrabold text-[#111827] uppercase tracking-wide leading-tight ${grid ? 'text-sm' : 'text-lg'}`}>
                {item.term}
              </h2>
            )}
            {item.concept && (
              <p className="text-xs text-gray-400 mt-0.5 leading-snug line-clamp-2">{item.concept}</p>
            )}
          </div>
          <div className="bg-amber-400 text-black font-extrabold rounded-xl flex-shrink-0 flex items-center justify-center"
            style={{ fontSize: grid ? '1rem' : '1.3rem', width: grid ? '44px' : '56px', height: grid ? '36px' : '48px' }}>
            {item.score.toFixed(1)}
          </div>
        </div>

        {/* Score bars */}
        <div className={`space-y-1.5 ${grid ? 'mt-2' : 'mt-3'}`}>
          {BARS.map(({ key, label, color }) => {
            const val = item.components[key as keyof typeof item.components] ?? 0;
            return (
              <div key={key}>
                <div className="flex justify-between items-center mb-0.5">
                  <span className="text-[10px] font-mono text-gray-400 tracking-wide">{label}</span>
                  <span className="text-[10px] font-mono font-bold" style={{ color }}>{val.toFixed(2)}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div className="h-1.5 rounded-full transition-all" style={{ width: `${Math.min(val * 100, 100)}%`, backgroundColor: color }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Meta grid — list only */}
        {!grid && (
          <>
            <div className="border-t border-gray-100 my-3" />
            <div className="grid grid-cols-2 gap-x-6 gap-y-2">
              <div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-gray-400">{t.growthLabel}</div>
                <div className="text-sm font-extrabold text-[#F59E0B] mt-0.5">+{item.growth_pct.toFixed(0)}%</div>
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-gray-400">{t.actionLabel}</div>
                <div className="text-sm font-extrabold text-[#111827] mt-0.5">
                  {item.angle === 'develop' ? t.developLabel : t.distributeLabel}
                </div>
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-gray-400">{t.confidenceLabel}</div>
                <div className="text-sm font-extrabold text-[#14B8A6] mt-0.5">{(item.confidence * 100).toFixed(0)}%</div>
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-gray-400">{t.popLineLabel}</div>
                <div className="text-sm font-extrabold text-[#111827] mt-0.5">
                  {item.pop_line
                    ? <><span className="text-[#14B8A6]">&#10003;</span> {item.pop_line}</>
                    : <span className="text-gray-300">—</span>}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Grid compact meta */}
        {grid && (
          <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
            <span className="text-[#F59E0B] font-bold">+{item.growth_pct.toFixed(0)}%</span>
            <span>{(item.confidence * 100).toFixed(0)}% conf.</span>
          </div>
        )}

        <div className="mt-2 flex justify-end">
          <button onClick={onChat} title={t.learnMore}
            className="text-xs bg-gray-50 hover:bg-[#4F46E5] text-gray-500 hover:text-white border border-gray-200 px-3 py-1.5 rounded-lg transition-colors font-medium">
            {t.learnMore}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── list row (table view) ─────────────────────────────────── */
function ListRow({
  item, index, onSelect, onChat, lang,
}: {
  item: Recommendation;
  index: number;
  onSelect: () => void;
  onChat: (e: React.MouseEvent) => void;
  lang: Lang;
}) {
  const t = TR[lang];
  return (
    <tr
      onClick={onSelect}
      title={`View details for ${item.term}`}
      className={`border-b border-gray-50 hover:bg-[#F5F7FF] cursor-pointer transition-colors group ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/40'}`}>

      {/* # */}
      <td className="py-3 pl-4 pr-2 text-xs text-gray-300 font-mono w-8 select-none">{index + 1}</td>

      {/* Product */}
      <td className="py-3 px-3">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full leading-none ${
            item.angle === 'develop' ? 'bg-[#EDE9FE] text-[#4F46E5]' : 'bg-[#DBEAFE] text-[#1D4ED8]'
          }`}>
            {item.angle === 'develop' ? t.developLabel : t.distributeLabel}
          </span>
          {item.pop_line && (
            <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full leading-none">{item.pop_line}</span>
          )}
        </div>
        {item.source_url ? (
          <a href={item.source_url} target="_blank" rel="noopener noreferrer"
            onClick={e => e.stopPropagation()} title={t.openSource}
            className="font-extrabold text-[#4F46E5] hover:text-[#4338CA] uppercase tracking-wide text-sm leading-tight block transition-colors">
            {item.term}
          </a>
        ) : (
          <div className="font-extrabold text-[#111827] uppercase tracking-wide text-sm leading-tight">{item.term}</div>
        )}
        {item.concept && (
          <div className="text-[11px] text-gray-400 mt-0.5 max-w-xs truncate">{item.concept}</div>
        )}
      </td>

      {/* Score */}
      <td className="py-3 px-3 text-center w-16">
        <span className="bg-amber-400 text-black font-extrabold text-sm px-2.5 py-1 rounded-lg inline-block tabular-nums">
          {item.score.toFixed(1)}
        </span>
      </td>

      {/* Growth */}
      <td className="py-3 px-3 text-right w-20">
        <span className="text-[#F59E0B] font-bold text-sm tabular-nums">+{item.growth_pct.toFixed(0)}%</span>
      </td>

      {/* Confidence */}
      <td className="py-3 px-3 text-right w-20">
        <span className="text-[#14B8A6] font-bold text-sm tabular-nums">{(item.confidence * 100).toFixed(0)}%</span>
      </td>

      {/* Sub-scores mini bars */}
      <td className="py-3 px-4 w-24">
        <div className="flex flex-col gap-1">
          {BARS.map(({ key, color }) => {
            const val = item.components[key as keyof typeof item.components] ?? 0;
            return (
              <div key={key} className="flex items-center gap-1.5">
                <div className="w-16 bg-gray-100 rounded-full h-1 flex-shrink-0">
                  <div className="h-1 rounded-full" style={{ width: `${Math.min(val * 100, 100)}%`, backgroundColor: color }} />
                </div>
                <span className="text-[9px] font-mono" style={{ color }}>{val.toFixed(2)}</span>
              </div>
            );
          })}
        </div>
      </td>

      {/* Actions */}
      <td className="py-3 pl-2 pr-4 text-right w-28">
        <button onClick={onChat} title={t.learnMore}
          className="text-xs bg-gray-50 hover:bg-[#4F46E5] text-gray-500 hover:text-white border border-gray-200 px-3 py-1.5 rounded-lg transition-colors font-medium whitespace-nowrap">
          {t.learnMore}
        </button>
      </td>
    </tr>
  );
}

/* ─── detail view ────────────────────────────────────────────── */
function DetailView({
  item, onChat, lang,
}: {
  item: Recommendation;
  onChat: () => void;
  lang: Lang;
}) {
  const t = TR[lang];
  const [showReviews, setShowReviews] = useState(false);

  return (
    <div className="max-w-7xl mx-auto px-8 py-6">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        {item.pop_line && (
          <span className="text-sm bg-white border border-gray-200 px-3 py-1 rounded-full text-gray-500 shadow-sm">
            {item.pop_line}
          </span>
        )}
        <span className={`text-sm px-3 py-1 rounded-full font-semibold ${
          item.angle === 'develop' ? 'bg-[#EDE9FE] text-[#4F46E5]' : 'bg-[#DBEAFE] text-[#1D4ED8]'
        }`}>
          {item.angle === 'develop' ? t.developLabel : t.distributeLabel}
        </span>
      </div>

      {item.source_url ? (
        <a href={item.source_url} target="_blank" rel="noopener noreferrer"
          title={t.openSource}
          className="text-3xl font-extrabold mb-1 text-[#4F46E5] hover:text-[#4338CA] uppercase tracking-wide block transition-colors">
          {item.term}
        </a>
      ) : (
        <h1 className="text-3xl font-extrabold mb-1 text-[#111827] uppercase tracking-wide">{item.term}</h1>
      )}
      {item.concept && <p className="text-gray-400 mb-4 text-sm">{item.concept}</p>}

      {/* Product image */}
      {item.image_url && (
        <div className="bg-white rounded-xl p-4 mb-4 border border-gray-100 shadow-sm">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">{t.productImage}</h2>
          <img src={item.image_url} alt={item.term}
            className="w-full max-h-56 object-contain rounded-lg" />
        </div>
      )}

      {/* Key stats */}
      <div className="bg-white rounded-xl p-4 mb-4 flex gap-6 flex-wrap border border-gray-100 shadow-sm">
        <div>
          <div className="text-3xl font-extrabold text-[#4F46E5]">
            {item.score.toFixed(1)}<span className="text-base text-gray-300 ml-1">/ 10</span>
          </div>
          <div className="text-gray-400 text-xs mt-0.5">{t.opportunityScore}</div>
        </div>
        <div>
          <div className="text-3xl font-extrabold text-[#F59E0B]">+{item.growth_pct.toFixed(0)}%</div>
          <div className="text-gray-400 text-xs mt-0.5">{t.growth}</div>
        </div>
        <div>
          <div className="text-3xl font-extrabold text-[#14B8A6]">{(item.confidence * 100).toFixed(0)}%</div>
          <div className="text-gray-400 text-xs mt-0.5">{t.confidenceLabel}</div>
        </div>
      </div>

      {/* Rationale */}
      <div className="bg-white rounded-xl p-4 mb-4 border border-gray-100 shadow-sm">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">{t.whyMatters}</h2>
        <p className="text-[#111827] leading-relaxed text-sm">{item.why_relevant}</p>
      </div>

      {/* Score breakdown */}
      <div className="bg-white rounded-xl p-4 mb-4 border border-gray-100 shadow-sm">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">{t.scoreBreakdown}</h2>
        {BARS.map(({ key, label, color }) => {
          const val = item.components[key as keyof typeof item.components] ?? 0;
          return (
            <div key={key} className="mb-2.5">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-500 font-mono">{label}</span>
                <span className="font-semibold" style={{ color }}>{val.toFixed(2)}</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div className="h-2 rounded-full" style={{ width: `${Math.min(val * 100, 100)}%`, backgroundColor: color }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Manufacturer */}
      {item.manufacturer && (
        <div className="bg-white rounded-xl p-4 mb-4 border border-gray-100 shadow-sm">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">{t.manufacturer}</h2>
          <p className="text-[#111827] text-sm leading-relaxed">{item.manufacturer}</p>
        </div>
      )}

      {/* Distribution details */}
      {item.distribution_details && (
        <div className="bg-white rounded-xl p-4 mb-4 border border-gray-100 shadow-sm">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">{t.distribution}</h2>
          <p className="text-[#111827] text-sm leading-relaxed">{item.distribution_details}</p>
        </div>
      )}

      {/* Reviews */}
      <div className="bg-white rounded-xl p-4 mb-4 border border-gray-100 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400">{t.reviewsSummary}</h2>
          {item.reviews_url && (
            <a href={item.reviews_url} target="_blank" rel="noopener noreferrer"
              title={t.viewReviews}
              className="text-xs text-[#4F46E5] hover:text-[#4338CA] font-medium transition-colors">
              {t.viewReviews} &#8594;
            </a>
          )}
        </div>
        {item.reviews_summary ? (
          <>
            <p className={`text-[#111827] text-sm leading-relaxed ${!showReviews ? 'line-clamp-3' : ''}`}>
              {item.reviews_summary}
            </p>
            {item.reviews_summary.length > 200 && (
              <button
                onClick={() => setShowReviews(v => !v)}
                title={showReviews ? 'Show less' : 'Show more reviews'}
                className="text-xs text-[#4F46E5] hover:text-[#4338CA] mt-1.5 font-medium transition-colors">
                {showReviews ? 'Show less' : 'Show more'}
              </button>
            )}
          </>
        ) : (
          <p className="text-gray-300 text-sm">{t.noInfo}</p>
        )}
      </div>

      {/* Signal sources */}
      <div className="bg-white rounded-xl p-4 mb-4 border border-gray-100 shadow-sm">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">{t.signalSources}</h2>
        <div className="flex gap-2 flex-wrap">
          {(Array.isArray(item.sources_seen) ? item.sources_seen : []).map(s => (
            <span key={s} className="bg-gray-50 border border-gray-200 px-3 py-1 rounded-full text-sm text-gray-600">{s}</span>
          ))}
        </div>
      </div>

      <button onClick={onChat} title={t.aiBtn}
        className="w-full bg-[#4F46E5] hover:bg-[#4338CA] text-white py-3 rounded-xl font-semibold text-sm transition-colors">
        {t.aiBtn}
      </button>
    </div>
  );
}

/* ─── main dashboard ─────────────────────────────────────────── */
export default function Dashboard() {
  const [lang, setLang]               = useLang();
  const [data, setData]               = useState<Recommendation[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');
  const [selectedAngle, setSelectedAngle] = useState('all');
  const [minScore, setMinScore]       = useState(0);
  const [sortKey, setSortKey]         = useState<SortKey>('score');
  const [viewMode, setViewMode]       = useState<ViewMode>('list');
  const [selected, setSelected]       = useState<Recommendation | null>(null);
  const [chatItem, setChatItem]       = useState<Recommendation | null>(null);

  const t = TR[lang];

  useEffect(() => {
    fetch(API_URL)
      .then(r => r.json())
      .then(json => { setData(Array.isArray(json) ? json : json.recommendations ?? []); setLoading(false); })
      .catch(() => { setError('Could not load recommendations. Please try again.'); setLoading(false); });
  }, []);

  const sortFns: Record<SortKey, (a: Recommendation, b: Recommendation) => number> = {
    score:      (a, b) => b.score      - a.score,
    name:       (a, b) => a.term.localeCompare(b.term),
    growth:     (a, b) => b.growth_pct - a.growth_pct,
    confidence: (a, b) => b.confidence - a.confidence,
  };

  const filtered = data
    .filter(item => {
      if (selectedAngle !== 'all' && item.angle !== selectedAngle) return false;
      if (item.score < minScore) return false;
      return true;
    })
    .sort(sortFns[sortKey]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#EEF2FF] via-[#F8FAFF] to-[#F0F4FF] text-[#111827] flex flex-col">
      {chatItem && <ChatModal item={chatItem} onClose={() => setChatItem(null)} lang={lang} />}

      {selected ? (
        <>
          <Nav lang={lang} setLang={setLang} onBack={() => setSelected(null)} />
          <DetailView
            item={selected}
            onChat={() => setChatItem(selected)}
            lang={lang}
          />
        </>
      ) : (
        <>
          <Nav lang={lang} setLang={setLang} />
          {/* Page header + toolbar — sticky below nav */}
          <div className="bg-white/90 backdrop-blur-sm border-b border-gray-100 sticky top-[65px] z-30">
            <div className="max-w-7xl mx-auto px-8 py-3">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h1 className="text-xl font-extrabold text-[#111827]">{t.dashTitle}</h1>
                  <p className="text-xs text-gray-400 mt-0.5">{t.dashSub}</p>
                </div>
                <div className="text-sm text-gray-400">
                  {loading ? t.loading : t.resultCount(filtered.length)}
                </div>
              </div>

              {/* Toolbar */}
              <div className="flex flex-wrap gap-3 items-end">
                {/* Angle filter */}
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">{t.type}</div>
                  <div className="flex gap-1">
                    {(['all', 'distribute', 'develop'] as const).map(v => (
                      <button key={v} onClick={() => setSelectedAngle(v)}
                        title={v === 'all' ? 'Show all opportunities' : v === 'distribute' ? 'Filter: distribute' : 'Filter: develop'}
                        className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors capitalize ${
                          selectedAngle === v
                            ? 'bg-[#4F46E5] text-white border-[#4F46E5]'
                            : 'bg-white text-gray-500 border-gray-200 hover:border-[#4F46E5] hover:text-[#4F46E5]'
                        }`}>
                        {v === 'all' ? t.all : v === 'distribute' ? t.distribute : t.develop}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sort */}
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">{t.sortBy}</div>
                  <select value={sortKey} onChange={e => setSortKey(e.target.value as SortKey)}
                    title="Change sort order"
                    className="text-xs bg-gray-50 text-[#111827] px-3 py-1.5 rounded-lg border border-gray-200 focus:outline-none focus:border-[#4F46E5] transition-colors">
                    <option value="score">{t.scoreOpt}</option>
                    <option value="name">{t.nameOpt}</option>
                    <option value="growth">{t.growthOpt}</option>
                    <option value="confidence">{t.confidenceOpt}</option>
                  </select>
                </div>

                {/* Min score */}
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-1">
                    {t.minScore}: <span className="text-[#4F46E5]">{minScore}</span>
                  </div>
                  <input type="range" min={0} max={10} step={0.5} value={minScore}
                    onChange={e => setMinScore(Number(e.target.value))}
                    title={`Minimum score: ${minScore}`}
                    className="w-28 accent-[#4F46E5]" />
                </div>

                <div className="flex-1" />

                {/* View toggle */}
                <div className="flex gap-1 border border-gray-200 rounded-lg p-1 bg-gray-50">
                  <button onClick={() => setViewMode('list')} title={t.listView}
                    className={`p-1.5 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white shadow-sm text-[#4F46E5]' : 'text-gray-400 hover:text-gray-600'}`}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <rect x="2" y="3" width="12" height="2" rx="1" fill="currentColor"/>
                      <rect x="2" y="7" width="12" height="2" rx="1" fill="currentColor"/>
                      <rect x="2" y="11" width="12" height="2" rx="1" fill="currentColor"/>
                    </svg>
                  </button>
                  <button onClick={() => setViewMode('grid')} title={t.gridView}
                    className={`p-1.5 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-white shadow-sm text-[#4F46E5]' : 'text-gray-400 hover:text-gray-600'}`}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <rect x="2" y="2" width="5" height="5" rx="1" fill="currentColor"/>
                      <rect x="9" y="2" width="5" height="5" rx="1" fill="currentColor"/>
                      <rect x="2" y="9" width="5" height="5" rx="1" fill="currentColor"/>
                      <rect x="9" y="9" width="5" height="5" rx="1" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Cards area — matches toolbar width */}
          <div className="w-full">
          <div className="max-w-7xl mx-auto px-8 py-4">
              {loading && viewMode === 'grid' && (
                <div className="grid grid-cols-2 gap-3">
                  {[1,2,3,4,5,6].map(i => <SkeletonCard key={i} grid />)}
                </div>
              )}
              {loading && viewMode === 'list' && (
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                  {[1,2,3,4,5,6].map(i => (
                    <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-gray-50">
                      <div className="skel h-3 w-4 rounded" />
                      <div className="flex-1">
                        <div className="skel h-3 w-24 rounded mb-1.5" />
                        <div className="skel h-4 w-40 rounded mb-1" />
                        <div className="skel h-2.5 w-56 rounded" />
                      </div>
                      <div className="skel h-8 w-12 rounded-lg" />
                      <div className="skel h-4 w-12 rounded" />
                      <div className="skel h-4 w-12 rounded" />
                      <div className="flex flex-col gap-1 w-24">
                        {[1,2,3,4,5].map(j => <div key={j} className="skel h-1 rounded-full" />)}
                      </div>
                      <div className="skel h-7 w-20 rounded-lg" />
                    </div>
                  ))}
                </div>
              )}

              {error && (
                <div className="text-center py-12 text-red-500 bg-white rounded-xl border border-red-100 shadow-sm">
                  <div className="font-semibold mb-1">{t.couldNotLoad}</div>
                  <div className="text-sm">{error}</div>
                </div>
              )}

              {!loading && !error && filtered.length === 0 && (
                <div className="text-center py-12 text-gray-400 bg-white rounded-xl border border-gray-100 shadow-sm">
                  <div className="text-lg font-semibold mb-1 text-[#111827]">{t.noResults}</div>
                  <div className="text-sm">{t.noResultsHint}</div>
                </div>
              )}

              {!loading && !error && filtered.length > 0 && viewMode === 'grid' && (
                <div className="grid grid-cols-2 gap-3">
                  {filtered.map((item, i) => (
                    <OpportunityCard
                      key={i} item={item} grid
                      onSelect={() => setSelected(item)}
                      onChat={e => { e.stopPropagation(); setChatItem(item); }}
                      lang={lang}
                    />
                  ))}
                </div>
              )}
              {!loading && !error && filtered.length > 0 && viewMode === 'list' && (
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50/60">
                        <th className="py-2.5 pl-4 pr-2 w-8" />
                        <th className="py-2.5 px-3 text-[10px] font-bold uppercase tracking-widest text-gray-400">Product</th>
                        <th className="py-2.5 px-3 text-[10px] font-bold uppercase tracking-widest text-gray-400 text-center w-16">Score</th>
                        <th className="py-2.5 px-3 text-[10px] font-bold uppercase tracking-widest text-gray-400 text-right w-20">Growth</th>
                        <th className="py-2.5 px-3 text-[10px] font-bold uppercase tracking-widest text-gray-400 text-right w-20">Confidence</th>
                        <th className="py-2.5 px-4 text-[10px] font-bold uppercase tracking-widest text-gray-400 w-24">Signals</th>
                        <th className="py-2.5 pl-2 pr-4 w-28" />
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((item, i) => (
                        <ListRow
                          key={i} item={item} index={i}
                          onSelect={() => setSelected(item)}
                          onChat={e => { e.stopPropagation(); setChatItem(item); }}
                          lang={lang}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
          </div>
          </div>
        </>
      )}
    </div>
  );
}
