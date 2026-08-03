import Link from "next/link";

const STEPS = [
  { label: "Intake", text: "Paralegals drop every client document into the case — scans, photos, PDFs, no sorting required." },
  { label: "Extraction", text: "Each document is classified and its dates, names, and reference numbers are pulled out automatically." },
  { label: "Cross-check", text: "The set is checked against the visa category's requirements: what's missing, what conflicts, what's expiring." },
  { label: "Briefing", text: "The attorney opens one page: a timeline, a flagged checklist, and a plain-language note — not a legal opinion, a head start." },
];

export default function LandingPage() {
  return (
    <main>
      <nav className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
        <span className="font-display text-xl">Casefile</span>
        <div className="flex gap-6 items-center text-sm">
          <Link href="/pricing" className="text-ink/70 hover:text-ink">Pricing</Link>
          <Link href="/login" className="text-ink/70 hover:text-ink">Log in</Link>
          <Link href="/signup" className="bg-ink text-parchment px-4 py-2 rounded-sm hover:bg-brass-dark transition-colors">
            Start free
          </Link>
        </div>
      </nav>

      <header className="max-w-5xl mx-auto px-6 pt-16 pb-20 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="font-display text-5xl leading-[1.1] mb-6">
            Every case document,<br />reviewed before your<br />attorney opens the file.
          </h1>
          <p className="text-lg text-ink/70 mb-8 max-w-md">
            Casefile reads every passport, I-797, and employment letter in a case,
            checks it against the visa category&apos;s requirements, and hands your
            attorneys a one-page briefing instead of a stack of scans.
          </p>
          <div className="flex gap-4 items-center">
            <Link href="/signup" className="bg-ink text-parchment px-5 py-3 rounded-sm hover:bg-brass-dark transition-colors">
              Start your first case free
            </Link>
            <span className="text-sm text-ink/50">No card required</span>
          </div>
        </div>

        <div className="bg-paper border border-parchment-line rounded-md p-6 rotate-1">
          <div className="flex items-center justify-between mb-4">
            <p className="font-mono text-xs text-ink/50">#A18F3C2E — H-1B</p>
            <span className="stamp stamp-attention">Needs attention</span>
          </div>
          <ul className="space-y-2 text-sm">
            <li className="flex gap-2 items-start">
              <span className="text-brick mt-0.5">●</span>
              <span>No degree certificate uploaded yet — required for H-1B.</span>
            </li>
            <li className="flex gap-2 items-start">
              <span className="text-amber mt-0.5">●</span>
              <span>I-797 validity window ends before the proposed employment start date.</span>
            </li>
            <li className="flex gap-2 items-start">
              <span className="text-sage mt-0.5">●</span>
              <span>Passport, employment letter — verified, no conflicts.</span>
            </li>
          </ul>
        </div>
      </header>

      <section className="bg-ink text-parchment py-16">
        <div className="max-w-5xl mx-auto px-6 grid md:grid-cols-4 gap-8">
          {STEPS.map((step, i) => (
            <div key={step.label}>
              <p className="font-mono text-xs text-brass mb-2">0{i + 1}</p>
              <h3 className="font-display text-lg mb-2">{step.label}</h3>
              <p className="text-sm text-parchment/70">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-3xl mx-auto px-6 py-20 text-center">
        <h2 className="font-display text-3xl mb-4">Built for boutique practices, not enterprise legal.</h2>
        <p className="text-ink/70 mb-8">
          One flat rate per firm. No per-seat pricing, no annual contract, no setup call required.
        </p>
        <Link href="/pricing" className="bg-ink text-parchment px-5 py-3 rounded-sm inline-block hover:bg-brass-dark transition-colors">
          See pricing
        </Link>
      </section>
    </main>
  );
}
