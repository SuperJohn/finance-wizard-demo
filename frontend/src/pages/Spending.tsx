import { useMemo, useState } from 'react'
import { Card, Chart, Seg, TxTable, base, zoom, useApi, usd, ym } from '../lib'
const PERIODS: [string, string][] = [[ym(0) + '-01', 'MTD'], [ym(-3) + '-01', '3M'], [ym(-6) + '-01', '6M'], [ym(-12) + '-01', '12M'], ['2015-01-01', 'All']]
export default function Spending() {
  const [since, setSince] = useState(PERIODS[2][0]); const [cat, setCat] = useState<string | null>(null); const [mer, setMer] = useState<string | null>(null)
  const [cats] = useApi<any[]>(`/spending?dim=category&since=${since}&limit=40`, [since])
  const [txAll] = useApi<any[]>(`/transactions?since=${since}&limit=5000`, [since])
  const [daily] = useApi<any[]>('/daily?days=730')
  const exp = useMemo(() => (txAll || []).filter(t => (t.kind === 'expense' || t.kind === 'refund') && (!cat || t.category === cat)), [txAll, cat])
  const merchants = useMemo(() => { const m: Record<string, number> = {}; exp.forEach(t => m[t.merchant] = (m[t.merchant] || 0) - t.amount); return Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 20) }, [exp])
  const rows = exp.filter(t => !mer || t.merchant === mer)
  const dd = useMemo(() => { const m: Record<string, number> = {}; (daily || []).filter(d => !cat || d.category === cat).forEach(d => m[d.date] = (m[d.date] || 0) + d.spend); return Object.entries(m).sort() }, [daily, cat])
  return <div className="space-y-4">
    <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Spending {cat && <span className="text-violet-300">› {cat}</span>} {mer && <span className="text-cyan-300">› {mer}</span>}</h1>
      <div className="flex gap-2">{(cat || mer) && <button className="text-xs text-zinc-400" onClick={() => { setCat(null); setMer(null) }}>reset filters</button>}<Seg value={since} set={setSince} options={PERIODS} /></div></div>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <Card title="Categories — click to cross-filter"><Chart h={360} onEvents={{ click: (e: any) => { setCat(cat === e.name ? null : e.name); setMer(null) } }} option={{
        tooltip: { formatter: (p: any) => `${p.name}<br/>${usd(p.value)} (${(p.data.share * 100).toFixed(1)}%) · ${p.data.count} txns` },
        series: [{ type: 'treemap', roam: false, nodeClick: false, breadcrumb: { show: false }, label: { formatter: '{b}\n{c}' }, itemStyle: { borderColor: '#09090b', borderWidth: 2, gapWidth: 2 },
          data: (cats || []).map(c => ({ name: c.name, value: Math.round(c.spend), share: c.share, count: c.count, itemStyle: cat && c.name !== cat ? { opacity: .3 } : {} })) }] }} /></Card>
      <Card title={`Top merchants${cat ? ' in ' + cat : ''} — click to filter`}><Chart h={360} onEvents={{ click: (e: any) => setMer(mer === e.name ? null : e.name) }} option={base({
        grid: { left: 140, right: 20, top: 10, bottom: 20 }, tooltip: { trigger: 'item', valueFormatter: (v: number) => usd(v) }, xAxis: { type: 'value', splitLine: { lineStyle: { color: '#27272a' } } },
        yAxis: { type: 'category', inverse: true, data: merchants.map(m => m[0]), axisLabel: { width: 130, overflow: 'truncate' } },
        series: [{ type: 'bar', data: merchants.map(m => ({ value: Math.round(m[1]), itemStyle: { color: mer && m[0] !== mer ? '#3f3f46' : '#22d3ee', borderRadius: 3 } })) }] })} /></Card></div>
    <Card title={`Daily spend${cat ? ' — ' + cat : ''} (zoom with the slider; hover for detail)`}><Chart h={260} option={base({ xAxis: { type: 'category', data: dd.map(d => d[0]) }, dataZoom: zoom,
      series: [{ type: 'bar', name: 'Spend', data: dd.map(d => d[1]), itemStyle: { color: '#8b5cf6' } }] })} /></Card>
    <Card title={`Transactions (${rows.length})`}><TxTable rows={rows} max={300} /></Card></div>
}
