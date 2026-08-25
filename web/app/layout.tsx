import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LotClock — the listings will not tell you how long a car takes to sell",
  description:
    "Five weeks of daily Malaysian used-car listing snapshots, and why days-to-sell is not in the data.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
