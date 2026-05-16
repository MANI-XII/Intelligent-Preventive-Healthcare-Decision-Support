import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect } from "react";
import { CheckBadgeIcon, DocumentTextIcon, SparklesIcon } from "@heroicons/react/24/outline";
import { useAuth } from "../context/AuthContext";

const heroFeatures = [
  {
    title: "Predictive risk scoring",
    description: "Multi-disease risk prediction with explainable AI insights.",
    Icon: CheckBadgeIcon,
  },
  {
    title: "Actionable recommendations",
    description: "Personalized preventive goals, tasks, and lifestyle suggestions.",
    Icon: SparklesIcon,
  },
  {
    title: "Report-ready insights",
    description: "Download PDF summaries and share results with your care team.",
    Icon: DocumentTextIcon,
  },
];

const steps = [
  {
    title: "Assess",
    desc: "Enter your health inputs once. The system estimates risk using trained models with clear, reviewable outputs.",
  },
  {
    title: "Understand",
    desc: "Review explanations and charts so you see what drove the prediction—not just a single score.",
  },
  {
    title: "Act",
    desc: "Simulate changes, schedule preventive tasks, and export PDFs to discuss with your care team.",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard/predict");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="flex w-full flex-1 flex-col">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-800/60 bg-gradient-to-b from-slate-950 via-slate-950 to-indigo-950/20 px-4 py-16 sm:px-6 sm:py-20 lg:px-8 lg:py-28">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            backgroundImage: `radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.35), transparent)`,
          }}
        />
        <div className="relative mx-auto grid max-w-7xl gap-12 lg:grid-cols-2 lg:gap-16 lg:items-center">
          <div>
            <p className="inline-flex rounded-full border border-indigo-500/35 bg-indigo-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-indigo-200">
              Explainable and Adaptive AI
            </p>
            <h1 className="mt-6 text-4xl font-bold leading-[1.1] tracking-tight text-slate-50 sm:text-5xl md:text-6xl lg:text-7xl">
              Intelligent Preventive Healthcare Decision Support
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-300 sm:text-xl">
              Predict chronic disease risk, understand model explanations, simulate lifestyle improvements, and track preventive
              actions from a single dashboard.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center rounded-xl bg-indigo-500 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-indigo-900/40 transition hover:bg-indigo-400"
              >
                Get Started
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-xl border border-slate-600 bg-slate-900/80 px-8 py-4 text-base font-semibold text-slate-100 transition hover:border-slate-500 hover:bg-slate-800"
              >
                Login
              </Link>
            </div>
            <div className="mt-14 space-y-4 border-t border-slate-800/80 pt-10 sm:max-w-lg">
              {heroFeatures.map(({ title, description, Icon }) => (
                <div key={title} className="flex items-start gap-4 rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4">
                  <div className="mt-1 flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-300">
                    <Icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-400">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-700/60 bg-slate-900/50 p-8 shadow-2xl shadow-slate-950/50 backdrop-blur-sm sm:p-10">
            <h2 className="text-2xl font-semibold text-slate-50">What you get</h2>
            <p className="mt-2 text-sm text-slate-400">Everything in one workspace—built for clarity, not clutter.</p>
            <ul className="mt-8 space-y-4">
              {[
                "Multi-disease risk prediction with explainable AI insights.",
                "Lifestyle simulation to compare risk before and after changes.",
                "Task tracking with weekly completion and trend analytics.",
                "Downloadable PDF reports for follow-up and consultation.",
              ].map((text) => (
                <li
                  key={text}
                  className="flex gap-4 rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 text-base leading-relaxed text-slate-200"
                >
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-indigo-400" aria-hidden />
                  {text}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-b border-slate-800/60 px-4 py-16 sm:px-6 sm:py-20 lg:px-8 lg:py-24">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-2xl">
            <h2 className="text-3xl font-bold tracking-tight text-slate-50 sm:text-4xl">How it works</h2>
            <p className="mt-3 text-lg text-slate-400">A simple loop: measure, interpret, and improve—without losing the human in the loop.</p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {steps.map((step, i) => (
              <div
                key={step.title}
                className="relative rounded-2xl border border-slate-800 bg-slate-900/40 p-8 transition hover:border-slate-700"
              >
                <span className="text-4xl font-bold text-slate-800">{String(i + 1).padStart(2, "0")}</span>
                <h3 className="mt-4 text-xl font-semibold text-slate-100">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="flex flex-1 flex-col justify-center px-4 py-16 sm:px-6 sm:py-20 lg:px-8 lg:py-28">
        <div className="mx-auto w-full max-w-5xl rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/50 to-slate-900/80 px-8 py-12 text-center sm:px-12 sm:py-16">
          <h2 className="text-2xl font-bold text-slate-50 sm:text-3xl">Ready to explore your preventive health picture?</h2>
          <p className="mx-auto mt-3 max-w-2xl text-slate-400">
            Create a free account to run predictions, simulations, and weekly task tracking. Your data stays under your account for
            this demo environment.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/signup"
              className="inline-flex rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-indigo-950 shadow-lg transition hover:bg-slate-100"
            >
              Create account
            </Link>
            <Link href="/login" className="inline-flex rounded-xl border border-slate-500 px-8 py-3.5 text-base font-semibold text-slate-100 hover:bg-slate-800/50">
              I already have an account
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
