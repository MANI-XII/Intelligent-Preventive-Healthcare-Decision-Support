import Link from "next/link";
import { ElementType } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../context/AuthContext";
import SiteFooter from "./SiteFooter";
import {
  ChartBarIcon,
  SparklesIcon,
  ClipboardDocumentListIcon,
  EyeDropperIcon,
  ArrowsRightLeftIcon,
  ChatBubbleLeftRightIcon,
  UserCircleIcon,
} from "@heroicons/react/24/outline";

type NavLeaf = {
  href?: string;
  label: string;
  icon: ElementType;
  children?: NavLeaf[];
  aliases?: string[];
};

const navItems: NavLeaf[] = [
  {
    label: "Smart Analysis",
    icon: ChartBarIcon,
    children: [
      { href: "/dashboard/predict", label: "Prediction", icon: ChartBarIcon },
      { href: "/dashboard/simulate", label: "Simulation", icon: SparklesIcon },
    ],
  },
  { href: "/dashboard/monitor", label: "Monitoring & Alerts", icon: EyeDropperIcon, aliases: ["/dashboard/alerts"] },
  { href: "/dashboard/tasks", label: "Goals & Progress", icon: ClipboardDocumentListIcon, aliases: ["/dashboard/goals"] },
  { href: "/dashboard/insights", label: "Insights", icon: ArrowsRightLeftIcon, aliases: ["/dashboard/behavior", "/dashboard/gamification"] },
  { href: "/dashboard/chat", label: "Chatbot", icon: ChatBubbleLeftRightIcon },
  { href: "/dashboard/profile", label: "Profile", icon: UserCircleIcon },
];

export default function DashboardLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { userId, logout } = useAuth();

  const routeMatches = (item: NavLeaf) =>
    Boolean(item.href && (router.pathname === item.href || item.aliases?.includes(router.pathname)));

  const renderNavItem = (item: NavLeaf, nested = false) => {
    const hasChildren = Boolean(item.children?.length);
    const childActive = item.children?.some((child) => routeMatches(child)) ?? false;
    const active = item.href ? routeMatches(item) : childActive;
    const Icon = item.icon;

    if (hasChildren) {
      return (
        <div key={item.label} className="rounded-3xl border border-slate-800 bg-slate-950/70 p-3">
          <div className={`flex items-center gap-3 rounded-2xl px-3 py-3 ${active ? "bg-indigo-500/10 text-indigo-100" : "text-slate-200"}`}>
            <Icon className="h-5 w-5 flex-shrink-0 text-slate-300" />
            <span className="text-base font-semibold">{item.label}</span>
          </div>
          <div className="mt-2 space-y-2 pl-4">
            {item.children?.map((child) => renderNavItem(child, true))}
          </div>
        </div>
      );
    }

    return (
      <Link
        key={item.href}
        href={item.href || "#"}
        className={`flex items-center gap-3 rounded-3xl px-5 py-4 text-base font-semibold transition ${
          active
            ? "bg-indigo-500 text-white shadow-sm"
            : nested
              ? "bg-slate-900 text-slate-200 hover:bg-slate-800"
              : "bg-slate-950 text-slate-200 hover:bg-slate-800"
        }`}
      >
        <Icon className="h-5 w-5 flex-shrink-0 text-slate-300" />
        <span>{item.label}</span>
      </Link>
    );
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 lg:px-6">
          <Link href="/" className="text-left transition hover:opacity-90">
            <div className="text-lg font-semibold text-slate-100">Preventive Healthcare Dashboard</div>
            <div className="text-xs text-slate-400">
              <span className="text-slate-500">Email · </span>
              {userId}
            </div>
          </Link>
        </div>
      </header>

      <div className="flex w-full flex-1 gap-6 px-4 py-8 lg:px-6">
        <aside className="h-full w-full max-w-[320px] shrink-0 rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20 lg:block">
          <div className="mb-6 border-b border-slate-800 pb-4">
            <div className="text-base font-semibold uppercase tracking-[0.24em] text-slate-300">Navigation</div>
          </div>
          <nav className="space-y-3">
            {navItems.map((item) => renderNavItem(item))}
          </nav>
          <div className="mt-6 border-t border-slate-800 pt-4">
            <button
              onClick={() => {
                logout();
                router.replace("/login");
              }}
              className="w-full rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
            >
              Logout
            </button>
          </div>
        </aside>

        <main className="h-full flex-1 rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl shadow-slate-950/10">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-slate-100">{title}</h1>
            {subtitle ? <p className="mt-2 text-base leading-relaxed text-slate-300">{subtitle}</p> : null}
          </div>
          {children}
        </main>
      </div>

      <SiteFooter />
    </div>
  );
}
