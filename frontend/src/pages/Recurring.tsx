import { useState } from 'react'
import { Card, Chart, Kpi, base, useApi, usd } from '../lib'
export default function Recurring() {
  const [d] = useApi<any[]>('/recurring'); const [showAll, setShowAll] = useState(false); const [cut, setCut] = useState<Set<string>>(new Set())
  const rows = (d || []).filter(r => showAll || r.active)
  const active = (d || []).filter(r => r.active); const total = active.reduce((s, r) => s + r.annualized, 0)
  const saved = active.filter(r => cut.has(r.merchant)).reduce((s, r) => s + r.annualized, 0)
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Recurring & subscriptions</h1>
    <div className="grid grid-cols-3 gap-3"><Kpi label="Active recurring" value={usd(total) + '/yr'} sub={`${active.length} streams · ${usd(total / 12)}/mo`} />
      <Kpi label="What-if: cut selected" value={usd(saved) + '/yr'} tone="good" sub="tick rows below" /><Kpi label="Detector" value="interval + amount CV" sub="cadence from median gap; confidence = regularity × stability" /></div>
    <Card title="Annualized cost by stream"><Chart h={Math.max(200, active.length * 26)} option={base({ grid: { left: 160, right: 30, top: 10, bottom: 20 }, tooltip: { trigger: 'item', valueFormatter: (v: number) => usd(v) },
      xAxis: { type: 'value', splitLine: { lineStyle: { color: '#27272a' } } }, yAxis: { type: 'category', inverse: true, data: active.map(r => r.merchant) },
      series: [{ type: 'bar', data: active.map(r => ({ value: r.annualized, itemStyle: { color: cut.has(r.merchant) ? '#34d399' : '#8b5cf6', borderRadius: 3 } })) }] })} /></Card>
    <Card title="Streams" right={<label className="text-zinc-400"><input type="checkbox" checked={showAll} onChange={e => setShowAll(e.target.checked)} /> include inactive</label>}>
      <table className="w-full text-xs"><thead className="text-zinc-500"><tr><th></th><th className="text-left">Merchant</th><th className="text-left">Category</th><th>Cadence</th><th className="text-right">Typical</th><th className="text-right">Annual</th><th>Last</th><th>Next</th><th className="text-right">Δ price</th><th className="text-right">Conf.</th></tr></thead>
        <tbody>{rows.map(r => <tr key={r.merchant} className={'border-t border-zinc-800 ' + (r.active ? '' : 'opacity-40')}>
          <td><input type="checkbox" checked={cut.has(r.merchant)} onChange={() => { const s = new Set(cut); s.has(r.merchant) ? s.delete(r.merchant) : s.add(r.merchant); setCut(s) }} /></td>
          <td className="py-1">{r.merchant}</td><td className="text-zinc-400">{r.category}</td><td className="text-center">{r.cadence}</td><td className="text-right font-mono">{usd(r.typical, 2)}</td>
          <td className="text-right font-mono">{usd(r.annualized)}</td><td className="text-center text-zinc-500">{r.last}</td><td className="text-center text-zinc-500">{r.next_expected}</td>
          <td className={'text-right font-mono ' + (r.price_change > 0 ? 'text-rose-400' : '')}>{r.price_change ? usd(r.price_change, 2) : ''}</td><td className="text-right">{(r.confidence * 100).toFixed(0)}%</td></tr>)}</tbody></table></Card></div>
}
