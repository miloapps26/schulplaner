const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');

const root = path.resolve(__dirname, '..');
const demoUrl = pathToFileURL(path.join(root, 'dark-mode-demo.html')).href;
const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'small-laptop', width: 1024, height: 720 },
  { name: 'mobile', width: 390, height: 844 }
];

(async () => {
  const browser = await chromium.launch();
  try {
    for (const viewport of viewports) {
      const page = await browser.newPage({ viewport });
      await page.goto(demoUrl);
      await page.waitForLoadState('load');
      const result = await page.evaluate(() => {
        const styles = getComputedStyle(document.body);
        return {
          bg: styles.backgroundColor,
          text: styles.color,
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
          mark: !!document.querySelector('.ci-mark-img'),
          aiAction: !!document.querySelector('.ci-ai-action[aria-label][title]'),
          status: !!document.querySelector('.ci-status-panel[role="status"]')
        };
      });
      if (result.scrollWidth > result.clientWidth + 1) throw new Error(`${viewport.name}: horizontal overflow`);
      if (!result.mark || !result.aiAction || !result.status) throw new Error(`${viewport.name}: required dark demo affordance missing`);
      if (!result.bg.includes('15, 20, 26')) throw new Error(`${viewport.name}: default dark background token not active (${result.bg})`);

      await page.evaluate(() => document.documentElement.setAttribute('data-ci-theme', 'light'));
      const lightBg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      if (!lightBg.includes('244, 247, 248')) throw new Error(`${viewport.name}: light opt-in background token not active (${lightBg})`);
      await page.close();
    }
  } finally {
    await browser.close();
  }
  console.log('Dark mode Playwright smoke test passed.');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
