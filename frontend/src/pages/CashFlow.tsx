import { useState } from 'react'
import { Card, Seg, TxTable, useApi, monthEnd } from '../lib'
import { CashflowChart, ForecastChart } from './widgets'
export default function CashFlow() {
  const [real, setReal] = useState(false); const [m, setM] = useState<string | null>(null)
  const end = m ? monthEnd(m) : ''
  const [tx] = useApi<any[]>(m ? `/transactions?since=${m}-01&until=${end}` : null, [m])
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Cash flow</h1>
    <Card title="Monthly income vs spend (transfers & card payments excluded) — click a month to drill down" right={<Seg value={real} set={setReal} options={[[false, 'Nominal'], [true, 'Real (CPI, today $)']]} />}>
      <CashflowChart h={400} real={real} onMonth={setM} /></Card>
    {m && <Card title={`Transactions in ${m}`} right={<button onClick={() => setM(null)} className="text-zinc-500">clear</button>}><TxTable rows={tx || []} /></Card>}
    <Card title="Spend forecast — EWMA level + damped trend, 80% interval"><ForecastChart h={320} /></Card></div>
}
