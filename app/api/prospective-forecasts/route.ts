import {getChatGPTUser} from "../../chatgpt-auth";
export const dynamic="force-dynamic";

type Forecast={fixture_id:string;model_version:string;predicted_at_utc:string;kickoff_utc:string;league:string;home_team:string;away_team:string;probabilities:Record<string,number>;predicted_outcome:string;confidence:number;top25:boolean;actual_outcome:string|null;score_home:number|null;score_away:number|null};

export async function GET(){
 const user=await getChatGPTUser();
 if(!user)return Response.json({error:"Potrebna je prijava."},{status:401});
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL;
 const key=process.env.SUPABASE_SERVICE_ROLE_KEY;
 if(!url||!key)return Response.json({error:"Supabase veza nije konfigurirana."},{status:503});
 try{
  const fields="fixture_id,model_version,predicted_at_utc,kickoff_utc,league,home_team,away_team,probabilities,predicted_outcome,confidence,top25,actual_outcome,score_home,score_away";
  const query=new URLSearchParams({select:fields,order:"kickoff_utc.asc",limit:"300"});
  const res=await fetch(url+"/rest/v1/prospective_predictions?"+query.toString(),{
   headers:{apikey:key,Authorization:"Bearer "+key},cache:"no-store"});
  if(!res.ok)throw Error("Forecast query failed");
  const rows=await res.json() as Forecast[];
  if(!Array.isArray(rows))throw Error("Invalid forecast response");
  const safeRows=rows.filter(row=>row&&typeof row.fixture_id==='string'&&typeof row.kickoff_utc==='string'&&typeof row.predicted_at_utc==='string'&&Date.parse(row.predicted_at_utc)<=Date.parse(row.kickoff_utc)-60*60*1000);
  return Response.json({forecasts:safeRows},{headers:{"Cache-Control":"private, no-store"}});
 }catch{return Response.json({error:"Spremljene prognoze trenutačno nisu dostupne."},{status:503});}
}
