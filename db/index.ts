import {createClient} from "@libsql/client";
import {drizzle} from "drizzle-orm/libsql";
export function getDb(){
 const url=process.env.MATCHLENS_RECORDS_DATABASE_URL;
 const authToken=process.env.MATCHLENS_RECORDS_DATABASE_TOKEN;
 if(!url)throw Error("Private records database is not configured");
 return drizzle(createClient({url,authToken}));
}
