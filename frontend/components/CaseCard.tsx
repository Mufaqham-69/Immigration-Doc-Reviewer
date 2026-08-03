import Link from "next/link";
import type { Case } from "@/lib/api";
import { StatusStamp } from "./StatusStamp";

export function CaseCard({ c }: { c: Case }) {
  return (
    <Link
      href={`/dashboard/cases/${c.id}`}
      className="block bg-paper border border-parchment-line rounded-md p-5 hover:border-brass transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs text-ink/50 mb-1">#{c.id.slice(0, 8)}</p>
          <h3 className="font-display text-lg">{c.visa_category}</h3>
        </div>
        {c.eligibility_summary ? (
          <StatusStamp status={c.eligibility_summary.overall_readiness} />
        ) : (
          <span className="stamp text-ink/50 bg-parchment border-parchment-line">Processing</span>
        )}
      </div>
      {c.eligibility_summary && (
        <p className="text-sm text-ink/70 mt-3 line-clamp-2">{c.eligibility_summary.attorney_notes}</p>
      )}
    </Link>
  );
}
