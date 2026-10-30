/** Validate generated model output before any immutable prediction write. */
export type ForecastCandidate={matchId:string;market:string;selection:string;prob:number;modelVersion:string;validationId:string;validatedAt:string;generatedAt:string;kickoff:string;validUntil:string;calibrated:boolean;status:string;odds?:number};
export function validatePrematchForecast(p:ForecastCandidate,now:string):string[]{
 const errors:string[]=[];
 for(const field of ['matchId','market','selection','modelVersion','validationId'] as const){if(typeof p[field]!=='string'||!p[field].trim())errors.push(field+' missing');}
 if(p.status!=='verified'||p.calibrated!==true)errors.push('not validated');
 if(typeof p.prob!=='number'||!Number.isFinite(p.prob)||p.prob<0||p.prob>100)errors.push('invalid probability');
 if(p.odds!==undefined&&(typeof p.odds!=='number'||!Number.isFinite(p.odds)||p.odds<=1))errors.push('invalid odds');
 const times=[p.validatedAt,p.generatedAt,p.kickoff,p.validUntil,now].map(x=>typeof x==='string'?Date.parse(x):NaN);
 if(times.some(x=>!Number.isFinite(x)))errors.push('invalid timestamp');
 else {const [validated,generated,kickoff,until,current]=times;
  if(!(validated<=generated&&generated<=current&&current<kickoff&&current<until&&generated<kickoff))errors.push('forecast not pre-kickoff or expired');
 }
 if(!['1X2','OU2.5'].includes(p.market))errors.push('unsupported market');
 if(p.market==='1X2'&&!['1','X','2'].includes(p.selection))errors.push('unsupported selection');
 if(p.market==='OU2.5'&&!['over','under'].includes(p.selection))errors.push('unsupported selection');
 return errors;
}
