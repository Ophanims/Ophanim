import Link from "next/link";

// Navbar.tsx
export default function Navbar() {

  return (
    <nav className="absolute text-white top-0 left-0 w-full px-8 py-4 flex items-center justify-between z-50">
      <div className="text-2xl font-semibold tracking-wide select-none">
        <Link href="/" className="relative">
          OPHANIM
        </Link>
      </div>
      <div className="flex space-x-10 text-sm font-medium items-center">
        {["Docs", "Github"].map((item) => (
          <a
            key={item}
            href="#"
            className="relative"
          >
            {item}
          </a>
        ))}
      </div>
    </nav>
  );
}
