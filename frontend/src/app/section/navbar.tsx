import Link from "next/link";

// Navbar.tsx
export default function Navbar() {

  const navItems = [
    { name: "MySQL", href: "http://localhost:8081/?server=mysql&username=mysql_admin&db=mysql_db" },
    { name: "Timescale", href: "http://localhost:5050/" },
    // { name: "Docs", href: "#" },
    { name: "Github", href: "https://github.com/MaaZiJyun" },
  ];

  return (
    <nav className="absolute text-white top-0 left-0 w-full px-8 py-4 flex items-center justify-between z-50">
      <div className="text-2xl font-semibold tracking-wide select-none">
        <Link href="/" className="relative">
          OPHANIM
        </Link>
      </div>
      <div className="flex space-x-10 text-sm font-medium items-center">
        {navItems.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className="relative"
          >
            {item.name}
          </a>
        ))}
      </div>
    </nav>
  );
}
