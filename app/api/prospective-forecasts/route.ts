export const dynamic="force-dynamic";

type Forecast={fixture_id:string;model_version:string;predicted_at_utc:string;kickoff_utc:string;league:string;home_team:string;away_team:string;probabilities:Record<string,number>;predicted_outcome:string;confidence:number;top25:boolean;actual_outcome:string|null;score_home:number|null;score_away:number|null};

export async function GET(){
 const url=process.env.SUPABASE_URL||process.env.NEXT_PUBLIC_SUPABASE_URL;
 const key=process.env.SUPABASE_PUBLISHABLE_KEY;
 if(!url||!key)return Response.json({error:"Supabase veza nije konfigurirana."},{status:503});
 try{
  const fields="fixture_id,model_version,predicted_at_utc,kickoff_utc,league,home_team,away_team,probabilities,predicted_outcome,confidence,top25,actual_outcome,score_home,score_away";
  // Supabase/PostgREST responses are page-limited. Retrieve every page rather than silently dropping forecasts.
  const rows:Forecast[]=[];
  const pageSize=1000;
  for(let offset=0;;offset+=pageSize){
   const query=new URLSearchParams({select:fields,order:"kickoff_utc.asc,fixture_id.asc",limit:String(pageSize),offset:String(offset)});
   const res=await fetch(url+"/rest/v1/prospective_predictions?"+query.toString(),{
    headers:{apikey:key,Authorization:"Bearer "+key},cache:"no-store"});
   if(!res.ok)throw Error("Forecast query failed");
   const page=await res.json() as Forecast[];
   if(!Array.isArray(page))throw Error("Invalid forecast response");
   rows.push(...page);
   if(page.length<pageSize)break;
  }
  const safeRows=rows.filter(row=>row&&typeof row.fixture_id==='string'&&typeof row.kickoff_utc==='string'&&typeof row.predicted_at_utc==='string'&&Date.parse(row.predicted_at_utc)<=Date.parse(row.kickoff_utc)-60*60*1000);
  const liveScores:Record<string,{home:number;away:number;finished:boolean}>={};
  const fixtureIds=[...new Set(safeRows.map(row=>row.fixture_id).filter(id=>/^openligadb:[0-9]+$/.test(id)))].slice(0,35);
  await Promise.all(fixtureIds.map(async fixtureId=>{
    try{
      const id=fixtureId.split(':')[1];
      const response=await fetch('https://api.openligadb.de/getmatchdata/'+id,{next:{revalidate:60}});
      if(!response.ok)return;
      const match=await response.json();
      const scores=Array.isArray(match.matchResults)?match.matchResults:[];
      const final=scores.find((item:{resultTypeID:number})=>item.resultTypeID===2);
      const interim=scores.find((item:{resultTypeID:number})=>item.resultTypeID===1);
      const score=match.matchIsFinished?final:(interim||final);
      if(score&&Number.isInteger(score.pointsTeam1)&&Number.isInteger(score.pointsTeam2))liveScores[fixtureId]={home:score.pointsTeam1,away:score.pointsTeam2,finished:match.matchIsFinished===true};
    }catch{}
  }));
  return Response.json({forecasts:safeRows.map(row=>({...row,live_score:liveScores[row.fixture_id]||null}))},{headers:{"Cache-Control":"private, no-store"}});
 }catch{return Response.json({error:"Spremljene prognoze trenutačno nisu dostupne."},{status:503});}
}
