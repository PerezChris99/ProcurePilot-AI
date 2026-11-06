// Checkout is an authenticated, human-initiated PayPal Sandbox redirect.
// Only use the backend-verified HTTPS approval link, never arbitrary provider URLs.
const SANDBOX_HOSTS=new Set(['www.sandbox.paypal.com','sandbox.paypal.com']);

export function verifiedSandboxApprovalUrl(raw){
  let url;
  try{url=new URL(raw)}
  catch{throw new Error('PayPal did not return a valid Sandbox approval URL.')}
  if(url.protocol!=='https:'||!SANDBOX_HOSTS.has(url.hostname.toLowerCase())||
     url.username||url.password||url.port){
    throw new Error('PayPal returned an unexpected checkout host. Navigation was blocked.');
  }
  return url.href;
}

export function redirectToPayPalSandbox(url,navigate=target=>window.location.assign(target)){
  const approved=verifiedSandboxApprovalUrl(url);
  navigate(approved); // same tab: sessionStorage survives the return to /orders
}
