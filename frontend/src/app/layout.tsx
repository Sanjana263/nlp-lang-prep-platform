import type { Metadata } from "next";
import { Atkinson_Hyperlegible_Mono, Atkinson_Hyperlegible_Next, Crimson_Pro } from "next/font/google";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

// Display: Crimson Pro (scholarly headings, band figures).
// Body: Atkinson Hyperlegible Next, designed for legibility, which matters for second-language readers.
// Data: Atkinson Hyperlegible Mono for labels, counts and tabular figures.
const display = Crimson_Pro({ variable: "--font-crimson", subsets: ["latin"] });
// No fallback metrics ship for the two Atkinson faces, so name the fallbacks explicitly.
const body = Atkinson_Hyperlegible_Next({
  variable: "--font-atkinson",
  subsets: ["latin"],
  adjustFontFallback: false,
  fallback: ["system-ui", "Segoe UI", "sans-serif"],
});
const mono = Atkinson_Hyperlegible_Mono({
  variable: "--font-atkinson-mono",
  subsets: ["latin"],
  adjustFontFallback: false,
  fallback: ["ui-monospace", "Cascadia Mono", "monospace"],
});

export const metadata: Metadata = {
  title: { default: "Cadence", template: "%s · Cadence" },
  description: "Practice for IELTS, TOEFL and PTE with instant band estimates and feedback.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only z-50 rounded-md bg-accent px-4 py-2 text-on-accent focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
        >
          Skip to content
        </a>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
