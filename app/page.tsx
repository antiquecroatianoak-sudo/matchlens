import Workspace from "./workspace";
import Login from "./login";
import {getChatGPTUser} from "./chatgpt-auth";
export const dynamic="force-dynamic";
export default async function Page(){
 const user=await getChatGPTUser();
 return user?<Workspace/>:<Login/>;
}
