import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function SignupPage() {
  const router = useRouter();
  const { signup, isAuthenticated, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard/predict");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="flex flex-1 flex-col justify-center px-4 py-14">
      <div className="mx-auto flex w-full max-w-md items-center">
        <div className="w-full rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-100">Create account</h1>
          <p className="mt-1 text-sm text-slate-300">Sign up to use your personalized health workspace.</p>

          {error ? (
            <div className="mt-4 rounded border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
              {error}
            </div>
          ) : null}

          <form
            className="mt-5 space-y-4"
            onSubmit={async (e) => {
              e.preventDefault();
              if (password !== confirmPassword) {
                setError("Passwords do not match.");
                return;
              }
              setBusy(true);
              setError(null);
              try {
                await signup(email.trim(), password);
                router.replace("/dashboard/predict");
              } catch (err: any) {
                setError(err?.response?.data?.detail || err?.message || "Signup failed.");
              } finally {
                setBusy(false);
              }
            }}
          >
            <div>
              <label htmlFor="signup-email" className="text-sm font-medium">
                Email
              </label>
              <input
                id="signup-email"
                type="email"
                autoComplete="email"
                className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 placeholder:text-slate-500"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">Password</label>
              <input
                type="password"
                className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 placeholder:text-slate-500"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">Confirm Password</label>
              <input
                type="password"
                className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 placeholder:text-slate-500"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                required
              />
            </div>

            <button
              disabled={busy || !email.trim() || password.length < 8 || confirmPassword.length < 8}
              className="w-full rounded bg-indigo-500 px-4 py-2 font-medium text-white disabled:opacity-50"
              type="submit"
            >
              {busy ? "Creating account..." : "Sign up"}
            </button>
          </form>

          <p className="mt-4 text-sm text-slate-300">
            Already have an account?{" "}
            <Link className="font-medium text-indigo-200 hover:underline" href="/login">
              Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
