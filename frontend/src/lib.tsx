import { useEffect, useState, ReactNode } from 'react'
import ReactECharts from 'echarts-for-react'

export async function api<T = any>(path: string, body?: any, method?: string): Promise<T> {
  const r = await fetch('/api' + path, body !== undefined ? { method: method || 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : { method: method || 'GET' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
export function useApi<T = any>(path: string | null, deps: any[] = []): [T | null, boolean, () => void] {
  const [d, setD] = useState<T | null>(null); const [l, setL] = useState(true); const [n, setN] = useState(0)
  useEffect(() => { if (!path) return; setL(true); api<T>(path).then(setD).catch(() => setD(null)).finally(() => setL(false)) }, [path, n, ...deps])
  return [d, l, () => setN(x => x + 1)]
}
export const usd = (v: number | null | undefined, d = 0) => v == null ? '—' : v.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: d })
export const pct = (v: number | null | undefined, d = 1) => v == null ? '—' : (v * 100).toFixed(d) + '%'
export const compact = (v: number) => Math.abs(v) >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : Math.abs(v) >= 1e3 ? (v / 1e3).toFixed(0) + 'k' : v.toFixed(0)
export const PALETTE = ['#8b5cf6', '#22d3ee', '#34d399', '#f59e0b', '#f43f5e', '#60a5fa', '#a3e635', '#e879f9', '#fb923c', '#94a3b8', '#2dd4bf', '#facc15']

export const base = (extra: any = {}) => ({
  backgroundColor: 'transparent', color: PALETTE, textStyle: { color: '#a1a1aa', fontFamily: 'Inter, system-ui' },
  grid: { left: 56, right: 24, top: 36, bottom: 56, containLabel: false },
  tooltip: { trigger: 'axis', backgroundColor: '#18181b', borderColor: '#3f3f46', textStyle: { color: '#e4e4e7' }, valueFormatter: (v: number) => usd(v) },
  legend: { top: 0, textStyle: { color: '#a1a1aa' }, type: 'scroll' },
  xAxis: { type: 'category', axisLine: { lineStyle: { color: '#3f3f46' } } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#27272a' } }, axisLabel: { formatter: (v: number) => compact(v) } },
  ...extra,
})
export const zoom = [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 8, borderColor: '#3f3f46', fillerColor: 'rgba(139,92,246,.15)', textStyle: { color: '#71717a' } }]

export function Chart({ option, h = 320, onEvents }: { option: any; h?: number; onEvents?: any }) {
  return <ReactECharts option={{ animationDuration: 300, ...option }} style={{ height: h, width: '100%' }} notMerge lazyUpdate onEvents={onEvents} theme="dark" opts={{ renderer: 'canvas' }} />
}
export function Card({ title, right, children, className = '' }: { title?: ReactNode; right?: ReactNode; children: ReactNode; className?: string }) {
  return <div className={'rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg shadow-black/20 ' + className}>
    {(title || right) && <div className="mb-2 flex items-center justify-between gap-2"><h3 className="text-sm font-semibold text-zinc-300">{title}</h3><div className="flex items-center gap-2 text-xs">{right}</div></div>}
    {children}</div>
}
export function Kpi({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: 'good' | 'bad' }) {
  return <div className="rounded-2xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-900/40 p-4">
    <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
    <div className={'mt-1 text-2xl font-semibold ' + (tone === 'bad' ? 'text-rose-400' : tone === 'good' ? 'text-emerald-400' : 'text-zinc-100')}>{value}</div>
    {sub && <div className="mt-1 text-xs text-zinc-500">{sub}</div>}</div>
}
export function Slider({ label, value, set, min, max, step = 1, fmt = (v: number) => String(v) }: any) {
  return <label className="block text-xs text-zinc-400"><div className="flex justify-between"><span>{label}</span><span className="font-mono text-zinc-200">{fmt(value)}</span></div>
    <input type="range" className="w-full" min={min} max={max} step={step} value={value} onChange={e => set(Number(e.target.value))} /></label>
}
export function Seg({ value, set, options }: { value: any; set: (v: any) => void; options: [any, string][] }) {
  return <div className="inline-flex rounded-lg border border-zinc-700 p-0.5">{options.map(([v, l]) =>
    <button key={String(v)} onClick={() => set(v)} className={'rounded-md px-2 py-0.5 text-xs ' + (value === v ? 'bg-violet-600 text-white' : 'text-zinc-400 hover:text-zinc-200')}>{l}</button>)}</div>
}
export function TxTable({ rows, max = 200 }: { rows: any[]; max?: number }) {
  return <div className="max-h-96 overflow-auto"><table className="w-full text-xs"><thead className="sticky top-0 bg-zinc-900 text-zinc-500"><tr>
    <th className="p-1 text-left">Date</th><th className="text-left">Merchant</th><th className="text-left">Category</th><th className="text-left">Account</th><th className="text-right">Amount</th></tr></thead>
    <tbody>{rows.slice(0, max).map(r => <tr key={r.txn_id} className="border-t border-zinc-800 hover:bg-zinc-800/50">
      <td className="p-1 font-mono text-zinc-500">{r.date}</td><td>{r.merchant}</td><td className="text-zinc-400">{r.category}</td><td className="text-zinc-500">{r.account}</td>
      <td className={'text-right font-mono ' + (r.amount > 0 ? 'text-emerald-400' : '')}>{usd(r.amount, 2)}</td></tr>)}</tbody></table></div>
}
// Local-calendar date helpers. Never use toISOString()/new Date('YYYY-MM-DD') for calendar dates: both are UTC and shift a day/month.
const p2 = (n: number) => String(n).padStart(2, '0')
export const isoLocal = (d: Date) => `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`
export const ym = (offset = 0) => { const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() + offset); return isoLocal(d).slice(0, 7) }
export const monthEnd = (m: string) => isoLocal(new Date(Number(m.slice(0, 4)), Number(m.slice(5, 7)), 0))
export const daysAgo = (n: number) => { const d = new Date(); d.setDate(d.getDate() - n); return isoLocal(d) }
