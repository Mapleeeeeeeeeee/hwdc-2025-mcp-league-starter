import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HWDC 2025 MCP League",
  description: "Frontend companion for the HWDC 2025 MCP League starter kit.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}
