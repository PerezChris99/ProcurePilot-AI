// PayPal Sandbox opens separately; only the backend-issued HTTPS link is trusted.
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

// Call synchronously from the buyer's click, BEFORE calling the asynchronous
// checkout API; browsers may block window.open after the await.
export function reservePayPalSandboxTab(openTab=()=>window.open('about:blank','_blank')){
  let tab;
  try{tab=openTab()}catch{return null}
  if(!tab||tab.closed)return null;
  try{
    // A trusted about:blank tab initially inherits sessionStorage from this
    // origin. This lets ProcurePilot authenticate the PayPal return page.
    // Detach window.opener before navigating to untrusted external content.
    tab.opener=null;
    tab.document.title='Preparing PayPal Sandbox checkout';
    tab.document.body.textContent='Connecting to PayPal Sandbox…';
  }catch{
    // Navigation can still be attempted if the browser isolates the document.
  }
  return tab;
}

// Never fall back to navigating the original application tab.
export function navigatePayPalSandboxTab(rawUrl,tab){
  const approved=verifiedSandboxApprovalUrl(rawUrl);
  if(!tab||tab.closed)return false;
  try{
    tab.location.replace(approved);
    return true;
  }catch{return false}
}

export function closePendingPayPalTab(tab){
  if(!tab||tab.closed)return;
  try{tab.close()}catch{}
}
