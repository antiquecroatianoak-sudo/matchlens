import {cookies} from "next/headers";
export const dynamic="force-dynamic";
export async function POST(req:Request){
 const origin=req.headers.get("origin");if(origin&&origin!==new URL(req.url).origin)return Response.json({error:"Neispravan izvor."},{status:403});
 const {email,password}=await req.json().catch(()=>({})) as {email?:string;password?:string};
 if(typeof email!=="string"||typeof password!=="string"||email.length>254||password.length>1024)return Response.json({error:"Unesite e-mail i lozinku."},{status:400});
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL,key=process.env.SUPABASE_ANON_KEY;
 if(!url||!key)return Response.json({error:"Prijava nije konfigurirana."},{status:503});
 try{
 const res=await fetch(new URL("/auth/v1/token?grant_type=password",url),{method:"POST",headers:{"Content-Type":"application/json",apikey:key},body:JSON.stringify({email,password}),cache:"no-store"});
 if(!res.ok)return Response.json({error:"Prijava nije uspjela. Provjerite podatke."},{status:401});
 const data=await res.json() as {access_token?:string;refresh_token?:string;expires_in?:number};
 if(!data.access_token||!data.refresh_token)return Response.json({error:"Prijava nije uspjela."},{status:502});
 const verified=await fetch(new URL("/auth/v1/user",url),{headers:{apikey:key,Authorization:"Bearer "+data.access_token},cache:"no-store"});
 if(!verified.ok)return Response.json({error:"Nije moguće potvrditi korisnika."},{status:401});
 const identity=await verified.json() as {id?:string};
 const owner=process.env.MATCHLENS_ALLOWED_USER_ID;
 if(!owner)return Response.json({error:"Privatni vlasnik nije konfiguriran."},{status:503});
 if(identity.id!==owner)return Response.json({error:"Pristup nije dopušten."},{status:403});
 const jar=await cookies();jar.set("matchlens_access_token",data.access_token,{httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"lax",path:"/",maxAge:Math.min(Math.max(data.expires_in||3600,60),3600)});
 jar.set("matchlens_refresh_token",data.refresh_token,{httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"lax",path:"/api/session",maxAge:60*60*24*30});
 return Response.json({ok:true},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"Usluga prijave nije dostupna."},{status:503});}
}
export async function DELETE(req:Request){
 const origin=req.headers.get("origin");if(origin&&origin!==new URL(req.url).origin)return Response.json({error:"Neispravan izvor."},{status:403});
 const jar=await cookies();jar.delete("matchlens_access_token");jar.delete("matchlens_refresh_token");return Response.json({ok:true},{headers:{"Cache-Control":"no-store"}});
}

export async function PUT(req:Request){
 const origin=req.headers.get("origin");if(origin&&origin!==new URL(req.url).origin)return Response.json({error:"Neispravan izvor."},{status:403});
 const jar=await cookies();const refresh=jar.get("matchlens_refresh_token")?.value;
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL,key=process.env.SUPABASE_ANON_KEY;
 if(!refresh)return Response.json({error:"Sesija je istekla. Prijavite se ponovno."},{status:401});
 if(!url||!key)return Response.json({error:"Prijava nije konfigurirana."},{status:503});
 try{
 const res=await fetch(new URL("/auth/v1/token?grant_type=refresh_token",url),{method:"POST",headers:{"Content-Type":"application/json",apikey:key},body:JSON.stringify({refresh_token:refresh}),cache:"no-store"});
 if(!res.ok){jar.delete("matchlens_access_token");jar.delete("matchlens_refresh_token");return Response.json({error:"Sesija je istekla. Prijavite se ponovno."},{status:401});}
 const data=await res.json() as {access_token?:string;refresh_token?:string;expires_in?:number};
 if(!data.access_token||!data.refresh_token)return Response.json({error:"Obnova sesije nije uspjela."},{status:502});
 const verified=await fetch(new URL("/auth/v1/user",url),{headers:{apikey:key,Authorization:"Bearer "+data.access_token},cache:"no-store"});
 if(!verified.ok)return Response.json({error:"Nije moguće potvrditi korisnika."},{status:401});
 const identity=await verified.json() as {id?:string};
 const owner=process.env.MATCHLENS_ALLOWED_USER_ID;
 if(!owner)return Response.json({error:"Privatni vlasnik nije konfiguriran."},{status:503});
 if(identity.id!==owner)return Response.json({error:"Pristup nije dopušten."},{status:403});
 jar.set("matchlens_access_token",data.access_token,{httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"lax",path:"/",maxAge:Math.min(Math.max(data.expires_in||3600,60),3600)});
 jar.set("matchlens_refresh_token",data.refresh_token,{httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"lax",path:"/api/session",maxAge:60*60*24*30});
 return Response.json({ok:true},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"Obnova sesije trenutačno nije dostupna."},{status:503});}
}
