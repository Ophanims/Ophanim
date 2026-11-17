export default function BrandIntroduction({ title_id }: { title_id: string }) {
  return <section className="md:pr-12 lg:pr-16" aria-labelledby={title_id}>
    <h1 id={title_id} className="text-5xl font-bold tracking-tight sm:text-6xl">OPHANIM</h1>
    <p className="mt-3 max-w-sm text-lg leading-relaxed tracking-tight text-white/85 sm:text-xl">
      Lightweight Satellite Constellation Simulator
    </p>
  </section>;
}
