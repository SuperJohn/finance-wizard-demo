import { useState } from 'react'
import { Card, api } from '../lib'
const EX = `SELECT date_trunc('month', date) m, category, round(-sum(amount)) spend
FROM fw.txns WHERE kind IN ('expense','refund') AND date >= current_date - INTERVAL 6 MONTH
GROUP BY ALL ORDER BY m DESC, spend DESC`
export default function Explorer() {
  const [sql, setSql] = useState(EX); const [res, setRes] = useState<any>(null); const [err, setErr] = useState('')
  const run = () => { setErr(''); api('/sql', { sql, limit: 1000 }).then(setRes).catch(e => setErr(e.message)) }
  return <div className="space-y-4"><h1 className="text-xl font-semibold">SQL explorer <span className="text-xs text-zinc-500">read-only · fw.txns, fw.balances (plus lake.* catalog)</span></h1>
    <Card><textarea value={sql} onChange={e => setSql(e.target.value)} rows={7} className="w-full rounded-lg bg-zinc-950 p-2 font-mono text-xs" onKeyDown={e => (e.metaKey && e.key === 'Enter') && run()} />
      <button onClick={run} className="mt-2 rounded-lg bg-violet-600 px-3 py-1 text-sm text-white">Run (⌘↵)</button>{err && <pre className="mt-2 text-xs text-rose-400">{err}</pre>}</Card>
    {res && <Card title={`${res.rows.length} rows`}><div className="max-h-[60vh] overflow-auto"><table className="text-xs"><thead className="sticky top-0 bg-zinc-900"><tr>{res.columns.map((c: string) => <th key={c} className="px-2 text-left">{c}</th>)}</tr></thead>
      <tbody>{res.rows.map((r: any[], i: number) => <tr key={i} className="border-t border-zinc-800">{r.map((v, j) => <td key={j} className="px-2 py-0.5 font-mono">{v}</td>)}</tr>)}</tbody></table></div></Card>}</div>
}
