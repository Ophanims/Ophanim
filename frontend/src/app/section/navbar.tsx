"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

function navigate_home(event: { preventDefault: () => void }, hash: string) {
  if (window.location.pathname !== "/") return;
  event.preventDefault();
  window.location.hash = hash;
}

export default function Navbar() {
  const pathname = usePathname();
  if (pathname === "/workspace" || pathname.startsWith("/workspace/")) return null;

  return <nav className="flex h-14 shrink-0 items-center justify-between border-b border-white/20 bg-black px-6 text-white">
    <Link href="/" onNavigate={(event) => navigate_home(event, "")} className="text-xl font-semibold">OPHANIM</Link>
    <div className="flex gap-8 text-sm"><Link href="/#projects" onNavigate={(event) => navigate_home(event, "projects")}>Projects</Link><Link href="/records">Records</Link></div>
  </nav>;
}
