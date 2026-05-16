import Link from "next/link";
import { useRouter } from "next/router";
import { useAuth } from "../context/AuthContext";

export default function SiteHeader() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="group flex min-w-0 items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-lg shadow-indigo-900/40">
            PH
          </span>
          <span className="min-w-0">
            <span className="block truncate text-base font-semibold text-slate-100 group-hover:text-white">
              Preventive Health
            </span>
            <span className="hidden text-xs text-slate-500 sm:block">Decision support system</span>
          </span>
        </Link>

        <nav className="flex items-center gap-2 sm:gap-3" aria-label="Main">
          {!isLoading && isAuthenticated ? (
            <Link
              href="/dashboard/predict"
              className="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-md shadow-indigo-900/30 transition hover:bg-indigo-400"
            >
              Dashboard
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className={`rounded-lg px-3 py-2 text-sm font-medium transition sm:px-4 ${
                  router.pathname === "/login"
                    ? "bg-slate-800 text-white"
                    : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                }`}
              >
                Login
              </Link>
              <Link
                href="/signup"
                className={`rounded-lg px-3 py-2 text-sm font-medium transition sm:px-4 ${
                  router.pathname === "/signup"
                    ? "bg-indigo-500 text-white"
                    : "bg-indigo-500/90 text-white hover:bg-indigo-400"
                }`}
              >
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
