import {getChatGPTUser} from "../../chatgpt-auth";
export const dynamic="force-dynamic";

/** Diagnostics only: never treats a configured URL or a row count as proof of a validated model. */
export async function GET(){
 const user=await getChatGPTUser();
 if(!user)return Response.json({error:"Potrebna je prijava."},{status:401});
 const blockers:string[]=[];
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL;
 const key=process.env.SUPABASE_SERVICE_ROLE_KEY;
 let upcoming=0;
 if(!url||!key){blockers.push("Izvor rasporeda nije konfiguriran.");}
 else {
  try {
   const u=new URL("/rest/v1/fixtures",url);
   u.searchParams.set("select","id");
   u.searchParams.set("match_date","gte."+new Date().toISOString().slice(0,10));
   u.searchParams.set("limit","0");
   const r=await fetch(u,{headers:{apikey:key,Authorization:"Bearer "+key,Prefer:"count=exact"},cache:"no-store",signal:AbortSignal.timeout(8000)});
   if(!r.ok)throw Error("fixtures unavailable");
   upcoming=Number(r.headers.get("content-range")?.split("/")[1]);
   if(!Number.isSafeInteger(upcoming)||upcoming<0)throw Error("missing count");
   if(upcoming===0)blockers.push("Nema budućih utakmica u postojećoj bazi.");
  }catch{blockers.push("Nije moguće potvrditi buduće utakmice iz baze.");}
 }
 // Deliberately fail closed until actual verified model and immutable pre-kickoff writer are wired.
 blockers.push("Nije potvrđen povezani trenirani i kalibrirani model.");
 blockers.push("Nije potvrđeno automatsko zaključavanje prognoza prije početka utakmice.");
 return Response.json({ready:false,upcomingFixtures:upcoming,blockers,checkedAt:new Date().toISOString()}, {headers:{"Cache-Control":"no-store"}});
}
