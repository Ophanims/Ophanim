"use client";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import type { Project } from "../../contracts/generated";
import schema from "../../contracts/schema.json";
import { create_initial_project } from "../../lib/InitialForm";
import { FormSection, ProjectEditorField, FIELD_STYLE } from "./ProjectEditorFields";
import { PROJECT_FORM_SECTIONS } from "./project_form_fields";
import { useProjectConfig } from "./useProjectConfig";
import styles from "./ProjectEditorDialog.module.css";

interface ProjectEditorDialogProps {
  project: Project | null;
  on_close: () => void;
  on_save: (project: Project) => void;
}

export default function ProjectEditorDialog({ project, on_close, on_save }: ProjectEditorDialogProps) {
  const [initial_project] = useState(() => project ?? create_initial_project());
  const { form, loading, error, update_field, handle_submit } = useProjectConfig(initial_project, on_save);
  const panel_ref = useRef<HTMLDivElement>(null);
  const form_id = useId();
  const title_id = useId();
  const is_editing = !!project?.project_id;
  const title = is_editing ? "Edit Project" : "Create Project";

  useEffect(() => {
    const previous_focus = document.activeElement;
    panel_ref.current?.querySelector<HTMLInputElement>('input[name="title"]')?.focus();
    return () => { if (previous_focus instanceof HTMLElement && previous_focus.isConnected) previous_focus.focus(); };
  }, []);

  const handle_key_down = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape" && !loading) { event.preventDefault(); on_close(); }
    if (event.key !== "Tab") return;
    const elements = Array.from(panel_ref.current?.querySelectorAll<HTMLElement>(
      'button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), summary, [tabindex="0"]',
    ) ?? []).filter((element) => element.getClientRects().length > 0);
    const first = elements[0], last = elements[elements.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  };

  return <div className="fixed inset-0 z-40 flex items-center justify-center p-3 sm:p-6">
    <button aria-label="Dismiss project editor" disabled={loading} onClick={on_close} tabIndex={-1}
      className="absolute inset-0 bg-black/35 backdrop-blur-sm" />
    <div ref={panel_ref} role="dialog" aria-modal="true" aria-labelledby={title_id} onKeyDown={handle_key_down}
      className={`${styles.panel} relative flex max-h-[92dvh] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-white/30 bg-black/65 text-white shadow-2xl backdrop-blur-xl`}>
      <header className="flex shrink-0 items-center justify-between gap-4 border-b border-white/15 px-5 py-5 sm:px-7">
        <h2 id={title_id} className="text-lg font-semibold">{title}</h2>
        <button type="button" disabled={loading} onClick={on_close}
          className="rounded-md border border-white/30 px-3 py-1.5 text-sm transition hover:bg-white/10 disabled:opacity-50">Close</button>
      </header>
      <div className="min-h-0 overflow-y-auto px-4 py-3 sm:px-6">
        <form id={form_id} onSubmit={(event) => { event.preventDefault(); void handle_submit(); }} className="space-y-2">
          <fieldset disabled={loading}>
            <FormSection title="Basic">
              <label className="flex flex-col gap-1.5 text-xs text-white/75">ID
                <input value={form.project_id || "Auto-generated"} disabled className={FIELD_STYLE} />
              </label>
              <label className="flex flex-col gap-1.5 text-xs text-white/75">Name
                <input name="title" required value={form.title} onChange={(event) => update_field(["title"], event.target.value)} className={FIELD_STYLE} />
              </label>
              <label className="flex flex-col gap-1.5 text-xs text-white/75">Algorithm
                <select name="algorithm" value={form.algorithm} onChange={(event) => update_field(["algorithm"], event.target.value)} className={FIELD_STYLE}>
                  {schema.$defs.Project.properties.algorithm.enum.map((algorithm) =>
                    <option key={algorithm} value={algorithm}>{algorithm === "ophanim" ? "Ophanim" : algorithm.toUpperCase()}</option>)}
                </select>
              </label>
              <label className="flex flex-col gap-1.5 text-xs text-white/75">Description
                <textarea name="description" rows={2} value={form.description} className={`${FIELD_STYLE} resize-y`}
                  onChange={(event) => update_field(["description"], event.target.value)} placeholder="Optional project description" />
              </label>
            </FormSection>
            {PROJECT_FORM_SECTIONS.map((section) => <FormSection key={section.title} title={section.title}>
              {section.fields.map((field) => <ProjectEditorField key={field.path.join(".")} field={field} form={form} update_field={update_field} />)}
            </FormSection>)}
          </fieldset>
        </form>
      </div>
      <footer className="shrink-0 border-t border-white/15 bg-black/35 px-5 py-4 sm:px-7">
        {error && <p role="alert" className="mb-3 text-sm text-red-200">{error}</p>}
        <div className="flex items-center gap-3">
          <button form={form_id} type="submit" disabled={loading}
            className="rounded-md bg-white px-4 py-2 text-sm font-semibold text-black transition hover:bg-white/85 disabled:opacity-50">
            {loading ? "Saving…" : is_editing ? "Update Project" : "Create Project"}
          </button>
          <button type="button" disabled={loading} onClick={on_close}
            className="rounded-md border border-white/30 px-4 py-2 text-sm transition hover:bg-white/10 disabled:opacity-50">Cancel</button>
          <span className="ml-auto hidden text-xs text-white/35 sm:inline">Times use your local time zone</span>
        </div>
      </footer>
    </div>
  </div>;
}
