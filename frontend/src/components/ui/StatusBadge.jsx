const styles={draft:'badge-neutral',pending_approval:'badge-amber',approved:'badge-blue',payment_pending:'badge-violet',paid:'badge-green',rejected:'badge-red',cancelled:'badge-neutral',payment_failed:'badge-red',expired:'badge-neutral'};
const labels={pending_approval:'Pending approval',payment_pending:'Payment pending',payment_failed:'Payment failed'};
export default function StatusBadge({status='draft'}){const value=status.toLowerCase();return <span className={'status-badge '+(styles[value]||'badge-neutral')}>{labels[value]||value.replaceAll('_',' ')}</span>}
