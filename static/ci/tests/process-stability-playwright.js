const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');

const root = path.resolve(__dirname, '..');
const demoUrl = pathToFileURL(path.join(root, 'process-stability-demo.html')).href;
const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'small-laptop', width: 1024, height: 720 },
  { name: 'mobile', width: 390, height: 844 }
];
const states = ['short', 'long', 'suggestion', 'loading', 'error', 'result'];
const tolerance = 2;

function closeEnough(a, b, delta = tolerance) {
  return Math.abs(a - b) <= delta;
}

async function rect(page, selector) {
  return await page.locator(selector).boundingBox();
}

async function metrics(page) {
  return await page.evaluate(() => ({
    scrollX: window.scrollX,
    scrollY: window.scrollY,
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    bodyClientWidth: document.body.clientWidth
  }));
}

(async () => {
  const browser = await chromium.launch();
  try {
    for (const viewport of viewports) {
      const page = await browser.newPage({ viewport });
      await page.goto(demoUrl);
      await page.waitForLoadState('load');

      const navBase = await rect(page, '[data-stability="nav"]');
      const previewBase = await rect(page, '[data-stability="preview"]');
      const statusBase = await rect(page, '[data-stability="status"]');
      const suggestionBase = await rect(page, '[data-stability="suggestion"]');
      const startMetrics = await metrics(page);

      if (startMetrics.scrollWidth > startMetrics.clientWidth + 1) {
        throw new Error(`${viewport.name}: initial horizontal overflow`);
      }

      for (const state of states) {
        await page.locator(`[data-state-button="${state}"]`).click();
        await page.waitForTimeout(80);
        const navNow = await rect(page, '[data-stability="nav"]');
        const previewNow = await rect(page, '[data-stability="preview"]');
        const statusNow = await rect(page, '[data-stability="status"]');
        const suggestionNow = await rect(page, '[data-stability="suggestion"]');
        const nowMetrics = await metrics(page);

        if (!closeEnough(navNow.x, navBase.x) || !closeEnough(navNow.y, navBase.y) || !closeEnough(navNow.width, navBase.width)) {
          throw new Error(`${viewport.name}/${state}: process navigation moved`);
        }
        if (!closeEnough(previewNow.x, previewBase.x) || !closeEnough(previewNow.width, previewBase.width) || !closeEnough(previewNow.height, previewBase.height)) {
          throw new Error(`${viewport.name}/${state}: preview changed size or horizontal position`);
        }
        if (!closeEnough(statusNow.width, statusBase.width) || statusNow.height < statusBase.height - tolerance) {
          throw new Error(`${viewport.name}/${state}: status area collapsed`);
        }
        if (!closeEnough(suggestionNow.width, suggestionBase.width) || suggestionNow.height < suggestionBase.height - tolerance) {
          throw new Error(`${viewport.name}/${state}: suggestion area collapsed`);
        }
        if (nowMetrics.scrollX !== 0 || nowMetrics.scrollWidth > nowMetrics.clientWidth + 1) {
          throw new Error(`${viewport.name}/${state}: horizontal overflow or scroll jump`);
        }
      }

      await page.keyboard.press('Control+Equal');
      await page.keyboard.press('Control+Equal');
      await page.locator('[data-state-button="long"]').click();
      await page.waitForTimeout(80);
      const zoomMetrics = await metrics(page);
      if (zoomMetrics.scrollWidth > zoomMetrics.clientWidth + 1) {
        throw new Error(`${viewport.name}: horizontal overflow after browser zoom`);
      }

      await page.close();
    }
  } finally {
    await browser.close();
  }
  console.log('Process stability Playwright regression passed.');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
