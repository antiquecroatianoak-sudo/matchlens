import { getChatGPTUser } from "../../chatgpt-auth";
import { getDb } from "../../../db";
import { records } from "../../../db/schema";
import { and, eq, desc } from "drizzle-orm";
export const dynamic = "force-dynamic";
const kinds = ["match","source","note","trial"];
export async function GET() {
 const user = await getChatGPTUser(); if(!user) return Response.json({error:"Potrebna je prijava."},{status:401});
 try { const rows = await getDb().select().from(records).where(eq(records.owner,user.userId)).orderBy(desc(records.createdAt)).limit(5000); return Response.json(rows.map(r=>({id:r.id,kind:r.kind,...JSON.parse(r.payload),createdAt:r.createdAt})),{headers:{"Cache-Control":"no-store"}}); } catch { return Response.json({error:"Podaci se trenutačno ne mogu učitati."},{status:503}); }
}
export async function POST(req: Request) {
 const user = await getChatGPTUser(); if(!user) return Response.json({error:"Potrebna je prijava."},{status:401});
 if(req.headers.get("origin") && req.headers.get("origin")!==new URL(req.url).origin) return Response.json({error:"Neispravan izvor zahtjeva."},{status:403});
 try { const raw = await req.text(); if(raw.length>500000) return Response.json({error:"Datoteka je prevelika."},{status:400});
 const b=JSON.parse(raw); const list=Array.isArray(b)?b:[b]; if(!list.length||list.length>200) throw Error();
 const rows=list.map(item=>{const {kind,id,createdAt,...data}=item; if(!kinds.includes(kind)||typeof data.title!=="string"||!data.title.trim()||data.title.length>200||JSON.stringify(data).length>20000) throw Error();
 if(kind==="source" && data.url) {const u=new URL(data.url);if(!["https:","http:"].includes(u.protocol))throw Error();}
 if(kind==="trial" && (!(Number(data.odds)>1)||!(Number(data.prob)>=0&&Number(data.prob)<=100)||!["pending","win","loss","void"].includes(data.result)||!data.market))throw Error();
 return {id:crypto.randomUUID(),owner:user.userId,kind,payload:JSON.stringify(data),createdAt:new Date().toISOString()};});
 const db=getDb(); const [first,...rest]=rows; await db.batch([db.insert(records).values(first),...rest.map(r=>db.insert(records).values(r))]); return Response.json({ok:true,count:rows.length});
 }catch {return Response.json({error:"Provjerite podatke. Najviše 200 zapisa po uvozu."},{status:400});}
}
export async function DELETE(req:Request) {
 const user=await getChatGPTUser();if(!user)return Response.json({error:"Potrebna je prijava."},{status:401});
 if(req.headers.get("origin") && req.headers.get("origin")!==new URL(req.url).origin)return Response.json({error:"Neispravan izvor zahtjeva."},{status:403});
 const id=new URL(req.url).searchParams.get("id");if(!id)return Response.json({error:"Nedostaje zapis."},{status:400});
 await getDb().delete(records).where(and(eq(records.owner,user.userId),eq(records.id,id)));return Response.json({ok:true});
}
export async function PATCH(req:Request){
 const user=await getChatGPTUser();if(!user)return Response.json({error:"Potrebna je prijava."},{status:401});
 if(req.headers.get("origin") && req.headers.get("origin")!==new URL(req.url).origin)return Response.json({error:"Neispravan izvor zahtjeva."},{status:403});
 try{const {id,result}=await req.json() as {id:string;result:string};if(!["pending","win","loss","void"].includes(result))throw Error(); const db=getDb(); const row=(await db.select().from(records).where(and(eq(records.owner,user.userId),eq(records.id,id))))[0];if(!row||row.kind!=="trial")throw Error(); const data=JSON.parse(row.payload);data.result=result;await db.update(records).set({payload:JSON.stringify(data)}).where(and(eq(records.owner,user.userId),eq(records.id,id)));return Response.json({ok:true});}catch{return Response.json({error:"Ishod nije spremljen."},{status:400});}
}
