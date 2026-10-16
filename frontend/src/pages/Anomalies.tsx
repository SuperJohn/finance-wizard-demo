import { useMemo, useState } from 'react'
import { Card, Chart, Slider, base, zoom, useApi, usd, daysAgo } from '../lib'
export default function Anomalies() {
  const [z, setZ] = useState(3.5); const [days, setDays] = useState(180)
  const [an] = useApi<any[]>(`/anomalies?days=${days}&z=${z}`, [z, days])
  const since = daysAgo(days)
  const [tx] = useApi<any[]>(`/transactions?since=${since}&limit=10000`, [days])
  const flagged = useMemo(() => new Set((an || []).map(a => a.txn_id)), [an])
  const exp = (tx || []).filter(t => t.kind === 'expense')
  const pts = (f: boolean) => exp.filter(t => flagged.has(t.txn_id) === f).map(t => [t.date, -t.amount, t.merchant, t.category])
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Anomaly model</h1>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[300px_1fr]">
      <Card title="Model controls"><div className="space-y-4"><Slider label="Robust z threshold (log-amount, per category, MAD)" value={z} set={setZ} min={1.5} max={6} step={0.1} />
        <Slider label="Lookback (days)" value={days} set={setDays} min={14} max={730} step={7} />
        <p className="text-xs text-zinc-500">Each charge is scored against its own category's distribution of log amounts using median/MAD (robust to outliers). Also flags first-ever merchants &gt; $250. Lower z = more sensitive.</p>
        <div className="text-2xl font-semibold text-rose-400">{an?.length ?? '…'} <span className="text-sm text-zinc-500">flagged</span></div></div></Card>
      <Card title="All expenses (log scale) — red = flagged; zoom & hover"><Chart h={420} option={base({ xAxis: { type: 'time' }, yAxis: { type: 'log', splitLine: { lineStyle: { color: '#27272a' } } }, dataZoom: zoom,
        tooltip: { trigger: 'item', backgroundColor: '#18181b', textStyle: { color: '#e4e4e7' }, formatter: (p: any) => `${p.value[0]}<br/>${p.value[2]} · ${p.value[3]}<br/><b>${usd(p.value[1], 2)}</b>` },
        series: [{ name: 'Normal', type: 'scatter', symbolSize: 5, itemStyle: { color: 'rgba(139,92,246,.45)' }, data: pts(false) }, { name: 'Flagged', type: 'scatter', symbolSize: 12, itemStyle: { color: '#f43f5e' }, data: pts(true) }] })} /></Card></div>
    <Card title="Flagged"><table className="w-full text-xs"><thead className="text-zinc-500"><tr><th className="text-left">Date</th><th className="text-left">Merchant</th><th className="text-left">Category</th><th className="text-right">Amount</th><th className="text-right">Typical</th><th className="text-right">z / reason</th></tr></thead>
      <tbody>{an?.map(a => <tr key={a.txn_id + (a.reason || '')} className="border-t border-zinc-800"><td className="py-1">{a.date}</td><td>{a.merchant}</td><td className="text-zinc-400">{a.category}</td><td className="text-right font-mono text-rose-300">{usd(a.amount, 2)}</td><td className="text-right font-mono">{usd(a.typical, 2)}</td><td className="text-right">{a.reason || a.robust_z}</td></tr>)}</tbody></table></Card></div>
}
