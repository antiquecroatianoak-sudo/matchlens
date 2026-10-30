import {getChatGPTUser} from "../../chatgpt-auth";
export const dynamic="force-dynamic";
/** Read-only source inspection; does not assert any row is eligible for model inference. */
export async function GET(){
 const user=await getChatGPTUser();
 if(!user)return Response.json({error:"Potrebna je prijava."},{status:401});
 const base=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL;
 const key=process.env.SUPABASE_SERVICE_ROLE_KEY;
 if(!base||!key)return Response.json({error:"Izvor utakmica nije konfiguriran."},{status:503});
 try{
  const url=new URL("/rest/v1/fixtures",base);
  url.searchParams.set("select","*");
  url.searchParams.set("match_date","gte."+new Date().toISOString().slice(0,10));
  url.searchParams.set("order","match_date.asc");
  url.searchParams.set("limit","200");
  const res=await fetch(url,{headers:{apikey:key,Authorization:"Bearer "+key},cache:"no-store",signal:AbortSignal.timeout(8000)});
  if(!res.ok)throw Error("fixture fetch failed");
  const rows=await res.json();
  if(!Array.isArray(rows))throw Error("unexpected fixture response");
  return Response.json({fixtures:rows,count:rows.length,source:"configured Supabase fixtures",retrievedAt:new Date().toISOString(),verifiedPredictions:false},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"Nije moguće dohvatiti raspored utakmica."},{status:503});}
}
