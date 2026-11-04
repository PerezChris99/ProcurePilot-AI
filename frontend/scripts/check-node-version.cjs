'use strict';

// Keep CMD metacharacters out of start.bat. This separate Node program can
// safely parse versions without quotes, parentheses or || in batch blocks.
function supportsVite7(version) {
  const value=String(version||'').replace(/^v/,'');
  if(!/^\d+\.\d+\.\d+$/.test(value))return false;
  const [major,minor]=value.split('.').map(Number);
  return (major===20&&minor>=19)||(major>=22&&(major>22||minor>=12));
}

if(require.main===module){
  const actual=process.versions.node;
  if(!supportsVite7(actual)){
    console.error('[ERROR] Node.js '+actual+' is incompatible with Vite 7.');
    console.error('Use Node.js 20.19+ or 22.12+ (LTS is preferred).');
    process.exitCode=1;
  }else{
    console.log('[OK] Node.js '+actual+' meets the Vite 7 minimum.');
  }
}

module.exports={supportsVite7};
