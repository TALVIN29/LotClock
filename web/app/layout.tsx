import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LotClock — Malaysian used-car listings, measured daily",
  description:
    "Daily snapshots of Malaysian used-car listings since July 2026: what the ads show, and what they cannot.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
