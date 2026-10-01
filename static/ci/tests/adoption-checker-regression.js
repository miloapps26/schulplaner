const { spawnSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const checker = path.resolve(__dirname, "..", "tools", "check-adoption.mjs");
const source = path.resolve(__dirname, "..");
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "milo-adoption-"));
const sourceVersion = fs.readFileSync(path.join(source, "VERSION"), "utf8").trim();

function copyFile(relative) {
  const from = path.join(source, relative);
  const to = path.join(temp, "static", "ci", relative);
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(from, to);
}

for (const relative of [
  "VERSION",
  "ci-manifest.json",
  "tokens.css",
  "ci.css",
  "LOGIN.md",
  "assets/milo-mark.svg",
  "assets/favicon.svg",
  "assets/favicon-32.png",
  "assets/favicon.ico",
  "assets/apple-touch-icon.png"
]) {
  copyFile(relative);
}

fs.mkdirSync(path.join(temp, "static"), { recursive: true });
fs.writeFileSync(path.join(temp, "static", "login.html"), `<!doctype html>
<html lang="de">
<head>
  <link rel="icon" href="/static/ci/assets/favicon.svg?v=${sourceVersion}" type="image/svg+xml">
  <link rel="icon" href="/static/ci/assets/favicon-32.png?v=${sourceVersion}" sizes="32x32" type="image/png">
  <link rel="shortcut icon" href="/static/ci/assets/favicon.ico?v=${sourceVersion}">
</head>
<body>
  <div class="ci-app">
    <header class="ci-topbar"><div class="ci-version">v0.1.0</div></header>
    <form id="login-form">
      <input name="username">
      <input name="password" type="password" autocomplete="current-password">
      <button class="ci-button" type="submit">Anmelden</button>
    </form>
  </div>
</body>
</html>`);

const bad = spawnSync(process.execPath, [checker, temp], { encoding: "utf8" });
if (bad.status === 0) {
  throw new Error("Checker did not fail for legacy login markup.");
}
if (!bad.stdout.includes("milo-login-layout") || !bad.stdout.includes("milo-login-controls")) {
  throw new Error("Checker did not report expected login adoption failures.\n" + bad.stdout);
}

fs.writeFileSync(path.join(temp, "static", "login.html"), `<!doctype html>
<html lang="de">
<head>
  <link rel="icon" href="/static/ci/assets/favicon.svg?v=${sourceVersion}" type="image/svg+xml">
  <link rel="icon" href="/static/ci/assets/favicon-32.png?v=${sourceVersion}" sizes="32x32" type="image/png">
  <link rel="shortcut icon" href="/static/ci/assets/favicon.ico?v=${sourceVersion}">
</head>
<body>
  <main class="ci-login-page">
    <section class="ci-login-card">
      <div class="ci-mark" aria-hidden="true"><img class="ci-mark-img" src="/static/ci/assets/milo-mark.svg" alt=""></div>
      <p class="ci-section-kicker">ZUGANG</p>
      <h1 class="ci-login-title">Anmelden</h1>
      <p class="ci-login-copy">Bitte anmelden.</p>
      <form class="ci-login-form" id="login-form">
        <label class="ci-field"><span class="ci-label">Benutzername</span><input class="ci-input" name="username" autocomplete="username"></label>
        <label class="ci-field"><span class="ci-label">Passwort</span><input class="ci-input" name="password" type="password" autocomplete="current-password"></label>
        <div class="ci-login-actions"><button class="ci-button ci-button-primary ci-button-block" type="submit">Anmelden</button></div>
      </form>
    </section>
  </main>
</body>
</html>`);

const good = spawnSync(process.execPath, [checker, temp], { encoding: "utf8" });
if (good.status !== 0) {
  throw new Error("Checker failed for migrated login markup.\n" + good.stdout + good.stderr);
}

console.log("Milo adoption checker regression passed.");