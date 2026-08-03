const CONFIG = {
  ready_to_file: { className: "stamp-ready", label: "Ready to file" },
  needs_attention: { className: "stamp-attention", label: "Needs attention" },
  not_ready: { className: "stamp-blocked", label: "Not ready" },
} as const;

export function StatusStamp({ status }: { status: keyof typeof CONFIG }) {
  const { className, label } = CONFIG[status] ?? CONFIG.needs_attention;
  return <span className={`stamp ${className}`}>{label}</span>;
}
