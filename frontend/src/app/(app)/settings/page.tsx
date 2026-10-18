import { SettingsView } from "@/components/settings-view";

// Login-gated, browser-rendered page: there is nothing static for Next's instant-navigation
// dev check to validate. (`instant` can only be exported from a Server Component, hence
// this thin wrapper around the client view.)
export const instant = false;

export default function SettingsPage() {
  return <SettingsView />;
}
