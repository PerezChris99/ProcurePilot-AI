/**
 * Fetch the minimal destination code while login/register waits on the
 * authenticated API response. This never calls an API or accesses secrets.
 * Errors here cannot block a valid sign-in; the route will retry normally.
 */
export function preloadWorkspace(destination='/dashboard'){
  void import('../components/layout/AppShell.jsx').catch(()=>{});
  const route=destination.startsWith('/orders') ? import('./OrdersPage.jsx')
    : destination.startsWith('/procurement') ? import('./ProcurementPage.jsx')
    : destination.startsWith('/approvals') ? import('./ApprovalsPage.jsx')
    : destination.startsWith('/discovery') ? import('./DiscoveryPage.jsx')
    : destination.startsWith('/requests/') ? import('./RequestDetailPage.jsx')
    : destination.startsWith('/activity') ? import('./ActivityPage.jsx')
    : destination.startsWith('/trust-lab') ? import('./TrustLabPage.jsx')
    : import('./DashboardPage.jsx');
  void route.catch(()=>{});
}
