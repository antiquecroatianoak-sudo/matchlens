"use client";
import {useEffect,useState} from "react";
export default function Login(){
 useEffect(()=>{fetch("/api/session",{method:"PUT"}).then(r=>{if(r.ok)window.location.reload();}).catch(()=>{});},[]);
 const [email,setEmail]=useState(""),[password,setPassword]=useState(""),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError("");
 try{const r=await fetch("/api/session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});const d=await r.json();if(!r.ok)throw Error(d.error||"Prijava nije uspjela.");window.location.reload();}
 catch(e){setError(e instanceof Error?e.message:"Prijava nije uspjela.");}finally{setBusy(false);}}
 return <main style={{maxWidth:420,width:"100%",boxSizing:"border-box",margin:"min(12vh,72px) auto",padding:"24px 20px",fontFamily:"system-ui"}}><h1>MatchLens</h1><p>Prijavite se za pristup privatnoj analizi utakmica.</p><form onSubmit={submit}><label>E-mail<input type="email" required autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} style={{display:"block",width:"100%",boxSizing:"border-box",minHeight:48,fontSize:16,padding:12,margin:"8px 0 16px"}}/></label><label>Lozinka<input type="password" required autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} style={{display:"block",width:"100%",padding:12,margin:"8px 0 16px"}}/></label><button type="submit" disabled={busy} style={{padding:12,width:"100%",minHeight:48,fontSize:16}}>{busy?"Prijava...":"Prijavi se"}</button>{error&&<p role="alert">{error}</p>}</form></main>;
}
