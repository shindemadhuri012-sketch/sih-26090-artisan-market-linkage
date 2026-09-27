import type { Metadata } from "next";
import React from "react";
import { PWAProvider } from "./pwa-provider";

export const metadata: Metadata = {
  title: "SIH 26090: Artisan Market Linkage",
  description: "AI-Powered Market Linkage & Smart Seller Matching for Indian Artisans",
  manifest: "/manifest.json",
  themeColor: "#b45309",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, -apple-system, sans-serif", backgroundColor: "#fdfbf7", color: "#1c1917" }}>
        <PWAProvider>{children}</PWAProvider>
      </body>
    </html>
  );
}
