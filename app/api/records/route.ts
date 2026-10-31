import {getChatGPTUser} from "../../chatgpt-auth";
export const dynamic="force-dynamic";
const kinds=["match","source","note","trial"];
async function context(){
 const user=await getChatGPTUser();if(!user)return null;
 const owner=process.env.MATCHLENS_ALLOWED_USER_ID;
 if(!owner||user.userId!==owner)return {error:Response.json({error:owner?"Pristup nije dopušten.":"Privatni vlasnik nije konfiguriran."},{status:owner?403:503})};
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL,key=process.env.SUPABASE_SERVICE_ROLE_KEY;
 if(!url||!key)return {error:Response.json({error:"Supabase nije konfiguriran."},{status:503})};
 return {user,url,key};
}
const headers=(key:string)=>({apikey:key,Authorization:"Bearer "+key,"Content-Type":"application/json"});
function sameOrigin(req:Request){const origin=req.headers.get("origin");return !origin||origin===new URL(req.url).origin;}
function endpoint(url:string,params:Record<string,string>){const u=new URL("/rest/v1/matchlens_records",url);Object.entries(params).forEach(([k,v])=>u.searchParams.set(k,v));return u;}
export async function GET(){
 const c=await context();if(!c)return Response.json({error:"Potrebna je prijava."},{status:401});if("error" in c)return c.error;
 try{const r=await fetch(endpoint(c.url,{select:"id,kind,payload,created_at",owner:"eq."+c.user.userId,order:"created_at.desc",limit:"5000"}),{headers:headers(c.key),cache:"no-store"});if(!r.ok)throw Error();const rows=await r.json() as Array<{id:string;kind:string;payload:Record<string,unknown>;created_at:string}>;return Response.json(rows.map(x=>({id:x.id,kind:x.kind,...x.payload,createdAt:x.created_at})),{headers:{"Cache-Control":"no-store"}});}catch{return Response.json({error:"Zapisi nisu dostupni."},{status:503});}
}
export async function POST(req:Request){
 const c=await context();if(!c)return Response.json({error:"Potrebna je prijava."},{status:401});if("error" in c)return c.error;
 if(!sameOrigin(req))return Response.json({error:"Neispravan izvor."},{status:403});
 try{const raw=await req.text();if(raw.length>500000)throw Error();const data=JSON.parse(raw);const list=Array.isArray(data)?data:[data];if(!list.length||list.length>200)throw Error();
 const rows=list.map(item=>{if(!item||typeof item!=="object")throw Error();const {kind,id,createdAt,...payload}=item;if(!kinds.includes(kind)||typeof payload.title!=="string"||!payload.title.trim()||payload.title.length>200||JSON.stringify(payload).length>20000)throw Error();
 if(kind==="source"&&payload.url){const u=new URL(payload.url);if(!["https:","http:"].includes(u.protocol))throw Error();}
 if(kind==="trial"&&(!(Number(payload.odds)>1)||!(Number(payload.prob)>=0&&Number(payload.prob)<=100)||!["pending","win","loss","void"].includes(payload.result)||!payload.market))throw Error();
 return {id:crypto.randomUUID(),owner:c.user.userId,kind,payload};});
 const r=await fetch(endpoint(c.url,{}),{method:"POST",headers:{...headers(c.key),Prefer:"return=minimal"},body:JSON.stringify(rows),cache:"no-store"});if(!r.ok)throw Error();return Response.json({ok:true,count:rows.length});}catch{return Response.json({error:"Provjerite podatke ili dostupnost baze."},{status:400});}
}
export async function DELETE(req:Request){
 const c=await context();if(!c)return Response.json({error:"Potrebna je prijava."},{status:401});if("error" in c)return c.error;if(!sameOrigin(req))return Response.json({error:"Neispravan izvor."},{status:403});
 const id=new URL(req.url).searchParams.get("id");if(!id||!/^[0-9a-f-]{36}$/i.test(id))return Response.json({error:"Neispravan zapis."},{status:400});
 try{const r=await fetch(endpoint(c.url,{id:"eq."+id,owner:"eq."+c.user.userId}),{method:"DELETE",headers:headers(c.key),cache:"no-store"});if(!r.ok)throw Error();return Response.json({ok:true});}catch{return Response.json({error:"Brisanje nije uspjelo."},{status:503});}
}
export async function PATCH(req:Request){
 const c=await context();if(!c)return Response.json({error:"Potrebna je prijava."},{status:401});if("error" in c)return c.error;if(!sameOrigin(req))return Response.json({error:"Neispravan izvor."},{status:403});
 try{const {id,result}=await req.json() as {id:string;result:string};if(!/^[0-9a-f-]{36}$/i.test(id)||!["pending","win","loss","void"].includes(result))throw Error();
 const url=endpoint(c.url,{id:"eq."+id,owner:"eq."+c.user.userId,kind:"eq.trial",select:"payload"});const existing=await fetch(url,{headers:headers(c.key),cache:"no-store"});if(!existing.ok)throw Error();const rows=await existing.json() as Array<{payload:Record<string,unknown>}>;if(rows.length!==1)throw Error();
 const updated=await fetch(endpoint(c.url,{id:"eq."+id,owner:"eq."+c.user.userId,kind:"eq.trial"}),{method:"PATCH",headers:headers(c.key),body:JSON.stringify({payload:{...rows[0].payload,result}}),cache:"no-store"});if(!updated.ok)throw Error();return Response.json({ok:true});}catch{return Response.json({error:"Ishod nije spremljen."},{status:400});}
}
