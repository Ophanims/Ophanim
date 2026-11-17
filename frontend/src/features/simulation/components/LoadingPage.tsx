"use client";
import { SpinnerWidget } from "./SpinnerWidget";

export default function LoadingPage() {
  return (
    <div className="w-full h-screen flex flex-col items-center justify-center bg-gray-08 text-white gap-6">
      <SpinnerWidget className={"w-36 h-36 border-4 border-white/50"} />
    </div>
  );
}
