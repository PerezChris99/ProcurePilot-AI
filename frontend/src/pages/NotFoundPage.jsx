import {Link} from 'react-router-dom';
export default function NotFoundPage(){return <section className="panel not-found"><span className="eyebrow">404 — PAGE NOT FOUND</span><h1>This page isn't in the workspace.</h1><p>The address may be incorrect or the page may have moved.</p><Link to="/" className="button button-primary">Return to overview</Link></section>}
