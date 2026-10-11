import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LotClock — Malaysian used-car listings, measured daily",
  description:
    "Daily snapshots of Malaysian used-car listings, July to October 2026: what the ads show, and what they cannot.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div
          style={{
            background: "var(--accent-soft)",
            color: "var(--text)",
            fontSize: "0.9rem",
            padding: "10px 20px",
            textAlign: "center",
          }}
        >
          Collection stopped 2026-10-11. Findings are final.{" "}
          <a href="/">Read the final note</a>
        </div>
        {children}
      </body>
    </html>
  );
}
