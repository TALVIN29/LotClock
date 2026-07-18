import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "What Drives a Used Car's Price?",
  description:
    "A gradient-boosted model trained on 7,900 real used-car listings, running entirely in your browser. No server, no LLM.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
