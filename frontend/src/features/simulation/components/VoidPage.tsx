import { PuzzlePieceIcon } from "@heroicons/react/24/outline";
import { useEffect,useState } from "react";

export default function VoidPage() {
  const [rotated, set_rotated] = useState(false);

  useEffect(() => {
    let shake_count = 0;
    const timer = setInterval(() => {
      set_rotated(true);
      setTimeout(() => {
        set_rotated(false);
        shake_count++;
        if (shake_count < 2) {
          setTimeout(() => set_rotated(true), 150);
          setTimeout(() => set_rotated(false), 300);
        } else {
          shake_count = 0;
        }
      }, 150);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="select-none flex flex-col w-full h-full items-center justify-center">
      <span
        className="text-white/40 text-[30vh] transition-transform duration-300"
        style={{
          display: "inline-block",
          transform: rotated ? "rotate(15deg)" : "rotate(-15deg)",
        }}
      >
        <PuzzlePieceIcon className="h-42 w-42" />
      </span>
      <div className="mt-10 text-sm space-y-1 text-center">
        <p>
          There is no simulation dataset. Please upload a dataset or turn on
          simulation to start.
        </p>
        <p>
          Go to the{" "}
          <span className="rounded-lg px-2 py-1 bg-white/30 text-white/80">
            Simulation
          </span>{" "}
          tab and click{" "}
          <span className="rounded-lg px-2 py-1 bg-white/30 text-white/80">
            Start Simulation
          </span>
          .
        </p>
      </div>
    </div>
  );
}
