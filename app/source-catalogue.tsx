import catalogue from './source-catalogue.json';
export default function SourceCatalogue({query}:{query:string}){
 const selected=catalogue.sources.filter(s=>JSON.stringify(s).toLowerCase().includes(query.toLowerCase()));
 return <section className="panel notes">
  <div className="panel-heading"><h2>Izvori za razvoj algoritma</h2><span className="tag">{catalogue.sources.length} IZVORA · 29.10.2026.</span></div>
  <p>Provjerene poveznice i ograničenja pristupa. Novi izvori su kandidati za proširenje podataka; postojeći povijesni model koristi OpenFootball. Više izvora samo po sebi ne jamči veću točnost.</p>
  <div className="records-grid">{selected.map(s=><article className="panel notes" key={s.id}>
   <div className="panel-heading"><h3><a href={s.url} target="_blank" rel="noopener noreferrer">{s.name} ↗</a></h3></div>
   <p><strong>{s.category}</strong></p><p className="tag">{s.status}</p>
   <p>{s.purpose}</p><p><strong>Pokrivenost: </strong>{s.coverage}</p>
   <details><summary>Pristup, uvjeti i povijesna provjera</summary><p>{s.access}</p><p>{s.timing}</p><ul>{s.evidence.map((url,i)=><li key={url}><a href={url} target="_blank" rel="noopener noreferrer">Službeni izvor {i+1} ↗</a></li>)}</ul></details>
   <p className="small muted">{s.active?'Povezan s postojećim povijesnim eksperimentima.':'Automatski uvoz nije povezan. Podaci nisu uključeni u treniranje.'}</p>
  </article>)}</div>
  {!selected.length&&<p>Nema izvora za zadani pojam.</p>}
  <p className="small muted">Za svaki novi podatak treba sačuvati izvor, vrijeme objave i dohvata te dokaz da je bio dostupan prije prognoze. Današnje stanje ozljeda, sezonski zbrojevi i postave ciljanog susreta ne smiju retroaktivno ulaziti u ranije prognoze.</p>
 </section>;
}
