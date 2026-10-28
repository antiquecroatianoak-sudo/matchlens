// Only upcoming, calibrated model outputs qualify. Manual trials stay separate.
export function rankPredictions<T extends {id:string;kind:string;[key:string]:any}>(rows:T[],options:{minOdds?:number;now?:number}={}):T[]{
 const now=options.now??Date.now();
 const valid=rows.filter(r=>{
  const generated=Date.parse(r.generatedAt),kickoff=Date.parse(r.kickoff),until=Date.parse(r.validUntil),validated=Date.parse(r.validatedAt);
  return r.kind==='prediction'&&r.status==='verified'&&r.calibrated===true&&typeof r.prob==='number'&&Number.isFinite(r.prob)&&r.prob>=0&&r.prob<=100&&typeof r.modelVersion==='string'&&r.modelVersion.trim()&&typeof r.validationId==='string'&&r.validationId.trim()&&r.market&&r.selection&&r.matchId&&Number.isFinite(validated)&&validated<=generated&&generated<=now&&now<kickoff&&now<until&&generated<kickoff&&(!options.minOdds||(typeof r.odds==='number'&&Number.isFinite(r.odds)&&r.odds>=options.minOdds));
 }).sort((a,b)=>b.prob-a.prob||Date.parse(b.generatedAt)-Date.parse(a.generatedAt)||a.id.localeCompare(b.id));
 const seen=new Set<string>();return valid.filter(r=>{const key=JSON.stringify([r.matchId,r.market,r.selection]);if(seen.has(key))return false;seen.add(key);return true;});
}
