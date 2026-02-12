const STATUS_MAP: Record<string, { label: string; className: string }> = {
  ready_now: { label: 'Ready Now', className: 'badge badge--ready' },
  getting_ready: { label: 'Getting Ready', className: 'badge badge--getting-ready' },
  not_ready: { label: 'Not Ready', className: 'badge badge--not-ready' },
  exit_alert: { label: 'Exit Alert', className: 'badge badge--exit' },
};

export default function ReadinessBadge({ status }: { status: string }) {
  const info = STATUS_MAP[status] || { label: status, className: 'badge' };
  return <span className={info.className}>{info.label}</span>;
}
