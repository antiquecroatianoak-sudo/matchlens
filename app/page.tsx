import Workspace from "./workspace";
import Login from "./login";
import {getChatGPTUser} from "./chatgpt-auth";
export const dynamic="force-dynamic";
export default async function Page(){
 const user=await getChatGPTUser();
 const ownerId=process.env.MATCHLENS_ALLOWED_USER_ID;
 // A valid Supabase account is not sufficient: MatchLens is owner-only.
 return user&&ownerId&&user.userId===ownerId?<Workspace/>:<Login/>;
}
