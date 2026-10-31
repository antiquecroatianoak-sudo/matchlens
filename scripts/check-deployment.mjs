#!/usr/bin/env node
// Public, unauthenticated deployment smoke test. Never submit credentials.
const base=process.argv[2];
if(!base){console.error("Usage: node scripts/check-deployment.mjs https://your-matchlens-host");process.exit(2)}
let url;
try{url=new URL(base);if(url.protocol!=="https:")throw Error("HTTPS required");}
catch{console.error("Supply a valid HTTPS URL");process.exit(2)}
const checks=[
 {path:"/",expect:[200],label:"App page"},
 {path:"/api/prospective-forecasts",expect:[401],label:"Forecasts protected"},
 {path:"/api/fixture-coverage",expect:[401],label:"Fixture data protected"},
 {path:"/api/records",expect:[401],label:"Private records protected"},
 {path:"/api/session",expect:[405],label:"Session endpoint disallows GET"},
];
let failed=0;
for(const check of checks){
 try{
  const response=await fetch(new URL(check.path,url),{redirect:"manual",signal:AbortSignal.timeout(10000),headers:{Accept:"application/json"}});
  const ok=check.expect.includes(response.status);
  console.log((ok?"PASS":"FAIL")+" "+check.label+" "+check.path+" HTTP "+response.status);
  if(!ok)failed++;
 }catch(e){console.log("FAIL "+check.label+" "+check.path+" "+e.message);failed++}
}
if(failed){console.error(failed+" deployment checks failed");process.exitCode=1}
else console.log("Public checks passed. Login, refresh and logout still require a separate authenticated test.");
