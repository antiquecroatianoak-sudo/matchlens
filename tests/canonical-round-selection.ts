import {selectRoundRecommendations} from '../app/prediction-ranking';
const now=Date.parse('2026-10-31T10:00:00Z');
const features=Array.from({length:11},(_,i)=>({name:'f'+i,value:i+1,source:'verified',availableAt:'2026-10-30T10:00:00Z'}));
const make=(i:number,odds=1.5)=>({id:'p'+i,kind:'prediction',status:'verified',calibrated:true,prob:80-i,modelVersion:'v1',validationId:'v',market:'1X2',selection:'1',matchId:'m'+i,generatedAt:'2026-10-31T09:00:00Z',validatedAt:'2026-10-30T09:00:00Z',kickoff:'2026-11-01T15:00:00Z',validUntil:'2026-11-01T15:00:00Z',odds,oddsTimestamp:'2026-10-31T08:00:00Z',features});
function assert(ok:boolean,msg:string){if(!ok)throw Error(msg)}
for(const n of [3,4,7,8]){
 const rows=Array.from({length:n},(_,i)=>make(i));
 const ids=rows.map(r=>r.matchId);
 const result=selectRoundRecommendations(rows,ids,{now,completeRound:true});
 assert(result.selected.length===Math.floor(n/4),'round cap '+n);
 assert(selectRoundRecommendations(rows,ids,{now}).selected.length===0,'incomplete round '+n);
}
const base=Array.from({length:8},(_,i)=>make(i));
assert(selectRoundRecommendations([base[0],{...base[0],id:'duplicate',selection:'2'},...base.slice(1)],base.map(r=>r.matchId),{now,completeRound:true}).selected.length===2,'one pick per match');
assert(selectRoundRecommendations([make(0,1.30)],Array.from({length:4},(_,i)=>'m'+i),{now,completeRound:true}).selected.length===0,'strict odds');
assert(selectRoundRecommendations([{...make(0),features:features.slice(0,10)}],Array.from({length:4},(_,i)=>'m'+i),{now,completeRound:true}).selected.length===0,'11 features');
assert(selectRoundRecommendations([{...make(0),oddsTimestamp:'2026-10-31T09:30:00Z'}],Array.from({length:4},(_,i)=>'m'+i),{now,completeRound:true}).selected.length===0,'odds at generation');
console.log('Canonical round selection regressions passed');
