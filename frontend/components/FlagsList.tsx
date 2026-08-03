import type { EligibilityFlag } from "@/lib/api";

const SEVERITY_STYLE: Record<EligibilityFlag["severity"], string> = {
  blocking: "border-brick/40 bg-brick-bg text-brick",
  warning: "border-amber/40 bg-amber-bg text-amber",
  info: "border-parchment-line bg-parchment text-ink/70",
};

export function FlagsList({ flags }: { flags: EligibilityFlag[] }) {
  if (flags.length === 0) {
    return <p className="text-sm text-sage">No open flags on this case.</p>;
  }
  return (
    <ul className="space-y-2">
      {flags.map((flag, i) => (
        <li key={i} className={`border rounded-md px-4 py-3 text-sm ${SEVERITY_STYLE[flag.severity]}`}>
          <span className="font-mono text-[10px] uppercase tracking-wider font-semibold mr-2">
            {flag.severity}
          </span>
          {flag.message}
        </li>
      ))}
    </ul>
  );
}
