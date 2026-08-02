import { Bot, Database, ShieldCheck, Wrench } from "lucide-react";

const foundations = [
  { icon: Bot, label: "Mock-first AI provider boundary" },
  { icon: Database, label: "PostgreSQL + pgvector architecture" },
  { icon: ShieldCheck, label: "SQL-authoritative pricing guardrail" },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-100 lg:grid lg:grid-cols-[300px_1fr]">
      <aside className="bg-slate-950 px-7 py-9 text-white">
        <div className="flex items-center gap-3">
          <span className="rounded-xl bg-cyan-500 p-2 text-slate-950"><Wrench aria-hidden="true" /></span>
          <div><p className="font-bold">Service Intelligence</p><p className="text-xs text-slate-400">Industrial maintenance demo</p></div>
        </div>
        <nav aria-label="Project navigation" className="mt-12 space-y-2 text-sm">
          <p className="rounded-lg bg-slate-800 px-4 py-3 text-cyan-300">Project overview</p>
          <p className="px-4 py-3 text-slate-400">Service Assistant · Phase 5</p>
          <p className="px-4 py-3 text-slate-400">Knowledge Base · Phase 3</p>
          <p className="px-4 py-3 text-slate-400">Repair Estimates · Phase 4</p>
        </nav>
      </aside>
      <section className="px-6 py-12 sm:px-12 lg:px-16">
        <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-800">Phase 1 foundation ready</span>
        <h1 className="mt-6 max-w-4xl text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">AI Service &amp; Repair Assistant</h1>
        <p className="mt-4 max-w-3xl text-xl text-slate-600">ระบบผู้ช่วยฝ่ายบริการและประเมินค่าซ่อมเครื่องจักรด้วย RAG</p>
        <p className="mt-8 max-w-3xl leading-7 text-slate-600">A traceable, bilingual assistant for preliminary machinery diagnosis and repair estimation. This scaffold proves the web and API application boundaries before business features are introduced.</p>
        <div className="mt-10 grid max-w-5xl gap-4 md:grid-cols-3">
          {foundations.map(({ icon: Icon, label }) => (
            <article key={label} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <Icon className="text-cyan-600" aria-hidden="true" />
              <h2 className="mt-5 font-semibold">{label}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">Designed now; implemented and tested in its scheduled phase.</p>
            </article>
          ))}
        </div>
        <div className="mt-8 max-w-5xl rounded-2xl border border-blue-200 bg-blue-50 p-6 text-sm text-blue-950">
          <strong>Safety boundary:</strong> Every future diagnosis is a preliminary assessment and must be confirmed by a qualified technician.
        </div>
      </section>
    </main>
  );
}
