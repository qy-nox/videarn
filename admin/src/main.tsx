import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Bell, Coins, FileWarning, Flag, Gauge, LayoutDashboard, LogOut, Megaphone, Menu, Settings, ShieldAlert, Users, Video, WalletCards } from "lucide-react";
import { adminLogin, get, mutate } from "./api";
import "./index.css";

type View = { key: string; label: string; icon: React.ElementType; endpoint: string };
const views: View[] = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard, endpoint: "/admin/dashboard" },
  { key: "users", label: "Users", icon: Users, endpoint: "/admin/users" },
  { key: "videos", label: "Videos", icon: Video, endpoint: "/admin/videos" },
  { key: "moderation", label: "Moderation queue", icon: Flag, endpoint: "/admin/videos?status=pending_review" },
  { key: "reports", label: "Reports", icon: FileWarning, endpoint: "/admin/reports" },
  { key: "finance", label: "Wallet & Finance", icon: WalletCards, endpoint: "/admin/withdrawals" },
  { key: "ads", label: "Ads management", icon: BarChart3, endpoint: "/admin/ads" },
  { key: "economy", label: "Economy settings", icon: Coins, endpoint: "/admin/economy" },
  { key: "fraud", label: "Fraud center", icon: ShieldAlert, endpoint: "/admin/fraud" },
  { key: "content", label: "Content setup", icon: Megaphone, endpoint: "/admin/hashtags" },
  { key: "notifications", label: "Notifications", icon: Bell, endpoint: "/admin/settings" },
  { key: "config", label: "Feature flags & config", icon: Settings, endpoint: "/admin/settings" },
  { key: "admins", label: "Admin users & roles", icon: Users, endpoint: "/admin/admin-users" },
  { key: "audit", label: "Audit logs", icon: Gauge, endpoint: "/admin/audit-logs" },
  { key: "support", label: "Support", icon: Bell, endpoint: "/admin/settings" },
];

function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [totp, setTotp] = useState(""); const [error, setError] = useState("");
  return <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
    <form className="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl" onSubmit={async (e) => { e.preventDefault(); try { await adminLogin(email, password, totp || undefined); onLogin(); } catch { setError("Login failed. Check credentials and 2FA code."); } }}>
      <div className="mb-8"><div className="mb-3 inline-flex rounded-xl bg-indigo-600 p-3 text-white"><Gauge /></div><h1 className="text-2xl font-bold">ClipEarn Admin</h1><p className="mt-1 text-sm text-slate-500">Secure operations console</p></div>
      {error && <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      <label className="mb-4 block text-sm font-medium">Email<input className="mt-1 w-full rounded-lg border p-3" type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
      <label className="mb-4 block text-sm font-medium">Password<input className="mt-1 w-full rounded-lg border p-3" type="password" value={password} onChange={e => setPassword(e.target.value)} required /></label>
      <label className="mb-6 block text-sm font-medium">TOTP code (if enabled)<input className="mt-1 w-full rounded-lg border p-3" value={totp} onChange={e => setTotp(e.target.value)} /></label>
      <button className="btn-primary w-full">Sign in</button>
    </form>
  </main>;
}

function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: () => get<any>("/admin/dashboard") });
  if (isLoading) return <Loading />;
  const cards = [["Users", data.users, Users], ["New signups", data.new_users_30d, BarChart3], ["Videos", data.videos, Video], ["Total views", data.views, Gauge], ["Pending withdrawals", data.pending_withdrawals, WalletCards], ["Fraud alerts", data.fraud_alerts, ShieldAlert]];
  return <><Header title="Dashboard" /><div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">{cards.map(([label, value, Icon]: any) => <div className="card" key={label}><Icon className="mb-4 text-indigo-600" size={20} /><p className="text-sm text-slate-500">{label}</p><p className="mt-1 text-2xl font-bold">{value.toLocaleString()}</p></div>)}</div><div className="mt-6 grid gap-6 lg:grid-cols-2"><div className="card"><h2 className="font-semibold">Payout budget</h2><div className="mt-5 h-4 overflow-hidden rounded-full bg-slate-100"><div className={`h-full ${data.payout_budget.paused ? "bg-red-500" : "bg-emerald-500"}`} style={{ width: `${Math.min(100, data.payout_budget.issued_coins / Math.max(1, data.payout_budget.estimated_revenue_usd * 10))}%` }} /></div><p className="mt-3 text-sm text-slate-500">Issued: {data.payout_budget.issued_coins.toLocaleString()} coins · Revenue: ${data.payout_budget.estimated_revenue_usd}</p></div><div className="card"><h2 className="font-semibold">Operational status</h2><p className="mt-4 text-sm text-slate-600">{data.payout_budget.paused ? "Rewards are paused until the payout budget is increased." : "Rewards budget is active."}</p></div></div></>;
}

function Header({ title }: { title: string }) { return <div className="mb-6 flex items-center justify-between"><div><h1 className="text-2xl font-bold">{title}</h1><p className="text-sm text-slate-500">ClipEarn operations</p></div><div className="rounded-full bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">Production controls enabled</div></div>; }
function Loading() { return <div className="card animate-pulse text-slate-400">Loading...</div>; }
function DataView({ view }: { view: View }) {
  const queryClient = useQueryClient(); const [status, setStatus] = useState("pending"); const [selected, setSelected] = useState<any>(null);
  const { data, isLoading, error } = useQuery({ queryKey: [view.key, status], queryFn: () => get<any>(view.endpoint) });
  if (isLoading) return <><Header title={view.label} /><Loading /></>;
  if (error) return <><Header title={view.label} /><div className="card text-red-600">Unable to load this page. Confirm your role permissions and API availability.</div></>;
  if (view.key === "economy") return <Economy data={data} />;
  if (view.key === "ads") return <Ads data={data} />;
  const rows = Array.isArray(data) ? data : Object.entries(data).map(([key, value]) => ({ key, value }));
  const columns = rows.length ? Object.keys(rows[0]) : [];
  return <><Header title={view.label} /><div className="card overflow-x-auto"><div className="mb-4 flex items-center justify-between"><p className="text-sm text-slate-500">{rows.length} records</p>{["videos","moderation","reports","finance"].includes(view.key) && <select className="rounded-lg border p-2 text-sm" value={status} onChange={e => setStatus(e.target.value)}><option value="pending">Pending</option><option value="open">Open</option><option value="published">Published</option><option value="pending_review">Pending review</option></select>}</div><table className="w-full text-left text-sm"><thead><tr className="border-b text-xs uppercase text-slate-400">{columns.slice(0, 7).map(c => <th className="px-3 py-3" key={c}>{c.replaceAll("_", " ")}</th>)}</tr></thead><tbody>{rows.map((row: any, i: number) => <tr className="border-b last:border-0 hover:bg-slate-50" key={row.id ?? row.key ?? i}>{columns.slice(0, 7).map(c => <td className="max-w-xs truncate px-3 py-3" key={c}>{typeof row[c] === "object" ? JSON.stringify(row[c]) : String(row[c] ?? "—")}</td>)}</tr>)}</tbody></table></div></>;
}
function Economy({ data }: { data: any }) { const [values, setValues] = useState(JSON.stringify(data, null, 2)); return <><Header title="Economy settings" /><div className="card max-w-3xl"><p className="mb-3 text-sm text-slate-500">Versioned settings control rewards, referrals, withdrawals, and payout safety.</p><textarea className="h-80 w-full rounded-lg border p-3 font-mono text-sm" value={values} onChange={e => setValues(e.target.value)} /><button className="btn-primary mt-4" onClick={async () => { await mutate("put", "/admin/economy", { values: JSON.parse(values) }); }}>Save settings</button></div></>; }
function Ads({ data }: { data: any }) { const [values, setValues] = useState(data); return <><Header title="Ads management" /><div className="card max-w-xl space-y-4">{Object.entries(values).map(([key, value]) => <label className="block text-sm font-medium" key={key}>{key.replaceAll("_", " ")}<input className="mt-1 w-full rounded-lg border p-3" type="number" value={String(value)} onChange={e => setValues({ ...values, [key]: Number(e.target.value) })} /></label>)}<button className="btn-primary" onClick={() => mutate("put", "/admin/ads", values)}>Save ad config</button></div></>; }
function App() { const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem("admin_token")); const [view, setView] = useState("dashboard"); const [open, setOpen] = useState(true); const active = views.find(x => x.key === view) ?? views[0]; if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />; return <div className="flex min-h-screen"><aside className={`${open ? "w-64" : "w-16"} shrink-0 border-r bg-slate-950 text-white transition-all`}><div className="flex h-16 items-center gap-3 border-b border-white/10 px-4"><button onClick={() => setOpen(!open)}><Menu size={20} /></button>{open && <span className="font-bold">ClipEarn</span>}</div><nav className="space-y-1 p-2">{views.map(item => <button key={item.key} onClick={() => setView(item.key)} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm ${view === item.key ? "bg-indigo-600" : "text-slate-300 hover:bg-white/10"}`}><item.icon size={18} />{open && item.label}</button>)}</nav><button onClick={() => { localStorage.removeItem("admin_token"); setLoggedIn(false); }} className="absolute bottom-4 ml-2 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/10"><LogOut size={18} />{open && "Sign out"}</button></aside><main className="min-w-0 flex-1 p-6 lg:p-8">{view === "dashboard" ? <Dashboard /> : <DataView view={active} />}</main></div>; }
createRoot(document.getElementById("root")!).render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>);
