"use client";
import {useEffect,useState} from "react";
export default function Callback(){
 const [message,setMessage]=useState("Potvrđujem Google prijavu…");
 useEffect(()=>{(async()=>{
  try{
   const hash=new URLSearchParams(location.hash.slice(1));
   const access_token=hash.get("access_token"),refresh_token=hash.get("refresh_token");
   history.replaceState(null,"",location.pathname);
   if(!access_token||!refresh_token)throw Error("Google prijava nije uspjela. Provjerite postavke Google prijave.");
   const res=await fetch("/api/auth/google/session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({access_token,refresh_token})});
   if(!res.ok){const d=await res.json();throw Error(d.error||"Pristup nije dopušten.");}
   location.replace("/");
  }catch(e){setMessage(e instanceof Error?e.message:"Prijava nije uspjela.");}
 })()},[]);
 return <main style={{maxWidth:450,margin:"15vh auto",padding:24,fontFamily:"system-ui"}}><h1>MatchLens</h1><p role="status">{message}</p><a href="/">Natrag na prijavu</a></main>
}