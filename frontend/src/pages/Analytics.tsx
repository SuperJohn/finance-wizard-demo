import { useState } from 'react'
import { Card, Chart, Kpi, Seg, base, zoom, useApi, usd, pct } from '../lib'
export default function Analytics() {
  const [real] = useApi<any[]>('/analytics/real?months=60'); const [sav] = useApi<any[]>('/analytics/savings?months=60')
  const [days, setDays] = useState(365); const [dist] = useApi<any>(`/analytics/distribution?days=${days}`, [days]); const [co] = useApi<any>('/analytics/cohorts')
  const st = dist?.stats || {}
  return <div className="space-y-4"><div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Economics lab</h1><Seg value={days} set={setDays} options={[[90, '90d'], [365, '1y'], [730, '2y'], [3650, 'All']]} /></div>
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-6"><Kpi label="Median ticket" value={usd(st.median, 2)} /><Kpi label="Mean ticket" value={usd(st.mean, 2)} /><Kpi label="p90 / p99" value={`${usd(st.p90)} / ${usd(st.p99)}`} />
      <Kpi label="Top-10% share of spend" value={pct(st.top10pct_share)} sub="lumpiness" /><Kpi label="Gini of tickets" value={st.gini ?? '—'} /><Kpi label="# expenses" value={st.n ?? '—'} /></div>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <Card title="Spend: nominal vs real (CPI-U, today's dollars)"><Chart option={base({ xAxis: { type: 'category', data: real?.map(r => r.month) }, dataZoom: zoom,
        series: [{ name: 'Nominal', type: 'line', symbol: 'none', data: real?.map(r => r.spend_nominal) }, { name: 'Real', type: 'line', symbol: 'none', data: real?.map(r => r.spend_real) }] })} /></Card>
      <Card title="Savings rate: monthly vs trailing-12m"><Chart option={base({ xAxis: { type: 'category', data: sav?.map(r => r.month) }, dataZoom: zoom, yAxis: { type: 'value', min: -2, max: 1, axisLabel: { formatter: (v: number) => v * 100 + '%' }, splitLine: { lineStyle: { color: '#27272a' } } },
        tooltip: { trigger: 'axis', valueFormatter: pct, backgroundColor: '#18181b', textStyle: { color: '#e4e4e7' } },
        series: [{ name: 'Monthly', type: 'bar', data: sav?.map(r => r.savings_rate == null ? null : Math.max(-2, r.savings_rate)), itemStyle: { color: '#3f3f46' } }, { name: 'TTM', type: 'line', symbol: 'none', lineStyle: { width: 3 }, color: '#34d399', data: sav?.map(r => r.ttm_savings_rate) }] })} /></Card>
      <Card title="Ticket-size distribution (count vs $)"><Chart option={base({ xAxis: { type: 'category', data: dist?.histogram.map((h: any) => h.bucket) }, yAxis: [{ type: 'value', splitLine: { lineStyle: { color: '#27272a' } } }, { type: 'value', splitLine: { show: false } }],
        tooltip: { trigger: 'axis', backgroundColor: '#18181b', textStyle: { color: '#e4e4e7' } },
        series: [{ name: 'Count', type: 'bar', data: dist?.histogram.map((h: any) => h.count), color: '#8b5cf6' }, { name: '$ spent', type: 'line', yAxisIndex: 1, data: dist?.histogram.map((h: any) => h.spend), color: '#f59e0b' }] })} /></Card>
      <Card title="Day-of-week spend"><Chart option={base({ xAxis: { type: 'category', data: dist?.day_of_week.map((d: any) => d.day) }, series: [{ type: 'bar', name: 'Spend', data: dist?.day_of_week.map((d: any) => d.spend), itemStyle: { color: '#22d3ee', borderRadius: 4 } }] })} /></Card>
      <Card title="Merchant cohorts — spend by year, by year merchant first appeared (lock-in vs churn)" className="xl:col-span-2"><Chart h={360} option={base({ xAxis: { type: 'category', data: co?.rows.map((r: any) => r.year) },
        series: (co?.cohorts || []).map((c: string) => ({ name: 'cohort ' + c, type: 'bar', stack: 'c', emphasis: { focus: 'series' }, data: co.rows.map((r: any) => r[c]) })) })} /></Card></div></div>
}
