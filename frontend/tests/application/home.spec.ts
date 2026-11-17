import { expect, test } from "@playwright/test";

test("home waits for the background and opens projects without replacing the Earth", async ({ page }) => {
  let release_texture!: () => void;
  let is_texture_requested = false;
  const texture_gate = new Promise<void>((resolve) => { release_texture = resolve; });
  await page.route("**/planet_texture/earth_texture_hd.jpg", async (route) => {
    is_texture_requested = true;
    await texture_gate;
    await route.continue();
  });
  let project_requests = 0;
  page.on("request", (request) => { if (new URL(request.url()).pathname === "/api/projects") project_requests++; });
  try {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect.poll(() => is_texture_requested, { timeout: 30_000 }).toBeTruthy();
    await expect(page.getByRole("status", { name: "Loading background", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Get Started", exact: true })).not.toBeVisible();
    await expect(page.getByRole("heading", { name: "OPHANIM", exact: true })).not.toBeVisible();
    expect(project_requests).toBe(0);
    await page.screenshot({ path: "test-results/home-background-loading.png" });
  } finally {
    release_texture();
  }
  await expect(page.getByRole("status", { name: "Loading background", exact: true })).not.toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole("button", { name: "Get Started", exact: true })).toBeVisible();
  const canvas = await page.getByTestId("dashboard-earth").locator("canvas").elementHandle();
  expect(canvas).not.toBeNull();
  await page.screenshot({ path: "test-results/home-ready.png" });
  await page.getByRole("button", { name: "Get Started", exact: true }).click();
  await expect(page).toHaveURL(/\/#projects$/);
  await expect(page.getByRole("button", { name: "Create Project", exact: true })).toBeVisible({ timeout: 30_000 });
  expect(project_requests).toBeGreaterThan(0);
  expect(await canvas!.evaluate((node) => node.isConnected && node === document.querySelector("canvas"))).toBeTruthy();
  await expect(page.getByRole("status", { name: "Loading background", exact: true })).not.toBeVisible();
  await page.screenshot({ path: "test-results/home-projects.png" });
  await page.goBack();
  await expect(page.getByRole("button", { name: "Get Started", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Projects", exact: true }).click();
  await expect(page.getByRole("button", { name: "Create Project", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "OPHANIM", exact: true }).click();
  await expect(page.getByRole("button", { name: "Get Started", exact: true })).toBeVisible();
  expect(await canvas!.evaluate((node) => node.isConnected)).toBeTruthy();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Get Started", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test("a failed background load can be retried", async ({ page }) => {
  let fail_texture = true;
  await page.route("**/planet_texture/earth_texture_hd.jpg", async (route) => {
    if (fail_texture) await route.abort("failed");
    else await route.continue();
  });
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("button", { name: "Retry background", exact: true })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("button", { name: "Get Started", exact: true })).not.toBeVisible();
  fail_texture = false;
  await page.getByRole("button", { name: "Retry background", exact: true }).click();
  await expect(page.getByRole("button", { name: "Get Started", exact: true })).toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole("status", { name: "Loading background", exact: true })).not.toBeVisible();
});
