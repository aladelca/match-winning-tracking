import type { Metadata } from "next";
import Link from "next/link";
import type { Route } from "next";
import { Activity } from "lucide-react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Liga 1 Predictions",
  description: "Predicciones de partidos y análisis de sensibilidad",
};

type NavItem = {
  href: Route;
  label: string;
};

const NAV: NavItem[] = [
  { href: "/" as Route, label: "Partidos" },
  { href: "/teams" as Route, label: "Equipos" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="min-h-screen">
        <header className="border-b bg-card">
          <div className="container flex items-center justify-between py-4">
            <Link
              href={"/" as Route}
              className="flex items-center gap-2 font-semibold"
            >
              <Activity className="h-5 w-5" />
              <span>Liga 1 Predictions</span>
            </Link>
            <nav className="flex items-center gap-4 text-sm text-muted-foreground">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="hover:text-foreground"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="container py-8">{children}</main>
        <footer className="border-t py-6 text-center text-xs text-muted-foreground">
          Mock predictions · Datos ilustrativos · Local only
        </footer>
      </body>
    </html>
  );
}
