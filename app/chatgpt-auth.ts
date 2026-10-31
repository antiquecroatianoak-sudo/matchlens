/** Standalone authentication adapter. Never trust an unsigned user identifier. */
export type AuthenticatedUser={userId:string};
export async function getChatGPTUser():Promise<AuthenticatedUser|null>{
 const {cookies}=await import("next/headers");
 const jar=await cookies();
 const token=jar.get("matchlens_access_token")?.value;
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL;
 const anonKey=process.env.SUPABASE_ANON_KEY;
 if(!token||!url||!anonKey)return null;
 try{
  const response=await fetch(new URL("/auth/v1/user",url),{
   headers:{apikey:anonKey,Authorization:"Bearer "+token},
   cache:"no-store",signal:AbortSignal.timeout(8000)
  });
  if(!response.ok)return null;
  const user=await response.json() as {id?:unknown};
  return typeof user.id==="string"&&user.id.length>0?{userId:user.id}:null;
 }catch{return null;}
}
