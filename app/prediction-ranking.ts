// Only upcoming, calibrated model outputs qualify. Manual trials stay separate.
export function rankPredictions<T extends {id:string;kind:string;[key:string]:any}>(rows:T[],options:{minOdds?:number;now?:number}={}):T[]{
 const now=options.now??Date.now();
 const valid=rows.filter(r=>{
  const generated=Date.parse(r.generatedAt),kickoff=Date.parse(r.kickoff),until=Date.parse(r.validUntil),validated=Date.parse(r.validatedAt);
  return r.kind==='prediction'&&r.status==='verified'&&r.calibrated===true&&typeof r.prob==='number'&&Number.isFinite(r.prob)&&r.prob>=0&&r.prob<=100&&typeof r.modelVersion==='string'&&r.modelVersion.trim()&&typeof r.validationId==='string'&&r.validationId.trim()&&r.market&&r.selection&&r.matchId&&Number.isFinite(validated)&&validated<=generated&&generated<=now&&now<kickoff&&now<until&&generated<kickoff&&(!options.minOdds||(typeof r.odds==='number'&&Number.isFinite(r.odds)&&r.odds>=options.minOdds));
 }).sort((a,b)=>b.prob-a.prob||Date.parse(b.generatedAt)-Date.parse(a.generatedAt)||a.id.localeCompare(b.id));
 const seen=new Set<string>();return valid.filter(r=>{const key=JSON.stringify([r.matchId,r.market,r.selection]);if(seen.has(key))return false;seen.add(key);return true;});
}


// Canonical round selection. A round must include the complete verified fixture list;
// an incomplete fixture denominator must never produce official recommendations.
export function selectRoundRecommendations<T extends {id:string;kind:string;[key:string]:any}>(
 rows:T[], fixtureIds:string[], options:{now?:number;completeRound?:boolean}={}
):{selected:T[];rejected:{id:string;reason:string}[];limit:number;fixtures:number}{
 const uniqueFixtures=new Set(fixtureIds.filter(x=>typeof x==='string'&&x.trim()));
 // The caller must attest that the full round was retrieved and verified.
 if(options.completeRound!==true)return {selected:[],rejected:rows.map(r=>({id:r.id,reason:'Nepotpun ili nepotvrđen popis kola'})),limit:0,fixtures:uniqueFixtures.size};
 const limit=Math.floor(uniqueFixtures.size*0.25);
 const ranked=rankPredictions(rows,{now:options.now});
 const rejected:{id:string;reason:string}[]=[];
 const eligible:T[]=[];
 for(const row of ranked){
  if(!uniqueFixtures.has(row.matchId)){rejected.push({id:row.id,reason:'Utakmica nije u potvrđenom popisu kola'});continue;}
  const pick=String(row.selection).toUpperCase().replace(/\s/g,'');
  const doubleChance=pick==='1X'||pick==='X2';
  const market=String(row.market).toUpperCase().replace(/\s/g,'');
  const validMarket=doubleChance?['DC','DOUBLECHANCE','1X2'].includes(market):['1','X','2'].includes(pick)?['1X2','MATCHRESULT'].includes(market):['OU2.5','OVERUNDER2.5','TOTAL2.5'].includes(market);
  if(!validMarket){rejected.push({id:row.id,reason:'Tržište i odabrani tip nisu usklađeni'});continue;}
  if(!doubleChance&&!['1','X','2','OVER2.5','UNDER2.5','VIŠE2.5','MANJE2.5'].includes(pick)){
   rejected.push({id:row.id,reason:'Tip nije među dopuštenim tržištima'});continue;
  }
  if(doubleChance){
   const p1=row.p1,px=row.px,p2=row.p2;
   if(![p1,px,p2].every(p=>typeof p==='number'&&Number.isFinite(p)&&p>=0&&p<=1)||Math.abs(p1+px+p2-1)>0.01){
    rejected.push({id:row.id,reason:'Nedostaju provjerene vjerojatnosti 1/X/2'});continue;
   }
   const denominator=pick==='1X'?p1+px:px+p2;
   if(Math.abs(row.prob-denominator*100)>0.1){rejected.push({id:row.id,reason:'Vjerojatnost tipa nije usklađena s 1/X/2'});continue;}
   if(denominator<=0||1/denominator<=2){
    rejected.push({id:row.id,reason:'Sintetička kvota nije strogo iznad 2,00'});continue;
   }
  }else if(!(typeof row.odds==='number'&&Number.isFinite(row.odds)&&row.odds>1.30&&
   typeof row.oddsTimestamp==='string'&&Number.isFinite(Date.parse(row.oddsTimestamp))&&
   Date.parse(row.oddsTimestamp)<Date.parse(row.kickoff)&&Date.parse(row.oddsTimestamp)<=Date.parse(row.generatedAt))){
   rejected.push({id:row.id,reason:'Nema stvarne datirane kvote strogo iznad 1,30'});continue;
  }
  if(!Array.isArray(row.features)||new Set(row.features.filter((f:any)=>f&&f.value!==null&&f.value!==undefined&&
   typeof f.source==='string'&&f.source.trim()&&typeof f.availableAt==='string'&&
   Number.isFinite(Date.parse(f.availableAt))&&Date.parse(f.availableAt)<=Date.parse(row.generatedAt))
   .map((f:any)=>f.name).filter(Boolean)).size<11){
   rejected.push({id:row.id,reason:'Manje od 11 potvrđenih prematch obilježja'});continue;
  }
  eligible.push(row);
 }
 const selected:T[]=[];const seen=new Set<string>();
 for(const row of eligible){
  if(seen.has(row.matchId)){rejected.push({id:row.id,reason:'Već odabran tip za utakmicu'});continue;}
  if(selected.length>=limit){rejected.push({id:row.id,reason:'Dosegnuto 25% utakmica kola'});continue;}
  selected.push(row);seen.add(row.matchId);
 }
 return {selected,rejected,limit,fixtures:uniqueFixtures.size};
}
