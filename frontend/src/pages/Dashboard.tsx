import { useEffect, useState } from 'react'
import { Settings2, ArrowUp, ArrowDown } from 'lucide-react'
import { Card, api } from '../lib'
import { Kpis, NetWorthChart, CashflowChart, CategoryTrend, ForecastChart, RecurringList, AnomalyList } from './widgets'

const W: Record<string, [string, any, number]> = {
  kpis: ['Key numbers', Kpis, 2], networth: ['Net worth composition', NetWorthChart, 2], cashflow: ['Cash flow & savings rate', CashflowChart, 1],
  forecast: ['Spend forecast (80% band)', ForecastChart, 1], categories: ['Category mix over time', CategoryTrend, 2],
  recurring: ['Active subscriptions', RecurringList, 1], anomalies: ['Anomalies (90d)', AnomalyList, 1],
}
const DEFAULT = ['kpis', 'networth', 'cashflow', 'forecast', 'categories', 'recurring', 'anomalies']

export default function Dashboard() {
  const [layout, setLayout] = useState<string[]>(DEFAULT); const [edit, setEdit] = useState(false)
  useEffect(() => { api('/state/dashboard').then(v => Array.isArray(v) && setLayout(v)).catch(() => {}) }, [])
  const save = (l: string[]) => { setLayout(l); api('/state/dashboard', l, 'PUT') }
  const move = (i: number, d: number) => { const l = [...layout]; const j = i + d; if (j < 0 || j >= l.length) return;[l[i], l[j]] = [l[j], l[i]]; save(l) }
  return <div className="space-y-4">
    <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Dashboard</h1>
      <button onClick={() => setEdit(!edit)} className="flex items-center gap-1 rounded-lg border border-zinc-700 px-2 py-1 text-xs"><Settings2 size={13} />{edit ? 'Done' : 'Customize'}</button></div>
    {edit && <Card title="Widgets (toggle, reorder; saved locally)"><div className="flex flex-wrap gap-2">{Object.entries(W).map(([k, [t]]) =>
      <label key={k} className="flex items-center gap-1 rounded border border-zinc-700 px-2 py-1 text-xs"><input type="checkbox" checked={layout.includes(k)} onChange={e => save(e.target.checked ? [...layout, k] : layout.filter(x => x !== k))} />{t}</label>)}</div></Card>}
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">{layout.filter(k => W[k]).map((k, i) => { const [t, C, span] = W[k]
      return <div key={k} className={span === 2 ? 'xl:col-span-2' : ''}>{k === 'kpis' && !edit ? <C /> :
        <Card title={t} right={edit && <><button onClick={() => move(i, -1)}><ArrowUp size={13} /></button><button onClick={() => move(i, 1)}><ArrowDown size={13} /></button></>}><C /></Card>}</div> })}</div>
  </div>
}
