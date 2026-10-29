import strategy from './active-strategy.json';
const pct=(v:number)=>(100*v).toLocaleString('hr-HR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%';
export default function ActiveStrategyPanel(){return <section className="panel notes">
 <div className="panel-heading"><h2>Osnovni model za odabir četvrtine</h2><span className="tag">{strategy.id}</span></div>
 <p><strong>{strategy.name}</strong> · {pct(strategy.reference.top_pick_accuracy)} najvjerojatnije ponude u ranijem punom uzorku na {strategy.reference.matches.toLocaleString('hr-HR')} povijesnih susreta: {strategy.reference.hits.toLocaleString('hr-HR')} pogodaka i {strategy.reference.misses.toLocaleString('hr-HR')} promašaja.</p>
 <p>Trenutačno najuspješniji postojeći model na usporedivom punom uzorku. Za 1X2 ponovno učenje po tromjesečjima, za golove po sezoni. Noviji ligaški i kadrovski pokusi te dodatna korekcija nisu pokazali veću usporedivu točnost pa ga nisu zamijenili.</p>
 <p className="muted">Nova strategija preuzima aktivno mjesto kada na istim susretima i uz isti obuhvat ostvari više pogodaka u odvojenoj vremenskoj provjeri, uz barem 200 različitih susreta. Čuvamo prethodnu verziju. Visok postotak na malom ili lakšem odabiru nije zamjena za bolji model cijelog uzorka.</p>
 <p className="small muted">Aktivan je model za povijesnu analizu. Broj {pct(strategy.reference.top_pick_accuracy)} potječe iz već pregledanih sezona, bez jamstva buduće točnosti. Aktualne provjerene prognoze čekaju odgovarajuće ulaze i provjeru; strategija s potvrđenih više od 90% još ne postoji.</p>
 </section>;}
