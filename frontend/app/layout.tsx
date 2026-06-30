import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "./nav";
import { Footer } from "./footer";

export const metadata: Metadata = {
  title: "聚职住 | JobPulse 北美",
  description: "北美华人招聘·租房聚合监控 — c.dadi360 / 168worker / us168168",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-surface-950 text-surface-100 font-sans antialiased flex flex-col">
        <Nav />
        <main className="max-w-6xl mx-auto px-4 py-8 w-full flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
