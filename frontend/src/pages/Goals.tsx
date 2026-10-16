import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { Card, Chart, base, api, useApi, usd, pct } from '../lib'
export default function Goals() {
  const [g, , rg] = useApi<any[]>('/goals'); const [b, , rb] = useApi<any[]>('/budgets'); const [cats] = useApi<any[]>('/spending?dim=category&since=2024-01-01&limit=60')
  const [f, setF] = useState<any>({ name: 'Emergency fund (6 mo)', target: 30000, by: '2027-12', track: 'cash' }); const [bf, setBf] = useState<any>({ category: '', monthly_amount: 300 })
  const inp = 'rounded bg-zinc-800 px-2 py-1 text-xs'
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Goals & budgets</h1>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <Card title="Goals"><div className="mb-3 flex flex-wrap gap-2"><input className={inp} value={f.name} onChange={e => setF({ ...f, name: e.target.value })} />
        <input type="number" className={inp + ' w-24'} value={f.target} onChange={e => setF({ ...f, target: Number(e.target.value) })} /><input className={inp + ' w-20'} value={f.by} onChange={e => setF({ ...f, by: e.target.value })} />
        <select className={inp} value={f.track} onChange={e => setF({ ...f, track: e.target.value })}>{['cash', 'investment', 'net_worth', ''].map(t => <option key={t} value={t}>{t || 'manual'}</option>)}</select>
        <button className="rounded bg-violet-600 px-2 text-xs text-white" onClick={() => api('/goals', { ...f, track: f.track || null }).then(rg)}>Add</button></div>
        {g?.map(x => <div key={x.name} className="mb-3"><div className="flex justify-between text-sm"><span>{x.name} <span className="text-xs text-zinc-500">by {x.by} · tracks {x.track || 'manual'}</span></span>
          <span className="flex items-center gap-2 font-mono text-xs">{usd(x.current)} / {usd(x.target)}<button onClick={() => api('/goals/' + encodeURIComponent(x.name), undefined, 'DELETE').then(rg)}><Trash2 size={12} /></button></span></div>
          <div className="mt-1 h-2 rounded bg-zinc-800"><div className="h-2 rounded bg-gradient-to-r from-violet-500 to-cyan-400" style={{ width: pct(Math.max(0, x.progress || 0)) }} /></div>
          <div className="mt-0.5 text-[11px] text-zinc-500">needs {usd(x.needed_per_month)}/mo</div></div>)}
        {g?.length === 0 && <p className="text-xs text-zinc-500">No goals yet — add one, or ask the Wizard.</p>}</Card>
      <Card title="Budgets (month-to-date pace)"><div className="mb-3 flex gap-2"><select className={inp} value={bf.category} onChange={e => setBf({ ...bf, category: e.target.value })}><option value="">category…</option>{cats?.map(c => <option key={c.name}>{c.name}</option>)}</select>
        <input type="number" className={inp + ' w-24'} value={bf.monthly_amount} onChange={e => setBf({ ...bf, monthly_amount: Number(e.target.value) })} />
        <button className="rounded bg-violet-600 px-2 text-xs text-white" onClick={() => bf.category && api('/budgets', bf).then(rb)}>Set</button></div>
        {b && b.length > 0 ? <Chart h={Math.max(160, b.length * 40)} option={base({ grid: { left: 140, right: 20, top: 20, bottom: 20 }, tooltip: { trigger: 'axis', valueFormatter: usd, backgroundColor: '#18181b', textStyle: { color: '#e4e4e7' } },
          xAxis: { type: 'value', splitLine: { lineStyle: { color: '#27272a' } } }, yAxis: { type: 'category', data: b.map(x => x.category) },
          series: [{ name: 'Budget', type: 'bar', data: b.map(x => x.budget), itemStyle: { color: '#27272a' }, barGap: '-100%' }, { name: 'Spent', type: 'bar', barWidth: '40%', data: b.map(x => ({ value: x.spent, itemStyle: { color: (x.pace || 0) > 1 ? '#f43f5e' : '#34d399' } })) }] })} />
          : <p className="text-xs text-zinc-500">No budgets yet.</p>}</Card></div></div>
}
