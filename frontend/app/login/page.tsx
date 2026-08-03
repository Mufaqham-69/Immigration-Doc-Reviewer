"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const { access_token } = await api.login(email, password);
      localStorage.setItem("access_token", access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="max-w-sm mx-auto px-6 py-20">
      <h1 className="font-display text-3xl mb-8">Log in</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block text-sm">
          <span className="text-ink/70 mb-1 block">Email</span>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-parchment-line rounded-sm px-3 py-2 bg-paper focus:border-brass outline-none"
          />
        </label>
        <label className="block text-sm">
          <span className="text-ink/70 mb-1 block">Password</span>
          <input
            required
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-parchment-line rounded-sm px-3 py-2 bg-paper focus:border-brass outline-none"
          />
        </label>
        {error && <p className="text-brick text-sm">{error}</p>}
        <button
          disabled={busy}
          className="w-full bg-ink text-parchment px-5 py-3 rounded-sm hover:bg-brass-dark transition-colors disabled:opacity-50"
        >
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="text-sm text-ink/60 mt-6">
        No account yet? <Link href="/signup" className="text-brass">Set up your firm</Link>
      </p>
    </main>
  );
}
