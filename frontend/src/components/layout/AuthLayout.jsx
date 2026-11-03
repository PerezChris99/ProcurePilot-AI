import {Link} from 'react-router-dom';
export default function AuthLayout({children}){return <main className="auth-page"><Link to="/login" className="auth-brand"><span className="brand-mark">PP</span><strong>procurepilot</strong></Link><section className="auth-card">{children}</section><p className="auth-footer">Intelligent procurement. Human-controlled purchasing.</p></main>}
