import {cookies} from "next/headers";
import {getChatGPTUser} from "../../chatgpt-auth";
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
 const data=await res.json() as {access_token?:string;expires_in?:number};
 if(!data.access_token)return Response.json({error:"Prijava nije uspjela."},{status:502});
 const jar=await cookies();jar.set("matchlens_access_token",data.access_token,{httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"lax",path:"/",maxAge:Math.min(Math.max(data.expires_in||3600,60),3600)});
 return Response.json({ok:true},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"Usluga prijave nije dostupna."},{status:503});}
}
export async function DELETE(req:Request){
 const origin=req.headers.get("origin");if(origin&&origin!==new URL(req.url).origin)return Response.json({error:"Neispravan izvor."},{status:403});
 const jar=await cookies();jar.delete("matchlens_access_token");return Response.json({ok:true},{headers:{"Cache-Control":"no-store"}});
}
