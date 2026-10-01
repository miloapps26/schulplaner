const { chromium } = require("playwright");
const path = require("path");

const fileUrl = "file:///" + path.resolve(__dirname, "..", "login-demo.html").replace(/\\/g, "/");

const viewports = [
  { name: "desktop", width: 1024, height: 768 },
  { name: "iphone", width: 390, height: 844 }
];

(async () => {
  const browser = await chromium.launch();
  try {
    for (const viewport of viewports) {
      const page = await browser.newPage({ viewport });
      await page.goto(fileUrl);

      const data = await page.evaluate(() => {
        const card = document.querySelector(".ci-login-card").getBoundingClientRect();
        const button = document.querySelector(".ci-login-actions .ci-button-primary").getBoundingClientRect();
        const input = document.querySelector("input.ci-input").getBoundingClientRect();
        const style = getComputedStyle(document.querySelector(".ci-login-card"));
        return {
          hasMark: !!document.querySelector(".ci-mark-img[src$='assets/milo-mark.svg']"),
          hasAppleIcon: !!document.querySelector("link[rel='apple-touch-icon'][sizes='180x180'][href$='assets/apple-touch-icon.png']"),
          hasManifest: !!document.querySelector("link[rel='manifest'][href$='site.webmanifest']"),
          cardWidth: card.width,
          buttonHeight: button.height,
          inputHeight: input.height,
          radius: parseFloat(style.borderTopLeftRadius),
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth
        };
      });

      if (!data.hasMark) throw new Error(`${viewport.name}: login card does not use official Milo mark`);
      if (!data.hasAppleIcon) throw new Error(`${viewport.name}: missing apple-touch-icon link`);
      if (!data.hasManifest) throw new Error(`${viewport.name}: missing web manifest link`);
      if (data.cardWidth > 422) throw new Error(`${viewport.name}: login card too wide: ${data.cardWidth}`);
      if (data.buttonHeight < 42) throw new Error(`${viewport.name}: login button too short: ${data.buttonHeight}`);
      if (data.inputHeight < 42) throw new Error(`${viewport.name}: login input too short: ${data.inputHeight}`);
      if (Math.abs(data.radius - 8) > 1) throw new Error(`${viewport.name}: login card radius must be 8px, got ${data.radius}`);
      if (data.overflow > 1) throw new Error(`${viewport.name}: horizontal overflow ${data.overflow}px`);

      await page.close();
    }
    console.log("Login layout regression passed.");
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});
