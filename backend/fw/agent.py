"""Model-agnostic tool-using agent. Uses a JSON protocol (works with any Ollama
model, including ones without native tool calling). Local by default; an
OpenAI-compatible cloud model is used only if configured AND requested."""
import json
import datetime as dt
import httpx
from . import config, tools

SYSTEM = """You are Finance Lab, a private, local-first financial analyst for the user.
Be precise, quantitative and concise; show numbers, cite which tool produced them, and mention caveats (e.g., transfers excluded, partial months).
Today is {today}. Amounts: negative = outflow in fw.txns.
Tools:
{tools}
Respond with ONLY a JSON object, either
{{"tool": "<name>", "args": {{...}}}}   to call a tool, or
{{"answer": "<markdown answer>"}}        when done.
Call at most one tool per message. Prefer specific tools; use run_sql for anything custom. Only use ACTION tools when the user asks for a change."""


def _chat(messages, model=None, cloud=False):
    if cloud:
        if not (config.CLOUD_BASE_URL and config.CLOUD_API_KEY):
            raise RuntimeError("Cloud model not configured (FW_CLOUD_BASE_URL / FW_CLOUD_API_KEY in .env)")
        r = httpx.post(f"{config.CLOUD_BASE_URL.rstrip('/')}/chat/completions", timeout=180,
                       headers={"Authorization": f"Bearer {config.CLOUD_API_KEY}"},
                       json={"model": model or config.CLOUD_MODEL, "messages": messages, "response_format": {"type": "json_object"}})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    r = httpx.post(f"{config.OLLAMA_URL}/api/chat", timeout=300,
                   json={"model": model or config.MODEL, "messages": messages, "stream": False, "format": "json", "options": {"temperature": 0.2, "num_ctx": 16384}})
    r.raise_for_status()
    return r.json()["message"]["content"]


def _parse(s: str):
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`").split("\n", 1)[-1]
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        i, j = s.find("{"), s.rfind("}")
        if i >= 0 and j > i:
            try:
                return json.loads(s[i:j + 1])
            except json.JSONDecodeError:
                pass
    return {"answer": s}


def run(history: list[dict], model=None, cloud=False, max_steps=6, chat=None):
    chat = chat or _chat
    msgs = [{"role": "system", "content": SYSTEM.format(today=dt.date.today().isoformat(), tools=tools.catalog())}] + history
    trace = []
    for _ in range(max_steps):
        out = _parse(chat(msgs, model, cloud))
        if "tool" in out:
            name, args = out["tool"], out.get("args") or {}
            try:
                res = tools.call(name, args); ok = True
            except Exception as e:
                res = {"error": str(e)}; ok = False
            txt = json.dumps(res, default=str)
            if len(txt) > 12000:
                txt = txt[:12000] + "...(truncated)"
            trace.append({"tool": name, "args": args, "ok": ok, "result": res})
            msgs += [{"role": "assistant", "content": json.dumps(out)}, {"role": "user", "content": f"TOOL_RESULT {name}: {txt}"}]
            continue
        return {"answer": out.get("answer", str(out)), "trace": trace}
    return {"answer": "I hit the step limit; partial results are in the trace.", "trace": trace}


def models():
    try:
        r = httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
        local = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        local = []
    return {"default": config.MODEL, "local": local, "cloud": bool(config.CLOUD_BASE_URL and config.CLOUD_API_KEY), "cloud_model": config.CLOUD_MODEL}
