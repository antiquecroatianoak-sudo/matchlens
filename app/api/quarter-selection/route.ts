import {getChatGPTUser} from '../../chatgpt-auth';
import {getDb} from '../../../db';
import {records} from '../../../db/schema';
import {and,eq} from 'drizzle-orm';
import {createRoundQuarter,type RoundSchedule} from '../../prediction-ranking';
import active from '../../active-strategy.json';
import policy from '../../quarter-policy.json';
export const dynamic='force-dynamic';

export async function GET(){
 const user=await getChatGPTUser();if(!user)return Response.json({error:'Potrebna je prijava.'},{status:401});
 try{const rows=await getDb().select().from(records).where(and(eq(records.owner,user.userId),eq(records.kind,'quarter_selection')));
 return Response.json(rows.map(r=>({id:r.id,...JSON.parse(r.payload)})),{headers:{'Cache-Control':'no-store'}});
 }catch{return Response.json({error:'Odabir trenutačno nije dostupan.'},{status:503});}
}

export async function POST(req:Request){
 const user=await getChatGPTUser();if(!user)return Response.json({error:'Potrebna je prijava.'},{status:401});
 if(req.headers.get('origin')&&req.headers.get('origin')!==new URL(req.url).origin)return Response.json({error:'Neispravan izvor.'},{status:403});
 if(!active.live_recommendations_enabled)return Response.json({captured:0,status:'awaiting_validated_predictions'});
 try{
  const db=getDb();const now=Date.now();
  const [schedules,predictions]=await Promise.all([
   db.select().from(records).where(and(eq(records.owner,user.userId),eq(records.kind,'round_schedule'))),
   db.select().from(records).where(and(eq(records.owner,user.userId),eq(records.kind,'prediction')))]);
  const pool=predictions.map(r=>({...JSON.parse(r.payload),id:r.id,kind:r.kind}));let captured=0;
  for(const raw of schedules){
   const schedule=JSON.parse(raw.payload) as RoundSchedule&{status?:string};
   if(schedule.status!=='verified')continue;
   const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify([user.userId,schedule.league,schedule.season,schedule.round])));
   const id='quarter-'+Array.from(new Uint8Array(digest)).map(b=>b.toString(16).padStart(2,'0')).join('');
   const old=await db.select().from(records).where(and(eq(records.id,id),eq(records.owner,user.userId)));
   if(old.length)continue; // Immutable, including after a model/version switch.
   let snapshot;try{snapshot=createRoundQuarter(pool,schedule,active.id,now,policy.weight);}catch{continue;}
   if(snapshot.eligibleFixtures<snapshot.budget||!snapshot.selected.length)continue;
   await db.insert(records).values({id,owner:user.userId,kind:'quarter_selection',payload:JSON.stringify(snapshot),createdAt:new Date(now).toISOString()}).onConflictDoNothing();captured++;
  }
  return Response.json({captured},{headers:{'Cache-Control':'no-store'}});
 }catch{return Response.json({error:'Odabir nije moguće zamrznuti.'},{status:503});}
}
