"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Case } from "@/lib/api";
import { CaseCard } from "@/components/CaseCard";

const VISA_CATEGORIES = ["H-1B", "EB-2 NIW", "F-1 OPT", "L-1A"];

export default function DashboardPage() {
  const router = useRouter();
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    api.listCases().then(setCases).catch(() => router.push("/login")).finally(() => setLoading(false));
  }, [router]);

  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display text-3xl">Cases</h1>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="bg-ink text-parchment px-4 py-2 rounded-sm hover:bg-brass-dark transition-colors"
        >
          New case
        </button>
      </div>

      {showForm && (
        <NewCaseForm
          onCreated={(c) => {
            setCases((prev) => [c, ...prev]);
            setShowForm(false);
            router.push(`/dashboard/cases/${c.id}`);
          }}
        />
      )}

      {loading ? (
        <p className="text-ink/50">Loading cases…</p>
      ) : cases.length === 0 ? (
        <p className="text-ink/50">No cases yet. Start one to upload your first client documents.</p>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {cases.map((c) => <CaseCard key={c.id} c={c} />)}
        </div>
      )}
    </main>
  );
}

function NewCaseForm({ onCreated }: { onCreated: (c: Case) => void }) {
  const [clientName, setClientName] = useState("");
  const [visaCategory, setVisaCategory] = useState(VISA_CATEGORIES[0]);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const created = await api.createCase({ client_name: clientName, visa_category: visaCategory });
      onCreated(created);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-paper border border-parchment-line rounded-md p-6 mb-8 flex gap-4 items-end">
      <label className="text-sm flex-1">
        <span className="text-ink/70 mb-1 block">Client name</span>
        <input
          required
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
          className="w-full border border-parchment-line rounded-sm px-3 py-2 focus:border-brass outline-none"
        />
      </label>
      <label className="text-sm">
        <span className="text-ink/70 mb-1 block">Visa category</span>
        <select
          value={visaCategory}
          onChange={(e) => setVisaCategory(e.target.value)}
          className="border border-parchment-line rounded-sm px-3 py-2 focus:border-brass outline-none"
        >
          {VISA_CATEGORIES.map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
      </label>
      <button disabled={busy} className="bg-ink text-parchment px-4 py-2 rounded-sm hover:bg-brass-dark transition-colors">
        {busy ? "Creating…" : "Create case"}
      </button>
    </form>
  );
}
