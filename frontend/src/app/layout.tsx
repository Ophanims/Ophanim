import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "@/app/globals.css";
import Navbar from "./section/navbar";


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Ophanim",
  description: "Satellite simulation, scheduling and model training",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`select-none ${geistSans.variable} ${geistMono.variable} antialiased flex h-dvh flex-col overflow-hidden bg-black text-white`}
      >
        <Navbar />
        <div className="relative min-h-0 flex-1 overflow-auto">
          {children}
        </div>
      </body>
    </html>
  );
}
