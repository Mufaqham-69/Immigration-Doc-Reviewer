import Link from "next/link";

export default function PricingPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-20 text-center">
      <h1 className="font-display text-4xl mb-4">One rate. Every case.</h1>
      <p className="text-ink/70 mb-12">No per-seat fees. No per-document metering. Cancel any time.</p>

      <div className="bg-paper border border-parchment-line rounded-md p-10 max-w-sm mx-auto">
        <p className="font-mono text-xs text-brass uppercase tracking-wider mb-2">Standard</p>
        <p className="font-display text-5xl mb-1">$100</p>
        <p className="text-sm text-ink/50 mb-8">per firm, per month</p>
        <ul className="text-sm text-left space-y-3 mb-8">
          <li>— Unlimited cases and clients</li>
          <li>— Unlimited document uploads</li>
          <li>— All supported visa categories</li>
          <li>— Unlimited attorney and paralegal seats</li>
        </ul>
        <Link
          href="/signup"
          className="block bg-ink text-parchment px-5 py-3 rounded-sm hover:bg-brass-dark transition-colors"
        >
          Start free, add a card later
        </Link>
      </div>
    </main>
  );
}
