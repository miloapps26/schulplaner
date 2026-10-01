const { chromium } = require("playwright");
const path = require("path");
const { pathToFileURL } = require("url");

(async () => {
  const browser = await chromium.launch();
  const pagePath = path.resolve(__dirname, "..", "workflow-resilience-demo.html");
  const viewports = [
    { name: "desktop", width: 1440, height: 980 },
    { name: "laptop", width: 1180, height: 760 },
    { name: "mobile", width: 390, height: 844 }
  ];

  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport });
    await page.goto(pathToFileURL(pagePath).href);

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (overflow > 1) throw new Error(viewport.name + ": horizontal overflow " + overflow);

    const preview = await page.locator(".ci-preview-frame").boundingBox();
    const status = await page.locator(".ci-status-panel").boundingBox();
    const actions = await page.locator(".ci-result-toolbar").boundingBox();
    if (!preview || preview.width < 260 || preview.height < 180) throw new Error(viewport.name + ": preview frame is unstable");
    if (!status || status.height < 44) throw new Error(viewport.name + ": status panel missing");
    if (!actions || actions.height < 44) throw new Error(viewport.name + ": result actions missing");

    const disabledPrimary = await page.locator(".ci-process-nav .ci-button-primary").isDisabled();
    if (!disabledPrimary) throw new Error(viewport.name + ": running job primary action is not disabled");

    const metaCount = await page.locator(".ci-job-meta div").count();
    if (metaCount < 4) throw new Error(viewport.name + ": job metadata incomplete");

    const buttons = await page.locator(".ci-candidate .ci-button").allTextContents();
    for (const label of ["Accept", "Reject", "Compare"]) {
      if (!buttons.includes(label)) throw new Error(viewport.name + ": missing suggestion action " + label);
    }

    await page.close();
  }

  await browser.close();
})().catch(async (error) => {
  console.error(error);
  process.exit(1);
});
