import { Chart, base, zoom, usd, pct, Kpi, useApi } from '../lib'

export function Kpis() {
  const [s] = useApi<any>('/summary')
  if (!s) return <div className="h-24 animate-pulse rounded-2xl bg-zinc-900" />
  return <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
    <Kpi label="Net worth" value={usd(s.net_worth?.net_worth)} sub={<>Δ month {usd(s.net_worth_change_30d)}</>} />
    <Kpi label="Liquid cash" value={usd(s.liquid_cash)} tone={s.liquid_cash < 5000 ? 'bad' : undefined} />
    <Kpi label="Avg spend (3 mo)" value={usd(s.avg_spend_3m)} sub={<>income {usd(s.avg_income_3m)}</>} />
    <Kpi label="Runway (baseline)" value={s.runway_months == null ? '36+ mo' : `${s.runway_months} mo`} sub={s.runs_out ? `cash < 0 in ${s.runs_out}` : 'no shortfall in 36 mo'} tone={s.runway_months != null && s.runway_months < 6 ? 'bad' : 'good'} />
    <Kpi label="Active recurring" value={usd(s.recurring_annual) + '/yr'} sub={`${s.anomalies} anomalies (30d)`} />
  </div>
}
export function NetWorthChart({ h = 320 }) {
  const [d] = useApi<any[]>('/networth?freq=W')
  if (!d) return null
  const s = (k: string, n: string) => ({ name: n, type: 'line', stack: 'nw', areaStyle: { opacity: .35 }, symbol: 'none', smooth: true, data: d.map(r => r[k]) })
  return <Chart h={h} option={base({ xAxis: { type: 'category', data: d.map(r => r.date) }, dataZoom: zoom,
    series: [s('property', 'Property'), s('investment', 'Investments'), s('cash', 'Cash'), s('liability', 'Liabilities'),
      { name: 'Net worth', type: 'line', symbol: 'none', lineStyle: { width: 3, color: '#fafafa' }, data: d.map(r => r.net_worth) }] })} />
}
export function CashflowChart({ h = 320, real = false, onMonth }: { h?: number; real?: boolean; onMonth?: (m: string) => void }) {
  const [d] = useApi<any[]>(`/cashflow?months=60&real=${real}`, [real])
  if (!d) return null
  return <Chart h={h} onEvents={onMonth ? { click: (e: any) => onMonth(e.name) } : undefined} option={base({
    xAxis: { type: 'category', data: d.map(r => r.month) }, dataZoom: zoom,
    yAxis: [{ type: 'value', splitLine: { lineStyle: { color: '#27272a' } } }, { type: 'value', min: -1, max: 1, axisLabel: { formatter: (v: number) => (v * 100) + '%' }, splitLine: { show: false } }],
    tooltip: { trigger: 'axis', backgroundColor: '#18181b', borderColor: '#3f3f46', textStyle: { color: '#e4e4e7' } },
    series: [{ name: 'Income', type: 'bar', data: d.map(r => r.income), itemStyle: { color: '#34d399', borderRadius: [3, 3, 0, 0] } },
      { name: 'Spend', type: 'bar', data: d.map(r => r.spend), itemStyle: { color: '#f43f5e', borderRadius: [3, 3, 0, 0] } },
      { name: 'Net', type: 'line', data: d.map(r => r.net), symbol: 'circle', color: '#fafafa' },
      { name: 'Savings rate', type: 'line', yAxisIndex: 1, data: d.map(r => r.savings_rate == null ? null : Math.max(-1, Math.min(1, r.savings_rate))), lineStyle: { type: 'dashed' }, color: '#8b5cf6', tooltip: { valueFormatter: (v: number) => pct(v) } }] })} />
}
export function CategoryTrend({ h = 320 }) {
  const [d] = useApi<any>('/category_trend?top=8&months=24')
  if (!d) return null
  return <Chart h={h} option={base({ xAxis: { type: 'category', data: d.rows.map((r: any) => r.month) }, dataZoom: zoom,
    series: d.series.map((s: string) => ({ name: s, type: 'bar', stack: 'c', emphasis: { focus: 'series' }, data: d.rows.map((r: any) => r[s]) })) })} />
}
export function ForecastChart({ h = 320 }) {
  const [d] = useApi<any>('/forecast?months=6')
  if (!d) return null
  const months = [...d.history.map((r: any) => r.month), ...d.forecast.map((r: any) => r.month)]
  const pad = d.history.map(() => null)
  return <Chart h={h} option={base({ xAxis: { type: 'category', data: months }, dataZoom: zoom,
    series: [{ name: 'Actual', type: 'line', data: d.history.map((r: any) => r.spend), color: '#22d3ee' },
      { name: 'lo', type: 'line', stack: 'band', symbol: 'none', lineStyle: { opacity: 0 }, data: [...pad, ...d.forecast.map((r: any) => r.lo)], tooltip: { show: false } },
      { name: '80% band', type: 'line', stack: 'band', symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(139,92,246,.25)' }, data: [...pad, ...d.forecast.map((r: any) => r.hi - r.lo)] },
      { name: 'Forecast', type: 'line', lineStyle: { type: 'dashed' }, color: '#8b5cf6', data: [...pad.slice(1), d.history.at(-1)?.spend, ...d.forecast.map((r: any) => r.spend)] }] })} />
}
export function RecurringList({ max = 8 }) {
  const [d] = useApi<any[]>('/recurring')
  return <div className="space-y-1 text-sm">{d?.filter(r => r.active).slice(0, max).map(r => <div key={r.merchant} className="flex justify-between border-b border-zinc-800/60 py-1">
    <span>{r.merchant} <span className="text-xs text-zinc-500">{r.cadence}</span></span><span className="font-mono text-zinc-300">{usd(r.annualized)}/yr</span></div>)}</div>
}
export function AnomalyList({ max = 8 }) {
  const [d] = useApi<any[]>('/anomalies?days=90')
  return <div className="space-y-1 text-sm">{d?.length === 0 && <div className="text-xs text-zinc-500">Nothing unusual in 90 days.</div>}{d?.slice(0, max).map(r => <div key={r.txn_id} className="flex justify-between border-b border-zinc-800/60 py-1">
    <span>{r.merchant} <span className="text-xs text-zinc-500">{r.date} · {r.reason || `z=${r.robust_z}`}</span></span><span className="font-mono text-rose-300">{usd(r.amount)}</span></div>)}</div>
}
