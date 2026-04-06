"use client";

import { useRouter } from "next/navigation";
import Navbar from "./section/navbar";

export default function Home() {
  const router = useRouter();

  const handleGetStarted = () => {
    router.push("/dashboard");
  };
  return (
    <div className="w-full h-screen relative font-sans overflow-hidden">
      <Navbar />

      {/* Hero Section */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center z-20 px-6 max-w-3xl mx-auto select-none">
        <h1 className="text-6xl font-extrabold mb-6 tracking-tight drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]">
          OPHANIM
        </h1>
        <p className="mb-10 text-xl leading-relaxed max-w-lg">
          OPHANIM, Light and easy visualization for LEO satellite
          experiments.
        </p>
        <button
          onClick={handleGetStarted}
          className="relative inline-block rounded-md border bg-transparent px-8 py-3 font-semibold transition hover:scale-105 hover:cursor-pointer"
        >
          Get Started
        </button>
      </div>

      {/* <Footer /> */}
    </div>
  );
}
