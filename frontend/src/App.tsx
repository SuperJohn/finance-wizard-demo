import { useState } from 'react'
import { LayoutDashboard, Landmark, ArrowLeftRight, PieChart, Repeat, Hourglass, GitBranch, FlaskConical, Target, Siren, Bot, Layers, Table2 } from 'lucide-react'
import { useApi } from './lib'
import Dashboard from './pages/Dashboard'
import NetWorth from './pages/NetWorth'
import CashFlow from './pages/CashFlow'
import Spending from './pages/Spending'
import Recurring from './pages/Recurring'
import Runway from './pages/Runway'
import Scenarios from './pages/Scenarios'
import Decomposition from './pages/Decomposition'
import Anomalies from './pages/Anomalies'
import Analytics from './pages/Analytics'
import Goals from './pages/Goals'
import Explorer from './pages/Explorer'
import Agent from './components/Agent'

const PAGES: [string, string, any, any][] = [
  ['dash', 'Dashboard', LayoutDashboard, Dashboard], ['nw', 'Net worth', Landmark, NetWorth], ['cf', 'Cash flow', ArrowLeftRight, CashFlow],
  ['sp', 'Spending', PieChart, Spending], ['rec', 'Recurring', Repeat, Recurring], ['run', 'Runway', Hourglass, Runway],
  ['scn', 'Scenarios', GitBranch, Scenarios], ['dec', 'Decomposition', Layers, Decomposition], ['ano', 'Anomalies', Siren, Anomalies],
  ['an', 'Economics lab', FlaskConical, Analytics], ['goal', 'Goals & budgets', Target, Goals], ['sql', 'SQL explorer', Table2, Explorer],
]

export default function App() {
  const [page, setPage] = useState(() => location.hash.slice(1) || 'dash')
  const [agentOpen, setAgentOpen] = useState(true)
  const [health] = useApi<any>('/health')
  const go = (p: string) => { setPage(p); location.hash = p }
  const P = (PAGES.find(p => p[0] === page) || PAGES[0])[3]
  return <div className="flex h-screen overflow-hidden">
    <nav className="flex w-56 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950 p-3">
      <div className="mb-5 flex items-center gap-2 px-2 pt-1"><div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-400 font-bold text-black">₩</div>
        <div><div className="text-sm font-semibold">Finance Lab</div><div className="text-[10px] text-zinc-500">local · private · agent-first</div></div></div>
      {PAGES.map(([id, label, Icon]) => <button key={id} onClick={() => go(id)}
        className={'mb-0.5 flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm ' + (page === id ? 'bg-violet-600/20 text-violet-200' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200')}>
        <Icon size={15} />{label}</button>)}
      <div className="mt-auto space-y-2 px-2 text-[10px] text-zinc-600">
        <div>Data: {health?.source?.startsWith('lake') ? <span className="text-emerald-500">finance lake (read-only snapshot)</span> : <span className="text-amber-500">{health?.source || '…'}</span>}</div>
        <div>Bound to 127.0.0.1 only</div></div>
    </nav>
    <main className="min-w-0 flex-1 overflow-y-auto p-6"><P go={go} /></main>
    {agentOpen ? <Agent close={() => setAgentOpen(false)} /> :
      <button onClick={() => setAgentOpen(true)} className="fixed bottom-6 right-6 flex items-center gap-2 rounded-full bg-violet-600 px-4 py-3 text-sm font-medium text-white shadow-xl"><Bot size={16} />Ask Wizard</button>}
  </div>
}
