import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {title:"MatchLens · Nogometna analitika",description:"Istraživanje stilova igre, izvora i uspješnosti nogometnih procjena."};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="hr"><body>{children}</body></html>}
