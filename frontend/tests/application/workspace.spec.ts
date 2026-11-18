import { expect, test } from "@playwright/test";
import { randomUUID } from "node:crypto";
import template from "../../src/features/simulation/contracts/default_project.json";
import type { Project } from "../../src/features/simulation/contracts/generated";
import { validate_contract } from "../../src/features/simulation/communication/contract_validation";
import { route_path } from "../../src/features/simulation/communication/config";

for (const algorithm of ["ophanim", "geometry", "phoenix"] as const) {
test(`${algorithm}: project workspace initializes, plays, changes views and replays its record`, async ({ page, request }) => {
  const project = validate_contract<Project>(structuredClone(template), "Project");
  project.project_id = `browser_${randomUUID().replaceAll("-", "")}`;
  project.algorithm = algorithm;
  project.title = "Browser integration check";
  project.constellation.number_of_planes = 2;
  project.constellation.number_of_sat_per_planes = 3;
  project.experiment.time_slot = algorithm === "phoenix" ? 0.5 : 30;
  project.experiment.end_time = algorithm === "phoenix"
    ? "2025-12-01T00:00:01.300000+00:00" : "2025-12-01T00:01:05+00:00";
  project.ground_stations = [{ id: "station", project_id: project.project_id, name: "Station", altitude_m: 0, location: { lat: 0, lon: 0 } }];
  project.rois = [{ id: "region", project_id: project.project_id, name: "ROI", length: 1000, width: 500, location: { lat: 0, lon: 0 } }];
  const response = await request.post(route_path("save_project"), { data: project });
  expect(response.ok(), await response.text()).toBeTruthy();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  try {
    await page.goto(`/workspace/${project.project_id}`);
    await expect(page.getByRole("heading", { name: project.title })).toBeVisible();
    await page.getByRole("button", { name: "Record", exact: true }).click();
    const picker = page.getByRole("dialog", { name: "Record", exact: true });
    await expect(picker.getByText("No records for this project yet.", { exact: false })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(picker).not.toBeVisible();
    await page.getByRole("button", { name: "Simulation", exact: true }).click();
    await expect(page.getByRole("button", { name: "Initialization", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Clear Datasets", exact: true })).toHaveCount(0);
    await page.getByRole("button", { name: "Launch Simulation", exact: true }).click();
    await expect(page.getByRole("button", { name: "Play simulation", exact: true })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: "Play simulation", exact: true }).click();
    await expect(page.getByText(project.experiment.end_time, { exact: false })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: "Visualization", exact: true }).click();
    await page.getByRole("button", { name: "Geometry View", exact: true }).click();
    await expect(page.locator("main canvas")).toBeVisible();
    await page.getByRole("button", { name: "Visualization", exact: true }).click();
    await page.getByRole("button", { name: "Map View", exact: true }).click();
    await expect(page.locator(".leaflet-container")).toBeVisible();
    await page.screenshot({ path: "test-results/application-map.png" });
    // Record metadata exposes identifiers; select by the backend contract when rendering is concise.
    const records_response = await request.get(route_path("list_records"));
    const records = (await records_response.json()).data as Array<{ record_id: string; project_id: string }>;
    const record = records.find((record) => record.project_id === project.project_id);
    expect(record).toBeDefined();
    const record_response = await request.get(route_path("get_record", { record_id: record!.record_id }));
    const record_window = (await record_response.json()).data;
    expect(record_window.record.status).toBe("completed");
    expect(record_window.record.frame_count).toBe(4);
    expect(record_window.record.algorithm).toBe(algorithm);
    await page.getByRole("button", { name: "Record", exact: true }).click();
    await expect(picker).toBeVisible();
    await expect(picker.locator("tbody tr")).toHaveCount(1);
    await expect(picker.getByText(record!.record_id, { exact: true })).toBeVisible();
    await page.screenshot({ path: `test-results/workspace-record-picker-${algorithm}.png` });
    await page.locator(".leaflet-container").evaluate((element) => element.setAttribute("data-replay-view", "preserved"));
    await page.route(`**/api/records/${record!.record_id}?*`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      await route.continue();
    });
    await picker.getByRole("button", { name: "Replay", exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`record_id=${record!.record_id}`));
    await expect(page.getByRole("status").filter({ hasText: "Loading recording" })).toBeVisible();
    await expect(page.getByRole("heading", { name: project.title, includeHidden: true })).toBeVisible();
    await expect(page.locator('[data-replay-view="preserved"]')).toBeVisible();
    await expect(page.getByText(`Replay: ${record!.record_id}`, { exact: false })).toBeVisible();
    await expect(page.locator('[data-replay-view="preserved"]')).toBeVisible();
    await expect(page.getByRole("region", { name: "Record playback", exact: true })).toHaveCSS("background-color", "rgb(13, 13, 13)");
    await expect(page.getByRole("button", { name: "Play playback", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Play playback", exact: true })).toBeInViewport();
    await page.screenshot({ path: `test-results/workspace-record-replay-${algorithm}.png` });
    const slider = page.getByRole("slider", { name: "Frame", exact: true });
    await expect(slider).toHaveAttribute("max", "3");
    await slider.press("End");
    await slider.press("ArrowLeft");
    await expect(slider).toHaveValue("2");
    await page.getByRole("button", { name: "Play playback", exact: true }).click();
    await expect(slider).toHaveValue("3");
    await expect(page.getByRole("button", { name: "Play playback", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Parameters", exact: true })).toBeDisabled();
    await page.getByRole("link", { name: "Return to live workspace", exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/workspace/${project.project_id}$`));
    await expect(page.getByText("Record playback", { exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Parameters", exact: true })).toBeEnabled();
    expect(errors).toEqual([]);
  } finally {
    await page.goto("/records").catch(() => undefined);
    const response = await request.get(route_path("list_records")).catch(() => null);
    const records = response?.ok() ? (await response.json()).data as Array<{ record_id: string; project_id: string }> : [];
    for (const record of records.filter((record) => record.project_id === project.project_id)) {
      await request.delete(route_path("delete_record", { record_id: record.record_id })).catch(() => undefined);
    }
    await request.delete(route_path("delete_project", { project_id: project.project_id })).catch(() => undefined);
  }
});

}
