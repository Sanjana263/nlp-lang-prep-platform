import { DashboardView } from "@/components/dashboard-view";

// Login-gated, browser-rendered page: there is nothing static for Next's instant-navigation
// dev check to validate. (`instant` can only be exported from a Server Component, hence
// this thin wrapper around the client view.)
export const instant = false;
export const metadata = { title: "Dashboard" };

export default function DashboardPage() {
  return <DashboardView />;
}
