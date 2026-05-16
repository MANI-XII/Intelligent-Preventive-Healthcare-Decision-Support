import { useRouter } from "next/router";
import { useEffect } from "react";
import RequireAuth from "../../components/RequireAuth";

export default function DashboardIndexPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/predict");
  }, [router]);

  return (
    <RequireAuth>
      <div className="p-6 text-sm text-slate-300">Redirecting...</div>
    </RequireAuth>
  );
}
