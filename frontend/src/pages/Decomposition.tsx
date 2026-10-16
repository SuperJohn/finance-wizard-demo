import { useState } from 'react'
import { Card, Chart, base, useApi, usd, ym } from '../lib'
const months = Array.from({ length: 36 }, (_, i) => ym(-i))
export default function Decomposition() {
  const [a, setA] = useState(ym(-2)); const [b, setB] = useState(ym(-1))
  const [d] = useApi<any>(`/decomposition?a=${a}&b=${b}`, [a, b])
  const rows = (d?.rows || []).filter((r: any) => Math.abs(r.delta) > 1).slice(0, 15)
  let run = d?.total_from || 0
  const helper: number[] = [], up: any[] = [], down: any[] = []
  const cats = [d?.from, ...rows.map((r: any) => r.category), d?.to]
  helper.push(0); up.push(d?.total_from); down.push('-')
  rows.forEach((r: any) => { if (r.delta >= 0) { helper.push(run); up.push(r.delta); down.push('-') } else { helper.push(run + r.delta); up.push('-'); down.push(-r.delta) } run += r.delta })
  helper.push(0); up.push(d?.total_to); down.push('-')
  const sel = 'rounded bg-zinc-800 px-1 text-xs'
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Spending decomposition</h1>
    <Card title="Why did spending change?" right={<><select className={sel} value={a} onChange={e => setA(e.target.value)}>{months.map(m => <option key={m}>{m}</option>)}</select>→<select className={sel} value={b} onChange={e => setB(e.target.value)}>{months.map(m => <option key={m}>{m}</option>)}</select></>}>
      <div className="mb-2 text-sm text-zinc-400">{usd(d?.total_from)} → {usd(d?.total_to)} ({usd((d?.total_to || 0) - (d?.total_from || 0))})</div>
      <Chart h={380} option={base({ tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: '#18181b', textStyle: { color: '#e4e4e7' }, formatter: (ps: any) => ps.filter((p: any) => p.seriesName !== 'h' && p.value !== '-').map((p: any) => `${p.name}: ${p.seriesName === 'Decrease' ? '-' : ''}${usd(p.value)}`).join('<br/>') },
        xAxis: { type: 'category', data: cats, axisLabel: { rotate: 30, interval: 0 } }, grid: { left: 56, right: 20, top: 30, bottom: 90 },
        series: [{ name: 'h', type: 'bar', stack: 'w', itemStyle: { color: 'transparent' }, data: helper },
          { name: 'Increase', type: 'bar', stack: 'w', data: up, itemStyle: { color: '#f43f5e' } }, { name: 'Decrease', type: 'bar', stack: 'w', data: down, itemStyle: { color: '#34d399' } }] })} /></Card>
    <Card title="Volume vs price effect per category (Shapley/midpoint split: Δ = Δn·p̄ + Δp·n̄)"><Chart h={380} option={base({ tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: usd, backgroundColor: '#18181b', textStyle: { color: '#e4e4e7' } },
      grid: { left: 150, right: 20, top: 30, bottom: 20 }, xAxis: { type: 'value', splitLine: { lineStyle: { color: '#27272a' } } }, yAxis: { type: 'category', inverse: true, data: rows.map((r: any) => r.category) },
      series: [{ name: 'Volume (# txns)', type: 'bar', stack: 'e', data: rows.map((r: any) => r.volume_effect), color: '#22d3ee' }, { name: 'Price (avg ticket)', type: 'bar', stack: 'e', data: rows.map((r: any) => r.price_effect), color: '#f59e0b' }] })} /></Card></div>
}
