import type { Metadata } from "next";
import { Instrument_Sans, Inter } from "next/font/google";
import "./globals.css";

const instrumentSans = Instrument_Sans({
  variable: "--fonte-titulo",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--fonte-corpo",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Finas",
  description: "Contas finas, sem stress.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="pt"
      className={`${instrumentSans.variable} ${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
