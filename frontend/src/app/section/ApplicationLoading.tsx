interface ApplicationLoadingProps {
  progress?: number;
  error?: string;
  on_retry?: () => void;
}

export default function ApplicationLoading({ progress, error, on_retry }: ApplicationLoadingProps) {
  return <div className="fixed inset-0 z-[70] flex min-h-dvh flex-col items-center justify-center gap-6 bg-black px-6 text-center text-white">
    <p className="text-3xl font-semibold tracking-widest">OPHANIM</p>
    {error ? <>
      <p role="alert" className="max-w-md text-sm text-white/70">{error}</p>
      <button type="button" onClick={on_retry} className="rounded-md border border-white/40 px-5 py-2 text-sm transition hover:bg-white/10">Retry background</button>
    </> : <div role="status" aria-label={progress === undefined ? "Loading application" : "Loading background"} className="flex flex-col items-center gap-4">
      <span aria-hidden="true" className="h-8 w-8 animate-spin rounded-full border border-white/20 border-t-white" />
      <p className="text-sm text-white/65">{progress === undefined ? "Loading…" : "Preparing the Earth…"}</p>
      {progress !== undefined && <div className="w-48">
        <div role="progressbar" aria-label="Background assets" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress)}
          className="h-px overflow-hidden bg-white/15">
          <div className="h-full bg-white/80 transition-[width] duration-300" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-2 text-xs tabular-nums text-white/35">{Math.round(progress)}%</p>
      </div>}
    </div>}
  </div>;
}
