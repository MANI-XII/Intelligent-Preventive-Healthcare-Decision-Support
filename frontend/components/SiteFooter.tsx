import Link from "next/link";

const footerLinks = [
  { href: "/", label: "Home" },
  { href: "/login", label: "Login" },
  { href: "/signup", label: "Sign up" },
];

export default function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-slate-800/80 bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-4 lg:gap-8">
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-xs font-bold text-white">
                PH
              </span>
              <span className="font-semibold text-slate-100">Preventive Health</span>
            </div>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-400">
              Explainable, adaptive tools for preventive healthcare planning. Use insights to support decisions alongside your
              clinician—not as a substitute for professional medical advice.
            </p>
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Navigate</h3>
            <ul className="mt-4 space-y-2">
              {footerLinks.map((item) => (
                <li key={item.href}>
                  <Link href={item.href} className="text-sm text-slate-300 transition hover:text-indigo-300">
                    {item.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link href="/dashboard/predict" className="text-sm text-slate-300 transition hover:text-indigo-300">
                  Dashboard
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Product</h3>
            <ul className="mt-4 space-y-2 text-sm text-slate-300">
              <li>Risk prediction</li>
              <li>Lifestyle simulation</li>
              <li>Tasks &amp; progress</li>
              <li>PDF reports</li>
            </ul>
          </div>
        </div>
        <div className="mt-10 flex flex-col gap-3 border-t border-slate-800/80 pt-8 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Preventive Health Decision Support. Academic / demonstration use.</p>
          <p className="max-w-xl sm:text-right">
            Not a medical device. Predictions are probabilistic and may be wrong—always consult a qualified professional for
            diagnosis and treatment.
          </p>
        </div>
      </div>
    </footer>
  );
}
