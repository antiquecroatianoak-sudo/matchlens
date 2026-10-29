// Only upcoming, calibrated model outputs qualify. Manual trials stay separate.
export function calculateSyntheticOdds(a:number,b:number):number|null{
 return Number.isFinite(a)&&Number.isFinite(b)&&a>1&&b>1?1/(1/a+1/b):null;
}
export function syntheticQuoteValid(row:{[key:string]:any}):boolean{
 if(row.oddsBasis===undefined||row.oddsBasis==='quoted')return true;
 if(row.oddsBasis!=='synthetic_1x2')return false;
 const legs=row.selection==='1X'?['1','X']:row.selection==='X2'?['X','2']:null;
 if(!legs||!row.underlyingOdds)return false;
 const a=row.underlyingOdds[legs[0]],b=row.underlyingOdds[legs[1]];
 const expected=calculateSyntheticOdds(a,b);
 return expected!==null&&typeof row.odds==='number'&&Math.abs(expected-row.odds)<=1e-10*Math.max(1,expected)&&typeof row.underlyingSnapshotId==='string'&&!!row.underlyingSnapshotId.trim()&&typeof row.underlyingBookmaker==='string'&&!!row.underlyingBookmaker.trim();
}
export function doubleChanceAllowed(row:{[key:string]:any},requireQuote=true):boolean{
 const symbol=typeof row.selection==='string'?row.selection.replace(/\s/g,'').toUpperCase():'';
 const isDouble=row.market==='Dvostruka šansa'||symbol==='1X'||symbol==='X2';
 if(!isDouble)return true;
 if(row.market!=='Dvostruka šansa'||!['1X','X2'].includes(row.selection))return false;
 if(!syntheticQuoteValid(row))return false;
 const odds=typeof row.odds==='number'||typeof row.odds==='string'?Number(row.odds):NaN;
 if(!Number.isFinite(odds)||odds<2)return false;
 if(!requireQuote)return true; // Manual diary has no verified status.
 const quoted=Date.parse(row.oddsTimestamp),generated=Date.parse(row.generatedAt);
 return typeof row.odds==='number'&&row.oddsMatchId===row.matchId&&row.oddsMarket===row.market&&row.oddsSelection===row.selection&&typeof row.oddsSource==='string'&&!!row.oddsSource.trim()&&typeof row.oddsTimestamp==='string'&&/(Z|[+-]\d{2}:\d{2})$/.test(row.oddsTimestamp)&&Number.isFinite(quoted)&&Number.isFinite(generated)&&quoted<=generated;
}
export function rankPredictions<T extends {id:string;kind:string;[key:string]:any}>(rows:T[],options:{minOdds?:number;now?:number;modelVersion?:string}={}):T[]{
 const now=options.now??Date.now();
 const valid=rows.filter(r=>{
  if(options.modelVersion&&r.modelVersion!==options.modelVersion)return false;
  if(!doubleChanceAllowed(r))return false;
  const generated=Date.parse(r.generatedAt),kickoff=Date.parse(r.kickoff),until=Date.parse(r.validUntil),validated=Date.parse(r.validatedAt);
  return r.kind==='prediction'&&r.status==='verified'&&r.calibrated===true&&typeof r.prob==='number'&&Number.isFinite(r.prob)&&r.prob>=0&&r.prob<=100&&typeof r.modelVersion==='string'&&r.modelVersion.trim()&&typeof r.validationId==='string'&&r.validationId.trim()&&r.market&&r.selection&&r.matchId&&Number.isFinite(validated)&&validated<=generated&&generated<=now&&now<kickoff&&now<until&&generated<kickoff&&(!options.minOdds||(typeof r.odds==='number'&&Number.isFinite(r.odds)&&r.odds>=options.minOdds));
 }).sort((a,b)=>b.prob-a.prob||Date.parse(b.generatedAt)-Date.parse(a.generatedAt)||a.id.localeCompare(b.id));
 const seen=new Set<string>();return valid.filter(r=>{const key=JSON.stringify([r.matchId,r.market,r.selection]);if(seen.has(key))return false;seen.add(key);return true;});
}

export type RoundSchedule={league:string;season:string;round:string;source:string;publishedAt:string;fixtures:{matchId:string;kickoff:string}[]};
export function createRoundQuarter<T extends {id:string;kind:string;[key:string]:any}>(rows:T[],schedule:RoundSchedule,modelVersion:string,now:number,weight=0){
 const published=Date.parse(schedule.publishedAt);
 if(!schedule.league||!schedule.season||!schedule.round||!schedule.source||!Number.isFinite(published)||published>now||!/(Z|[+-]\d{2}:\d{2})$/.test(schedule.publishedAt))throw Error('Invalid pre-round schedule');
 const fixtures=schedule.fixtures,ids=fixtures.map(f=>f.matchId),kickoffs=fixtures.map(f=>Date.parse(f.kickoff));
 if(!fixtures.length||ids.some(id=>!id)||new Set(ids).size!==ids.length||fixtures.some(f=>!/(Z|[+-]\d{2}:\d{2})$/.test(f.kickoff))||kickoffs.some(t=>!Number.isFinite(t))||now>=Math.min(...kickoffs))throw Error('Round must be frozen before its first kickoff');
 const ranked=rankPredictions(rows,{now,modelVersion}).filter(r=>ids.includes(r.matchId)&&Date.parse(r.kickoff)===kickoffs[ids.indexOf(r.matchId)]);
 const seen=new Set<string>();const primary=ranked.filter(r=>{if(seen.has(r.matchId))return false;seen.add(r.matchId);return true;});
 function margin(r:T):number|null{
  if(typeof r.selectionMargin==='number'&&Number.isFinite(r.selectionMargin)&&r.selectionMargin>=0&&r.selectionMargin<=1)return r.selectionMargin;
  if(r.market==='Dvostruka šansa')return Math.abs(2*r.prob/100-1);
  const family=ranked.filter(v=>v.matchId===r.matchId&&v.market===r.market).map(v=>Number(v.prob)).sort((a,b)=>b-a);
  const count=r.market==='1X2'?3:r.market==='Golovi'?2:0;
  return count&&family.length===count?(family[0]-family[1])/100:null;
 }
 const scored=primary.map(r=>({r,margin:margin(r)})).filter(v=>weight===0||v.margin!==null);
 scored.sort((a,b)=>-(a.r.prob/100+weight*(a.margin??0))+(b.r.prob/100+weight*(b.margin??0))||a.r.matchId.localeCompare(b.r.matchId));
 const budget=Math.floor(fixtures.length/4);
 return {league:schedule.league,season:schedule.season,round:schedule.round,source:schedule.source,
  schedulePublishedAt:schedule.publishedAt,frozenAt:new Date(now).toISOString(),firstKickoff:new Date(Math.min(...kickoffs)).toISOString(),
  modelVersion,ratio:.25,weight,totalRoundFixtures:fixtures.length,eligibleFixtures:scored.length,budget,
  selected:scored.slice(0,budget).map(v=>({...v.r,selectionMargin:v.margin})),policy:'round-quarter-v1'};
}
