import {getChatGPTUser} from "../../chatgpt-auth";
export const dynamic="force-dynamic";
export async function GET(){
 const user=await getChatGPTUser();
 if(!user)return Response.json({error:"Potrebna je prijava."},{status:401});
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL;
 const key=process.env.SUPABASE_SERVICE_ROLE_KEY;
 if(!url||!key)return Response.json({error:"Supabase veza nije konfigurirana."},{status:503});
 try{
  const headers={apikey:key,Authorization:"Bearer "+key,Prefer:"count=exact"};
  const [all,upcoming,latest]=await Promise.all([
   fetch(url+"/rest/v1/fixtures?select=id&limit=0",{headers,cache:"no-store"}),
   fetch(url+"/rest/v1/fixtures?select=id&match_date=gte."+new Date().toISOString().slice(0,10)+"&limit=0",{headers,cache:"no-store"}),
   fetch(url+"/rest/v1/fixtures?select=match_date&order=match_date.desc&limit=1",{headers,cache:"no-store"})
  ]);
  if(!all.ok||!upcoming.ok||!latest.ok)throw Error("Supabase query failed");
  const count=(r:Response)=>Number(r.headers.get("content-range")?.split("/")[1]||0);
  const rows=await latest.json();
  return Response.json({total:count(all),upcoming:count(upcoming),latest:rows[0]?.match_date??null},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"Podaci o utakmicama nisu dostupni."},{status:503})}
}
