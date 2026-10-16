import { useEffect, useState } from 'react'
import { Card, Chart, Kpi, Slider, base, zoom, api, usd, pct, ym } from '../lib'

const months = Array.from({ length: 30 }, (_, i) => ym(i))
function MonthPick({ label, value, set }: any) {
  return <label className="block text-xs text-zinc-400">{label}<select value={value} onChange={e => set(e.target.value)} className="ml-2 rounded bg-zinc-800 px-1">{months.map(m => <option key={m}>{m}</option>)}</select></label>
}
export function useRunwayDefaults() {
  const [d, setD] = useState<any>(null); useEffect(() => { api('/runway/defaults').then(setD) }, []); return d
}
export default function Runway() {
  const d = useRunwayDefaults()
  const [p, setP] = useState<any>(null); const [mc, setMc] = useState<any>(null)
  useEffect(() => { if (d) setP({ cash: Math.round(d.cash), burn: Math.round(d.monthly_burn), extra: 0, extraStart: ym(3), lump: 0, lumpM: ym(2), job: 0, jobStart: ym(4), vol: 0.25, mvol: 0, infl: 0.03, ret: 0.04, months: 36 }) }, [d])
  useEffect(() => {
    if (!p) return
    const t = setTimeout(() => api('/runway/mc', {
      cash: p.cash, monthly_burn: p.burn, months: p.months, inflation: p.infl, return_rate: p.ret, spend_vol: p.vol, market_vol: p.mvol, sims: 2000,
      extra_monthly: p.extra ? [{ label: 'New recurring cost', amount: p.extra, start: p.extraStart }] : [],
      lump_sums: p.lump ? [{ label: 'One-off inflow', amount: p.lump, month: p.lumpM }] : [], income: p.job ? [{ label: 'New income', monthly_net: p.job, start: p.jobStart }] : [],
    }).then(setMc), 200); return () => clearTimeout(t)
  }, [p])
  if (!p) return <div>Loading…</div>
  const s = (k: string) => (v: any) => setP({ ...p, [k]: v })
  const b = mc?.bands || []
  const firstBroke = b.find((r: any) => r.p_broke >= 0.5)
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Runway lab <span className="text-xs text-zinc-500">Monte-Carlo, {2000} paths</span></h1>
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Kpi label="Median runway" value={firstBroke ? `${b.indexOf(firstBroke)} mo` : `${p.months}+ mo`} sub={firstBroke ? `P(broke) ≥ 50% by ${firstBroke.month}` : 'never majority-broke in horizon'} tone={firstBroke && b.indexOf(firstBroke) < 6 ? 'bad' : 'good'} />
      <Kpi label="P(cash < 0) at horizon" value={pct(mc?.p_broke_end)} />
      <Kpi label="Cash in 12 mo (p10 / p50 / p90)" value={usd(b[11]?.p50)} sub={`${usd(b[11]?.p10)} … ${usd(b[11]?.p90)}`} />
      <Kpi label="Spend volatility (σ log)" value={mc?.spend_vol ?? '—'} sub="from your history unless overridden" /></div>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[320px_1fr]">
      <Card title="Assumptions"><div className="space-y-3">
        <Slider label="Starting liquid cash" value={p.cash} set={s('cash')} min={0} max={250000} step={500} fmt={usd} />
        <Slider label="Monthly burn" value={p.burn} set={s('burn')} min={500} max={15000} step={50} fmt={usd} />
        <Slider label="New recurring cost / mo" value={p.extra} set={s('extra')} min={0} max={6000} step={25} fmt={usd} /><MonthPick label="…starting" value={p.extraStart} set={s('extraStart')} />
        <Slider label="One-off inflow (bonus, sale, windfall)" value={p.lump} set={s('lump')} min={0} max={300000} step={1000} fmt={usd} /><MonthPick label="…received" value={p.lumpM} set={s('lumpM')} />
        <Slider label="New net income / mo" value={p.job} set={s('job')} min={0} max={25000} step={250} fmt={usd} /><MonthPick label="…first payment" value={p.jobStart} set={s('jobStart')} />
        <Slider label="Spend volatility σ" value={p.vol} set={s('vol')} min={0.05} max={0.6} step={0.01} />
        <Slider label="Market volatility on cash (ann.)" value={p.mvol} set={s('mvol')} min={0} max={0.3} step={0.01} fmt={pct} />
        <Slider label="Inflation" value={p.infl} set={s('infl')} min={0} max={0.1} step={0.005} fmt={pct} />
        <Slider label="Yield on cash" value={p.ret} set={s('ret')} min={0} max={0.08} step={0.0025} fmt={pct} />
        <Slider label="Horizon (months)" value={p.months} set={s('months')} min={6} max={60} /></div></Card>
      <div className="space-y-4">
        <Card title="Cash fan chart — p10–p90 band, median, deterministic path, and P(broke)"><Chart h={460} option={base({
          xAxis: { type: 'category', data: b.map((r: any) => r.month) }, dataZoom: zoom,
          yAxis: [{ type: 'value', splitLine: { lineStyle: { color: '#27272a' } }, axisLabel: { formatter: (v: number) => (v / 1000).toFixed(0) + 'k' } }, { type: 'value', min: 0, max: 1, axisLabel: { formatter: (v: number) => v * 100 + '%' }, splitLine: { show: false } }],
          tooltip: { trigger: 'axis', backgroundColor: '#18181b', borderColor: '#3f3f46', textStyle: { color: '#e4e4e7' } },
          series: [{ name: 'p10', type: 'line', stack: 'b', symbol: 'none', lineStyle: { opacity: 0 }, data: b.map((r: any) => r.p10), tooltip: { valueFormatter: usd } },
            { name: 'p10–p90', type: 'line', stack: 'b', symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(139,92,246,.25)' }, data: b.map((r: any) => r.p90 - r.p10), tooltip: { show: false } },
            { name: 'Median', type: 'line', symbol: 'none', color: '#a78bfa', lineStyle: { width: 3 }, data: b.map((r: any) => r.p50), tooltip: { valueFormatter: usd } },
            { name: 'Deterministic', type: 'line', symbol: 'none', color: '#22d3ee', lineStyle: { type: 'dashed' }, data: b.map((r: any) => r.deterministic), tooltip: { valueFormatter: usd },
              markLine: { silent: true, symbol: 'none', lineStyle: { color: '#f43f5e' }, data: [{ yAxis: 0 }] } },
            { name: 'P(broke)', type: 'line', yAxisIndex: 1, symbol: 'none', color: '#f43f5e', areaStyle: { opacity: .08 }, data: b.map((r: any) => r.p_broke), tooltip: { valueFormatter: pct } }] })} /></Card>
        <Card title="Monthly ledger (deterministic)"><div className="max-h-64 overflow-auto"><table className="w-full text-xs"><thead className="text-zinc-500"><tr><th className="text-left">Month</th><th className="text-right">Spend</th><th className="text-right">Income</th><th className="text-right">Lump</th><th className="text-right">Cash</th></tr></thead>
          <tbody>{mc?.deterministic.rows.map((r: any) => <tr key={r.month} className="border-t border-zinc-800"><td>{r.month}</td><td className="text-right font-mono">{usd(r.spend)}</td><td className="text-right font-mono">{usd(r.income)}</td><td className="text-right font-mono">{r.lump ? usd(r.lump) : ''}</td><td className={'text-right font-mono ' + (r.cash < 0 ? 'text-rose-400' : '')}>{usd(r.cash)}</td></tr>)}</tbody></table></div></Card></div></div></div>
}
