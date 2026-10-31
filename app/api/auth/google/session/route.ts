import {cookies} from "next/headers";
export async function POST(req:Request){
 const origin=new URL(req.url).origin;
 if(req.headers.get("origin")!==origin)return Response.json({error:"Neispravan izvor."},{status:403});
 const {access_token,refresh_token}=await req.json().catch(()=>({})) as {access_token?:unknown;refresh_token?:unknown};
 if(typeof access_token!=="string"||typeof refresh_token!=="string"||access_token.length>8192||refresh_token.length>8192)return Response.json({error:"Neispravna sesija."},{status:400});
 const base=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL,key=process.env.SUPABASE_ANON_KEY,owner=process.env.MATCHLENS_ALLOWED_USER_ID;
 if(!base||!key||!owner)return Response.json({error:"Prijava nije konfigurirana."},{status:503});
 try{
  const response=await fetch(new URL("/auth/v1/user",base),{headers:{apikey:key,Authorization:"Bearer "+access_token},cache:"no-store"});
  if(!response.ok)return Response.json({error:"Google sesija nije valjana."},{status:401});
  const user=await response.json() as {id?:string;app_metadata?:{providers?:string[]}};
  if(user.id!==owner)return Response.json({error:"Ovaj Google račun nema pristup privatnom MatchLensu."},{status:403});
  if(!user.app_metadata?.providers?.includes("google"))return Response.json({error:"Prijava mora biti putem Googlea."},{status:403});
  const jar=await cookies();const secure=process.env.NODE_ENV==="production";
  jar.set("matchlens_access_token",access_token,{httpOnly:true,secure,sameSite:"lax",path:"/",maxAge:3600});
  jar.set("matchlens_refresh_token",refresh_token,{httpOnly:true,secure,sameSite:"lax",path:"/api/session",maxAge:2592000});
  return Response.json({ok:true},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"Provjera Google prijave nije dostupna."},{status:503});}
}