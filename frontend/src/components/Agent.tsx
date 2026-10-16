import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import { Bot, X, Send, Wrench, Cloud, Cpu } from 'lucide-react'
import { api, useApi } from '../lib'

const SUGGEST = ['How long is my runway if I take a 3-month sabbatical?', 'What subscriptions can I cut, and what would that save per year?',
  'Why was September spending higher than August?', 'Flag anything unusual in the last 60 days', 'Set a $400/mo budget for Restaurants & Bars']

export default function Agent({ close }: { close: () => void }) {
  const [msgs, setMsgs] = useState<any[]>([])
  const [input, setInput] = useState(''); const [busy, setBusy] = useState(false)
  const [models] = useApi<any>('/models')
  const [model, setModel] = useState(''); const [cloud, setCloud] = useState(false)
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { if (models && !model) setModel(models.local.includes(models.default) ? models.default : models.local[0] || models.default) }, [models])
  useEffect(() => end.current?.scrollIntoView({ behavior: 'smooth' }), [msgs, busy])
  async function send(text: string) {
    if (!text.trim()) return
    const hist = [...msgs, { role: 'user', content: text }]; setMsgs(hist); setInput(''); setBusy(true)
    try {
      const r = await api('/agent', { messages: hist.map(m => ({ role: m.role, content: m.content })), model: cloud ? undefined : model, cloud })
      setMsgs([...hist, { role: 'assistant', content: r.answer, trace: r.trace }])
    } catch (e: any) { setMsgs([...hist, { role: 'assistant', content: '⚠️ ' + e.message }]) }
    setBusy(false)
  }
  return <aside className="flex w-[400px] shrink-0 flex-col border-l border-zinc-800 bg-zinc-950">
    <div className="flex items-center justify-between border-b border-zinc-800 p-3">
      <div className="flex items-center gap-2 text-sm font-semibold"><Bot size={16} className="text-violet-400" />Wizard</div>
      <div className="flex items-center gap-2">
        {!cloud && <select value={model} onChange={e => setModel(e.target.value)} className="max-w-[150px] rounded bg-zinc-900 px-1 py-0.5 text-xs">{models?.local.map((m: string) => <option key={m}>{m}</option>)}</select>}
        <button title={models?.cloud ? 'Toggle cloud model' : 'Cloud model not configured (.env)'} disabled={!models?.cloud} onClick={() => setCloud(!cloud)}
          className={'rounded p-1 ' + (cloud ? 'bg-cyan-700 text-white' : 'text-zinc-500 disabled:opacity-30')}>{cloud ? <Cloud size={14} /> : <Cpu size={14} />}</button>
        <button onClick={close} className="text-zinc-500 hover:text-zinc-200"><X size={16} /></button></div></div>
    <div className="flex-1 space-y-3 overflow-y-auto p-3 text-sm">
      {msgs.length === 0 && <div className="space-y-2"><p className="text-xs text-zinc-500">Ask anything about your money. I query your lake with typed tools (SQL, forecast, anomalies, subscriptions, runway) and can take actions (categorize, budgets, goals). Runs on your local model by default.</p>
        {SUGGEST.map(s => <button key={s} onClick={() => send(s)} className="block w-full rounded-lg border border-zinc-800 p-2 text-left text-xs text-zinc-300 hover:border-violet-600">{s}</button>)}</div>}
      {msgs.map((m, i) => <div key={i} className={m.role === 'user' ? 'ml-8 rounded-xl bg-violet-600/20 p-2' : 'mr-2'}>
        {m.trace?.length > 0 && <details className="mb-1 text-[11px] text-zinc-500"><summary className="cursor-pointer"><Wrench size={11} className="mr-1 inline" />{m.trace.length} tool call(s): {m.trace.map((t: any) => t.tool).join(', ')}</summary>
          {m.trace.map((t: any, j: number) => <pre key={j} className="mt-1 max-h-40 overflow-auto rounded bg-zinc-900 p-1 text-[10px]">{t.tool}({JSON.stringify(t.args)}) → {JSON.stringify(t.result).slice(0, 1500)}</pre>)}</details>}
        <div className="prose-sm"><Markdown>{m.content}</Markdown></div></div>)}
      {busy && <div className="animate-pulse text-xs text-zinc-500">thinking with {cloud ? 'cloud model' : model}…</div>}
      <div ref={end} /></div>
    <form onSubmit={e => { e.preventDefault(); send(input) }} className="flex gap-2 border-t border-zinc-800 p-3">
      <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask or instruct…" className="flex-1 rounded-lg bg-zinc-900 px-3 py-2 text-sm outline-none ring-violet-600 focus:ring-1" />
      <button disabled={busy} className="rounded-lg bg-violet-600 px-3 text-white disabled:opacity-50"><Send size={14} /></button></form>
  </aside>
}
