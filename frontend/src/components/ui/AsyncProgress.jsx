/**
 * Indeterminate progress: shows real pending work without inventing
 * percentage completion for an HTTP request or dynamic module load.
 */
export default function AsyncProgress({label='Working securely…',compact=false}){
  return <div className={'async-progress'+(compact?' async-progress-compact':'')} role="status" aria-live="polite" aria-atomic="true">
    <div className="async-progress-track" role="progressbar"
      aria-label={label} aria-valuetext={label}>
      <span className="async-progress-indicator"/>
    </div>
    <p className="async-progress-label">{label}</p>
  </div>;
}
