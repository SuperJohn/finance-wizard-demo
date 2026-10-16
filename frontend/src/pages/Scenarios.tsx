import { useEffect, useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Card, Chart, base, zoom, api, usd, ym } from '../lib'
import { useRunwayDefaults } from './Runway'

type S = { name: string; lump: number; lumpM: string; income: number; incomeStart: string; extra: number; on: boolean }
const PRESETS: S[] = [  // illustrative examples; edit or delete them, changes are autosaved locally
  { name: 'Annual bonus $12k in March', lump: 12000, lumpM: ym(5), income: 0, incomeStart: ym(6), extra: 0, on: true },
  { name: 'Raise: +$600/mo net from next quarter', lump: 0, lumpM: ym(1), income: 600, incomeStart: ym(3), extra: 0, on: true },
  { name: 'Move to a bigger place (+$700/mo)', lump: 0, lumpM: ym(4), income: 0, incomeStart: ym(6), extra: 700, on: true },
  { name: 'Sabbatical: 3 months of no pay', lump: -20000, lumpM: ym(6), income: 0, incomeStart: ym(6), extra: 0, on: false },
]
export default function Scenarios() {
  const d = useRunwayDefaults()
  const [sc, setSc] = useState<S[]>(PRESETS); const [res, setRes] = useState<any[]>([]); const [cash, setCash] = useState<number | null>(null)
  useEffect(() => { api('/state/scenarios').then(v => { if (Array.isArray(v) && v.length) { setSc(v) } }).catch(() => {}) }, [])
  useEffect(() => { if (d && cash == null) setCash(Math.round(d.cash)) }, [d])
  useEffect(() => {
    if (!d || cash == null) return
    api('/state/scenarios', sc, 'PUT')
    const t = setTimeout(() => api('/scenarios', { base: { ...d, cash, months: 36 }, variants: sc.filter(s => s.on).map(s => ({ name: s.name,
      lump_sums: s.lump ? [{ amount: s.lump, month: s.lumpM }] : [], income: s.income ? [{ monthly_net: s.income, start: s.incomeStart }] : [], extra_monthly: s.extra ? [{ amount: s.extra, start: s.lumpM }] : [] })) }).then(setRes), 250)
    return () => clearTimeout(t)
  }, [sc, d, cash])
  const up = (i: number, k: keyof S, v: any) => setSc(sc.map((s, j) => j === i ? { ...s, [k]: v } : s))
  const inp = 'w-24 rounded bg-zinc-800 px-1 py-0.5 font-mono text-xs'
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Scenario simulator</h1>
    <Card title="Scenarios (stack on top of baseline burn; edit inline, autosaved)" right={<>Starting cash <input type="number" className={inp} value={cash ?? 0} onChange={e => setCash(Number(e.target.value))} />
      <button onClick={() => setSc([...sc, { name: 'New scenario', lump: 0, lumpM: ym(1), income: 0, incomeStart: ym(3), extra: 0, on: true }])} className="flex items-center gap-1 rounded bg-violet-600 px-2 py-0.5 text-white"><Plus size={12} />Add</button></>}>
      <table className="w-full text-xs"><thead className="text-zinc-500"><tr><th></th><th className="text-left">Name</th><th>Lump sum</th><th>Month</th><th>Net income/mo</th><th>From</th><th>Extra cost/mo</th><th className="text-right">Runway</th><th className="text-right">Cash @36m</th><th></th></tr></thead>
        <tbody>{sc.map((s, i) => { const r = res.find(x => x.name === s.name); return <tr key={i} className="border-t border-zinc-800">
          <td><input type="checkbox" checked={s.on} onChange={e => up(i, 'on', e.target.checked)} /></td>
          <td><input value={s.name} onChange={e => up(i, 'name', e.target.value)} className="w-72 rounded bg-transparent px-1" /></td>
          <td><input type="number" className={inp} value={s.lump} onChange={e => up(i, 'lump', Number(e.target.value))} /></td><td><input className={inp} value={s.lumpM} onChange={e => up(i, 'lumpM', e.target.value)} /></td>
          <td><input type="number" className={inp} value={s.income} onChange={e => up(i, 'income', Number(e.target.value))} /></td><td><input className={inp} value={s.incomeStart} onChange={e => up(i, 'incomeStart', e.target.value)} /></td>
          <td><input type="number" className={inp} value={s.extra} onChange={e => up(i, 'extra', Number(e.target.value))} /></td>
          <td className="text-right">{r ? (r.runway_months == null ? '36+ mo' : r.runway_months + ' mo') : ''}</td><td className={'text-right font-mono ' + (r?.end_cash < 0 ? 'text-rose-400' : 'text-emerald-400')}>{r ? usd(r.end_cash) : ''}</td>
          <td><button onClick={() => setSc(sc.filter((_, j) => j !== i))} className="text-zinc-500"><Trash2 size={12} /></button></td></tr> })}</tbody></table></Card>
    <Card title="Cash trajectories (click legend to compare subsets)"><Chart h={440} option={base({ xAxis: { type: 'category', data: res[0]?.rows.map((r: any) => r.month) || [] }, dataZoom: zoom,
      series: res.map((r, i) => ({ name: r.name, type: 'line', symbol: 'none', lineStyle: { width: i === 0 ? 3 : 2, type: i === 0 ? 'dashed' : 'solid' }, data: r.rows.map((x: any) => x.cash),
        markLine: i === 0 ? { silent: true, symbol: 'none', lineStyle: { color: '#f43f5e' }, data: [{ yAxis: 0 }] } : undefined })) })} /></Card></div>
}
