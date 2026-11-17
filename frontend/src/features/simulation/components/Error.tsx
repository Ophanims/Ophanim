import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import Link from "next/link";

export default function ErrorPage({
  title = "Something went wrong",
  message = "An unexpected error occurred. Try refreshing or contact support if the problem persists.",
  on_retry,
}: {
  title?: string;
  message?: string;
  on_retry?: () => void;
}) {
  const handle_retry = () => {
    if (on_retry) on_retry();
    else window.location.reload();
  };

  return (
    <div className="bg-black select-none flex flex-col w-full h-screen items-center justify-center p-6">
      <div>
        <ExclamationTriangleIcon className="h-20 w-20 text-red-500" />
      </div>

      <div className="mt-8 text-center max-w-xl">
        <h1 className="text-2xl font-semibold text-white mb-2">{title}</h1>
        <p className="text-sm text-white/70 mb-4">{message}</p>

        <div className="flex items-center justify-center gap-3">
          <button
            onClick={handle_retry}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 active:bg-red-700 text-white rounded-md text-sm shadow"
          >
            Retry
          </button>

          <Link
            href="/"
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-md text-sm"
          >
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
