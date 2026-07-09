"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import type { ReactNode } from "react";

const kpis = [
  { label: "Projects", sub: "Accessible", value: 24, href: "/projects", tint: "blue", icon: "doc" },
  { label: "In Review", sub: "Active", value: 18, href: "/dashboard/queue", tint: "green", icon: "check" },
  { label: "Pending Response", sub: "Applicant", value: 7, href: "/response-package", tint: "amber", icon: "clock" },
  { label: "Ready for Handoff", sub: "Packages", value: 5, href: "/review-packet", tint: "violet", icon: "users" },
] as const;

const workload = [
  { label: "Document Review", value: 24, pct: 44, color: "#2563eb", href: "/documents" },
  { label: "Evidence Review", value: 12, pct: 22, color: "#16a34a", href: "/findings" },
  { label: "Applicant Response", value: 7, pct: 13, color: "#f59e0b", href: "/response-package" },
  { label: "Package Handoff", value: 5, pct: 9, color: "#a855f7", href: "/review-packet" },
  { label: "Other", value: 6, pct: 12, color: "#94a3b8", href: "/workflow-board" },
];

const workloadTotal = 54;

const recentActivity = [
  { title: "Document set uploaded", meta: "Brookside Meadows", time: "2h ago", href: "/documents" },
  { title: "Response submitted by applicant", meta: "Pinecrest Commercial", time: "4h ago", href: "/response-package" },
  { title: "Finding updated", meta: "Riverside Office Park", time: "5h ago", href: "/findings" },
  { title: "Package ready for handoff", meta: "Meadowbrook Phase 2", time: "1d ago", href: "/review-packet" },
];

const priorityAlerts = [
  { kind: "overdue", title: "Response overdue", meta: "Pinecrest Commercial", time: "2 days", href: "/dashboard/queue" },
  { kind: "warning", title: "Evidence expiring soon", meta: "Riverside Office Park", time: "5 days", href: "/findings" },
  { kind: "info", title: "Reviewer capacity high", meta: "Multiple projects", time: "5h ago", href: "/dashboard" },
];

const sidebar = [
  { label: "Dashboard", href: "/", icon: "grid" },
  { label: "Projects", href: "/projects", icon: "doc" },
  { label: "Reviewer Queue", href: "/dashboard/queue", icon: "list" },
  { label: "Rule Packs", href: "/rule-packs", icon: "layers" },
  { label: "Organizations", href: "/organizations", icon: "users" },
  { label: "Guided Demo", href: "/guided-demo", icon: "play" },
];

function Donut({
  active,
  setActive,
}: {
  active: number | null;
  setActive: (i: number | null) => void;
}) {
  const R = 70;
  const STROKE = 26;
  const C = 2 * Math.PI * R;
  let offset = 0;

  return (
    <svg viewBox="0 0 180 180" className="h-44 w-44">
      <g transform="rotate(-90 90 90)">
        {workload.map((s, i) => {
          const len = (s.pct / 100) * C;
          const dash = `${len} ${C - len}`;

          const el = (
            <circle
              key={s.label}
              cx="90"
              cy="90"
              r={R}
              fill="none"
              stroke={s.color}
              strokeWidth={active === i ? STROKE + 6 : STROKE}
              strokeDasharray={dash}
              strokeDashoffset={-offset}
              className="cursor-pointer transition-all duration-200"
              style={{ opacity: active === null || active === i ? 1 : 0.35 }}
              onMouseEnter={() => setActive(i)}
              onMouseLeave={() => setActive(null)}
            />
          );

          offset += len;
          return el;
        })}
      </g>

      <text x="90" y="84" textAnchor="middle" className="fill-slate-900 text-2xl font-bold">
        {active === null ? workloadTotal : workload[active].value}
      </text>

      <text x="90" y="104" textAnchor="middle" className="fill-slate-500 text-[11px]">
        {active === null ? "Total Items" : workload[active].label}
      </text>
    </svg>
  );
}

function Icon({
  name,
  className = "h-5 w-5",
}: {
  name: string;
  className?: string;
}) {
  const paths: Record<string, ReactNode> = {
    grid: <path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z" />,
    doc: <path d="M6 2h9l5 5v15H6zM15 2v5h5" />,
    list: <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />,
    layers: <path d="M12 2 2 7l10 5 10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />,
    users: <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0 .01M23 21v-2a4 4 0 0 0-3-3.87" />,
    play: <circle cx="12" cy="12" r="9" />,
    check: <path d="M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
  };

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {paths[name] ?? paths.doc}
    </svg>
  );
}

const tints: Record<string, string> = {
  blue: "bg-blue-50 text-blue-600",
  green: "bg-green-50 text-green-600",
  amber: "bg-amber-50 text-amber-600",
  violet: "bg-violet-50 text-violet-600",
};

export default function HomeDashboard() {
  const [active, setActive] = useState<number | null>(null);

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <aside className="hidden w-60 shrink-0 flex-col justify-between bg-slate-900 px-4 py-5 text-slate-200 lg:flex">
        <div>
          <div className="mb-8 flex items-center gap-3 px-2">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-teal-400 to-blue-600 text-sm font-bold text-white">
              CE
            </div>

            <div>
              <div className="text-sm font-semibold text-white">Civil Engineer AI</div>
              <div className="text-[11px] text-slate-400">Stormwater Review Assistant</div>
            </div>
          </div>

          <nav className="space-y-1">
            {sidebar.map((s, i) => (
              <Link
                key={s.href}
                href={s.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                  i === 0
                    ? "bg-white/10 font-medium text-white"
                    : "text-slate-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                <Icon name={s.icon} className="h-[18px] w-[18px]" />
                {s.label}
              </Link>
            ))}
          </nav>
        </div>

        <Link href="/workspace" className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-2.5 hover:bg-white/10">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-teal-400 to-blue-600 text-xs font-bold text-white">
            CE
          </div>

          <div className="text-left text-xs">
            <div className="font-medium text-white">Civil Engineer</div>
            <div className="text-slate-400">Reviewer</div>
          </div>
        </Link>
      </aside>

      <main className="flex-1">
        <section className="px-4 pb-4 pt-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
                  Reviewer Command Center
                </h1>
                <p className="mt-1 text-sm text-slate-600">
                  Document-first. Evidence-first. Reviewer-controlled.
                </p>
              </div>

              <div className="w-fit rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2">
                <div className="flex items-center gap-2 text-xs font-medium text-emerald-800">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  System Status
                </div>
                <div className="text-[11px] text-emerald-700">All Systems Operational</div>
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
              <div className="relative aspect-[16/9] w-full">
                <Image
                  src="/images/civil-engineer/brookside-project-thumbnail.webp"
                  alt="Brookside Meadows residential subdivision aerial view"
                  fill
                  priority
                  sizes="(max-width: 768px) 100vw, (max-width: 1280px) calc(100vw - 320px), 1152px"
                  className="object-cover object-center"
                />
              </div>
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 gap-6 px-4 pb-6 sm:px-6 lg:px-8 xl:grid-cols-[1fr_300px]">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {kpis.map((k) => (
                <Link
                  key={k.label}
                  href={k.href}
                  className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className={`mb-3 grid h-10 w-10 place-items-center rounded-lg ${tints[k.tint]}`}>
                    <Icon name={k.icon} />
                  </div>

                  <div className="text-3xl font-bold">{k.value}</div>
                  <div className="text-sm font-medium text-slate-700">{k.label}</div>
                  <div className="text-xs text-slate-400">{k.sub}</div>
                </Link>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold">Active Workload</h2>

                <div className="flex items-center justify-center">
                  <Donut active={active} setActive={setActive} />
                </div>

                <ul className="mt-4 space-y-2">
                  {workload.map((s, i) => (
                    <li key={s.label}>
                      <Link
                        href={s.href}
                        onMouseEnter={() => setActive(i)}
                        onMouseLeave={() => setActive(null)}
                        className="flex items-center justify-between rounded-md px-2 py-1 text-xs hover:bg-slate-50"
                      >
                        <span className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
                          {s.label}
                        </span>

                        <span className="text-slate-500">
                          {s.value} ({s.pct}%)
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold">Recent Activity</h2>

                <ul className="space-y-1">
                  {recentActivity.map((a) => (
                    <li key={a.title + a.meta}>
                      <Link href={a.href} className="flex items-start gap-3 rounded-md px-2 py-2 hover:bg-slate-50">
                        <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-500">
                          <Icon name="doc" className="h-3.5 w-3.5" />
                        </span>

                        <span className="min-w-0 flex-1">
                          <span className="block text-xs font-medium text-slate-800">{a.title}</span>
                          <span className="block text-[11px] text-slate-400">{a.meta}</span>
                        </span>

                        <span className="whitespace-nowrap text-[11px] text-slate-400">{a.time}</span>
                      </Link>
                    </li>
                  ))}
                </ul>

                <Link href="/audit" className="mt-2 block px-2 text-xs font-medium text-blue-600 hover:underline">
                  View all activity →
                </Link>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold">Priority Alerts</h2>

                <ul className="space-y-1">
                  {priorityAlerts.map((a) => (
                    <li key={a.title}>
                      <Link href={a.href} className="flex items-start gap-3 rounded-md px-2 py-2 hover:bg-slate-50">
                        <span
                          className={`mt-0.5 text-sm ${
                            a.kind === "overdue"
                              ? "text-red-500"
                              : a.kind === "warning"
                                ? "text-amber-500"
                                : "text-blue-500"
                          }`}
                        >
                          {a.kind === "overdue" ? "▮" : a.kind === "warning" ? "⚠" : "◉"}
                        </span>

                        <span className="min-w-0 flex-1">
                          <span className="block text-xs font-medium text-slate-800">{a.title}</span>
                          <span className="block text-[11px] text-slate-400">{a.meta}</span>
                        </span>

                        <span className="whitespace-nowrap text-[11px] text-slate-400">{a.time}</span>
                      </Link>
                    </li>
                  ))}
                </ul>

                <Link href="/dashboard/queue" className="mt-2 block px-2 text-xs font-medium text-blue-600 hover:underline">
                  View all alerts →
                </Link>
              </div>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold">Map Overview</h2>

              <Link href="/sheet-viewer" className="block overflow-hidden rounded-lg">
                <div className="relative h-36 w-full">
                  <Image
                    src="/images/civil-engineer/dashboard-hero-command-center.webp"
                    alt="Project map overview"
                    fill
                    sizes="300px"
                    className="object-cover"
                    style={{ objectPosition: "82% 40%" }}
                  />
                </div>
              </Link>

              <div className="mt-4 flex gap-8">
                <div>
                  <div className="text-xl font-bold">12</div>
                  <div className="text-[11px] text-slate-400">On Map</div>
                </div>

                <div>
                  <div className="text-xl font-bold">3</div>
                  <div className="text-[11px] text-slate-400">Near You</div>
                </div>
              </div>

              <div className="mt-1 text-[11px] text-slate-400">Active Projects by Location</div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-2 flex items-center gap-2">
                <span className="text-green-600">⚖</span>
                <h2 className="text-sm font-semibold">System Guidance</h2>
              </div>

              <p className="text-xs leading-relaxed text-slate-500">
                AI provides review support. You make the decisions. Every review is human.
              </p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
