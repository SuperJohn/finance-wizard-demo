import { Card, useApi, usd } from '../lib'
import { NetWorthChart } from './widgets'
export default function NetWorth() {
  const [a] = useApi<any[]>('/accounts')
  const groups = ['cash', 'investment', 'property', 'liability']
  return <div className="space-y-4"><h1 className="text-xl font-semibold">Net worth</h1>
    <Card title="Composition (drag the slider / scroll to zoom, click legend to isolate)"><NetWorthChart h={420} /></Card>
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">{groups.map(g => <Card key={g} title={g[0].toUpperCase() + g.slice(1)} right={<span className="font-mono">{usd(a?.filter(x => x.klass === g).reduce((s, x) => s + x.balance, 0))}</span>}>
      {a?.filter(x => x.klass === g).map(x => <div key={x.account} className="flex justify-between py-0.5 text-xs"><span className="truncate text-zinc-400">{x.account}</span><span className="font-mono">{usd(x.balance)}</span></div>)}</Card>)}</div></div>
}
