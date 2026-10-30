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
  url.searchParams.set("select","id,match_date,kickoff_utc,league,home_team,away_team,source,source_url,imported_at");
  url.searchParams.set("kickoff_utc","gt."+new Date().toISOString());
  url.searchParams.set("order","kickoff_utc.asc");
  url.searchParams.set("limit","200");
  const res=await fetch(url,{headers:{apikey:key,Authorization:"Bearer "+key},cache:"no-store",signal:AbortSignal.timeout(8000)});
  if(!res.ok)throw Error("fixture fetch failed");
  const rows=await res.json();
  if(!Array.isArray(rows))throw Error("unexpected fixture response");
  return Response.json({fixtures:rows,count:rows.length,source:"configured Supabase fixtures",retrievedAt:new Date().toISOString(),kickoffTimesVerified:true,verifiedPredictions:false,warning:"Kickoff timestamps are present, but source freshness and match status still require verification."},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"Nije moguće dohvatiti raspored utakmica."},{status:503});}
}
