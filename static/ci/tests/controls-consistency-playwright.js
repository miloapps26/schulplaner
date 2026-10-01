const { chromium } = require("playwright");
const path = require("path");

const fileUrl = "file:///" + path.resolve(__dirname, "..", "controls-consistency-demo.html").replace(/\\/g, "/");

const viewports = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "small-laptop", width: 1024, height: 720 },
  { name: "mobile", width: 390, height: 844 }
];

function nearly(actual, expected, label) {
  if (Math.abs(actual - expected) > 1) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
}

(async () => {
  const browser = await chromium.launch();
  try {
    for (const viewport of viewports) {
      const page = await browser.newPage({ viewport });
      await page.goto(fileUrl);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (overflow > 1) throw new Error(`${viewport.name}: horizontal overflow ${overflow}px`);

      const controlData = await page.$$eval(
        [
          ".ci-button:not(.ci-button-block)",
          ".ci-icon-button",
          ".ci-ai-action",
          ".ci-process-step",
          "input.ci-input",
          "select.ci-input",
          ".ci-segmented",
          ".ci-input-group"
        ].join(","),
        nodes => nodes.map(node => {
          const style = getComputedStyle(node);
          const rect = node.getBoundingClientRect();
          return {
            selector: node.className || node.tagName,
            radius: parseFloat(style.borderTopLeftRadius),
            height: rect.height
          };
        })
      );

      for (const item of controlData) {
        nearly(item.radius, 6, `${viewport.name} ${item.selector} radius`);
        if (item.height < 42) throw new Error(`${viewport.name} ${item.selector} is shorter than standard controls: ${item.height}`);
      }

      const square = await page.$eval(".ci-icon-button", node => {
        const rect = node.getBoundingClientRect();
        return { width: rect.width, height: rect.height };
      });
      nearly(square.width, square.height, `${viewport.name} icon button square`);

      const innerRadius = await page.$eval(".ci-input-group input", node => parseFloat(getComputedStyle(node).borderTopLeftRadius));
      nearly(innerRadius, 0, `${viewport.name} input group inner radius`);

      const panelRadius = await page.$eval(".ci-status-panel", node => parseFloat(getComputedStyle(node).borderTopLeftRadius));
      nearly(panelRadius, 8, `${viewport.name} panel radius`);

      const metricHeight = await page.$eval(".ci-metric-input", node => node.getBoundingClientRect().height);
      if (metricHeight < 48) throw new Error(`${viewport.name}: metric input is not using the larger metric height: ${metricHeight}`);

      const tabsHeight = await page.$eval(".ci-tabs-compact", node => node.getBoundingClientRect().height);
      if (tabsHeight > 48) throw new Error(`${viewport.name}: compact tabs are too tall: ${tabsHeight}`);

      const colors = await page.evaluate(() => {
        const primary = getComputedStyle(document.querySelector(".ci-button-primary"));
        const secondary = getComputedStyle([...document.querySelectorAll(".ci-button")].find(node => !node.classList.contains("ci-button-primary") && !node.disabled));
        return { primaryBg: primary.backgroundColor, secondaryBg: secondary.backgroundColor };
      });
      if (colors.primaryBg === colors.secondaryBg) {
        throw new Error(`${viewport.name}: primary and secondary buttons should not have the same visual weight`);
      }

      const pillRadius = await page.$eval(".ci-badge", node => parseFloat(getComputedStyle(node).borderTopLeftRadius));
      if (pillRadius < 10) throw new Error(`${viewport.name}: badge is not pill-shaped`);

      await page.close();
    }
    console.log("Controls consistency regression passed.");
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});
