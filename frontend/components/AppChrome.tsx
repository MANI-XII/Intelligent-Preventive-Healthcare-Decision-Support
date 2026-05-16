import type { ReactNode } from "react";
import { useRouter } from "next/router";
import SiteFooter from "./SiteFooter";
import SiteHeader from "./SiteHeader";

export default function AppChrome({ children }: { children: ReactNode }) {
  const router = useRouter();
  const isDashboard = router.pathname.startsWith("/dashboard");

  if (isDashboard) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-950">
      <SiteHeader />
      <main className="flex flex-1 flex-col">{children}</main>
      <SiteFooter />
    </div>
  );
}
