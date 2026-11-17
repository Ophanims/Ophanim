import Link from "next/link";
import { PencilSquareIcon, TrashIcon } from "@heroicons/react/24/outline";
import type { Project } from "../../contracts/generated";

interface ProjectListProps {
  projects: Project[];
  search_content: string;
  set_search_content: (search_content: string) => void;
  on_edit: (project: Project) => void;
  delete_project: (project_id: string) => Promise<void>;
}

export default function ProjectList({ projects, search_content, set_search_content, on_edit, delete_project }: ProjectListProps) {
  return <section aria-labelledby="projects-heading" className="mt-10 min-w-0">
    <div className="mb-4 flex items-center justify-between gap-4">
      <h2 id="projects-heading" className="text-lg font-semibold">Projects</h2>
      <input aria-label="Search projects" placeholder="Search projects…" value={search_content}
        onChange={(event) => set_search_content(event.target.value)}
        className="min-w-0 w-40 border-b border-white/20 bg-transparent py-1 text-xs text-white outline-none placeholder:text-white/35 focus:border-white/70" />
    </div>
    <div className="max-h-[38dvh] overflow-y-auto pr-1">
      {!projects.length && <p className="py-4 text-sm text-white/50">
        {search_content ? "No matching projects." : "No projects yet. Create one to get started."}
      </p>}
      {projects.map((project) => <div key={project.project_id}
        className="group flex items-center gap-2 border-b border-white/10 transition-colors hover:bg-white/5">
        <Link href={`/workspace/${encodeURIComponent(project.project_id)}`}
          className="min-w-0 flex-1 py-3 pr-2 outline-none focus-visible:ring-1 focus-visible:ring-white/70">
          <span className="block truncate text-sm font-semibold">{project.title}</span>
          <span className="mt-1 block text-xs text-white/45">
            {project.constellation.number_of_planes * project.constellation.number_of_sat_per_planes} satellites
            <span className="px-2 text-white/25">/</span>{project.constellation.altitude / 1000} km
          </span>
        </Link>
        <button type="button" aria-label={`Edit ${project.title}`} onClick={() => on_edit(project)}
          className="rounded p-2 text-white/60 transition hover:text-white focus-visible:opacity-100 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100">
          <PencilSquareIcon className="h-4 w-4" />
        </button>
        <button type="button" aria-label={`Delete ${project.title}`} onClick={() => void delete_project(project.project_id)}
          className="rounded p-2 text-white/60 transition hover:text-white focus-visible:opacity-100 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100">
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>)}
    </div>
  </section>;
}
