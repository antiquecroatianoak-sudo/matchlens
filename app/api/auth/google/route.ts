export async function GET(req:Request){
 const base=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL;
 if(!base)return new Response("Google prijava nije konfigurirana.",{status:503});
 const callback=new URL("/auth/google/callback",new URL(req.url).origin).toString();
 const url=new URL("/auth/v1/authorize",base);url.searchParams.set("provider","google");url.searchParams.set("redirect_to",callback);
 return Response.redirect(url,303);
}