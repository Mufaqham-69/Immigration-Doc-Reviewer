"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [firmName, setFirmName] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const { access_token } = await api.signup({ firm_name: firmName, full_name: fullName, email, password });
      localStorage.setItem("access_token", access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="max-w-sm mx-auto px-6 py-20">
      <h1 className="font-display text-3xl mb-8">Set up your firm</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label="Firm name" value={firmName} onChange={setFirmName} />
        <Field label="Your name" value={fullName} onChange={setFullName} />
        <Field label="Email" type="email" value={email} onChange={setEmail} />
        <Field label="Password" type="password" value={password} onChange={setPassword} />
        {error && <p className="text-brick text-sm">{error}</p>}
        <button
          disabled={busy}
          className="w-full bg-ink text-parchment px-5 py-3 rounded-sm hover:bg-brass-dark transition-colors disabled:opacity-50"
        >
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className="text-sm text-ink/60 mt-6">
        Already have an account? <Link href="/login" className="text-brass">Log in</Link>
      </p>
    </main>
  );
}

function Field({
  label, value, onChange, type = "text",
}: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <label className="block text-sm">
      <span className="text-ink/70 mb-1 block">{label}</span>
      <input
        required
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-parchment-line rounded-sm px-3 py-2 bg-paper focus:border-brass outline-none"
      />
    </label>
  );
}
