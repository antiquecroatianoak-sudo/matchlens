"use client";
import {useEffect,useState} from "react";
export default function Login(){
 const [error,setError]=useState("");
 useEffect(()=>{fetch("/api/session",{method:"PUT"}).then(r=>{if(r.ok)location.reload()}).catch(()=>{})},[]);
 return <main style={{maxWidth:420,margin:"12vh auto",padding:24,fontFamily:"system-ui"}}><h1>MatchLens</h1><p>Privatni pristup aplikaciji.</p><a href="/api/auth/google" style={{display:"block",padding:16,textAlign:"center",border:"1px solid #888",borderRadius:10,fontWeight:700}}>Prijavi se putem Googlea</a><p>Pristup je dopušten samo vlasniku aplikacije.</p>{error&&<p role="alert">{error}</p>}</main>
}