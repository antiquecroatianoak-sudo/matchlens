"use client";
import {useState} from "react";
export default function Login(){
 const [email,setEmail]=useState(""),[password,setPassword]=useState(""),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError("");
 try{const r=await fetch("/api/session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});const d=await r.json();if(!r.ok)throw Error(d.error||"Prijava nije uspjela.");window.location.reload();}
 catch(e){setError(e instanceof Error?e.message:"Prijava nije uspjela.");}finally{setBusy(false);}}
 return <main style={{maxWidth:420,margin:"12vh auto",padding:24,fontFamily:"system-ui"}}><h1>MatchLens</h1><p>Prijavite se za pristup privatnoj analizi utakmica.</p><form onSubmit={submit}><label>E-mail<input type="email" required autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} style={{display:"block",width:"100%",padding:12,margin:"8px 0 16px"}}/></label><label>Lozinka<input type="password" required autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} style={{display:"block",width:"100%",padding:12,margin:"8px 0 16px"}}/></label><button type="submit" disabled={busy} style={{padding:12,width:"100%"}}>{busy?"Prijava...":"Prijavi se"}</button>{error&&<p role="alert">{error}</p>}</form></main>;
}
