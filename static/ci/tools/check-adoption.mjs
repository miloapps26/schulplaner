#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const sourceRoot = path.resolve(__dirname, "..");
const targetRoot = path.resolve(process.argv[2] || process.cwd());
const sourceVersion = readText(path.join(sourceRoot, "VERSION")).trim();
const versionPattern = sourceVersion.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const failures = [];
const warnings = [];

function readText(file) {
  return fs.readFileSync(file, "utf8").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function exists(file) {
  return fs.existsSync(file);
}

function rel(file) {
  return path.relative(targetRoot, file).replace(/\\/g, "/") || ".";
}

function fail(id, message, file) {
  failures.push({ id, message, file: file ? rel(file) : undefined });
}

function warn(id, message, file) {
  warnings.push({ id, message, file: file ? rel(file) : undefined });
}

function walk(dir, predicate, out = []) {
  if (!exists(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    const normalized = full.replace(/\\/g, "/");
    if (entry.isDirectory()) {
      if (/\/(node_modules|\.git|dist|build|\.venv|__pycache__|data|outputs)\b/.test(normalized)) continue;
      walk(full, predicate, out);
    } else if (predicate(full)) {
      out.push(full);
    }
  }
  return out;
}

function candidateCiDirs() {
  return [
    path.join(targetRoot, "static", "ci"),
    path.join(targetRoot, "public", "milo"),
    path.join(targetRoot, "public", "ci"),
    path.join(targetRoot, "assets", "ci"),
    path.join(targetRoot, "ci")
  ].filter((dir) => exists(path.join(dir, "VERSION")) || exists(path.join(dir, "ci-manifest.json")));
}

function classHas(html, className) {
  return new RegExp('class=["\'][^"\']*\\b' + className + '\\b').test(html);
}

function inputMissingClass(html) {
  const inputs = html.match(/<input\b[^>]*>/gi) || [];
  return inputs.filter((tag) => !/type=["']hidden["']/i.test(tag) && !/class=["'][^"']*\bci-input\b/i.test(tag));
}

function submitButtonIsPrimary(html) {
  const buttons = html.match(/<button\b[^>]*>/gi) || [];
  return buttons.some((tag) => /type=["']submit["']/i.test(tag) && /class=["'][^"']*\bci-button\b/i.test(tag) && /class=["'][^"']*\bci-button-primary\b/i.test(tag) && /class=["'][^"']*\bci-button-block\b/i.test(tag));
}

const ciDirs = candidateCiDirs();
if (ciDirs.length === 0) {
  fail("ci-missing", "No vendored Milo CI directory found. Expected static/ci, public/milo, public/ci, assets/ci or ci.");
} else {
  for (const ciDir of ciDirs) {
    const versionFile = path.join(ciDir, "VERSION");
    const manifestFile = path.join(ciDir, "ci-manifest.json");
    const version = exists(versionFile) ? readText(versionFile).trim() : "";
    if (version !== sourceVersion) {
      fail("ci-version", "Vendored Milo CI VERSION is " + (version || "missing") + ", expected " + sourceVersion + ".", versionFile);
    }
    if (!exists(manifestFile)) {
      fail("ci-manifest", "Vendored ci-manifest.json is missing.", manifestFile);
    } else {
      const manifest = JSON.parse(readText(manifestFile));
      if (manifest.ciVersion !== sourceVersion) {
        fail("ci-manifest-version", "Vendored ci-manifest.json ciVersion is " + manifest.ciVersion + ", expected " + sourceVersion + ".", manifestFile);
      }
    }
    for (const required of [
      "tokens.css",
      "ci.css",
      "LOGIN.md",
      "assets/milo-mark.svg",
      "assets/favicon.svg",
      "assets/favicon-32.png",
      "assets/favicon.ico",
      "assets/apple-touch-icon.png"
    ]) {
      if (!exists(path.join(ciDir, required))) fail("ci-required-file", "Missing vendored Milo CI file: " + required + ".", path.join(ciDir, required));
    }
    const ciCss = path.join(ciDir, "ci.css");
    if (exists(ciCss) && !/\[hidden\]\s*\{\s*display:\s*none\s*!important;\s*\}/.test(readText(ciCss))) {
      fail("native-hidden-wins", "ci.css does not contain the required [hidden] display override.", ciCss);
    }
  }
}

const htmlFiles = walk(targetRoot, (full) => /\.html?$/i.test(full) && !full.replace(/\\/g, "/").includes("/static/ci/") && !full.replace(/\\/g, "/").includes("/public/milo/"));
const cssFiles = walk(targetRoot, (full) => /\.css$/i.test(full) && !full.replace(/\\/g, "/").includes("/static/ci/") && !full.replace(/\\/g, "/").includes("/public/milo/"));
const appTextFiles = walk(targetRoot, (full) => /\.(html?|css|js|jsx|ts|tsx|py|md)$/i.test(full) && !full.replace(/\\/g, "/").includes("/static/ci/") && !full.replace(/\\/g, "/").includes("/public/milo/"));
const projectText = appTextFiles.map((full) => readText(full)).join("\n");
const hasAuth = /MILO_AUTH_REQUIRED|MILO_AUTH_USERS|\/api\/login|#login-form|name=["']password["']|autocomplete=["']current-password["']/i.test(projectText);

for (const htmlFile of htmlFiles) {
  const html = readText(htmlFile);
  const name = path.basename(htmlFile).toLowerCase();
  const isLoginPage = name.includes("login") || /id=["']login-form["']|action=["'][^"']*login/i.test(html);
  const isCiDemo = /Milo CI Demo|ci-manifest/.test(html);

  if (!isCiDemo) {
    if (!new RegExp("favicon\\.svg\\?v=" + versionPattern).test(html)) fail("favicon-current", "HTML shell does not link the current versioned Milo SVG favicon.", htmlFile);
    if (!new RegExp("favicon-32\\.png\\?v=" + versionPattern).test(html)) fail("favicon-png-current", "HTML shell does not link the current versioned Milo PNG favicon.", htmlFile);
    if (!new RegExp("favicon\\.ico\\?v=" + versionPattern).test(html)) fail("favicon-ico-current", "HTML shell does not link the current versioned Milo ICO fallback.", htmlFile);
  }

  if (classHas(html, "ci-mark") && !/class=["'][^"']*\bci-mark-img\b[^"']*["'][^>]+src=["'][^"']*assets\/milo-mark\.svg/i.test(html)) {
    fail("milo-mark-consistency", "ci-mark is used without the official assets/milo-mark.svg image.", htmlFile);
  }

  if (classHas(html, "ci-topbar") && (!classHas(html, "ci-topbar-meta") || !classHas(html, "ci-version"))) {
    fail("app-version-topbar", "Topbar must include ci-topbar-meta and ci-version.", htmlFile);
  }

  if (isLoginPage) {
    if (classHas(html, "ci-topbar")) fail("milo-login-layout", "Login pages must not use the normal app topbar.", htmlFile);
    for (const required of ["ci-login-page", "ci-login-card", "ci-login-title", "ci-login-form", "ci-login-actions"]) {
      if (!classHas(html, required)) fail("milo-login-layout", "Login page is missing ." + required + ".", htmlFile);
    }
    if (!/class=["'][^"']*\bci-mark-img\b[^"']*["'][^>]+src=["'][^"']*assets\/milo-mark\.svg/i.test(html)) {
      fail("milo-login-layout", "Login card must use the official Milo mark image.", htmlFile);
    }
    if (inputMissingClass(html).length > 0) fail("milo-login-controls", "Login inputs must use class ci-input.", htmlFile);
    if (!submitButtonIsPrimary(html)) fail("milo-login-controls", "Login submit button must use ci-button ci-button-primary ci-button-block.", htmlFile);
  }
}

if (hasAuth) {
  const loginPages = htmlFiles.filter((full) => /login/i.test(path.basename(full)) || /id=["']login-form["']/.test(readText(full)));
  if (loginPages.length === 0) fail("auth-login-page", "Project appears to use auth but no login page was found.");
  const appShells = htmlFiles.filter((full) => !/login/i.test(path.basename(full)) && classHas(readText(full), "ci-topbar"));
  if (appShells.length > 0 && !appShells.some((full) => classHas(readText(full), "ci-logout-button") || /logout/i.test(readText(full)))) {
    warn("auth-logout", "Authenticated project has topbar shells but no visible logout action was detected.");
  }
}

for (const cssFile of cssFiles) {
  const css = readText(cssFile);
  if (/\.login-(main|panel|form)\b/.test(css)) {
    warn("legacy-login-css", "Local .login-* CSS exists. Remove it once login pages use Milo ci-login-* components.", cssFile);
  }
  if (/border-radius\s*:\s*(1[0-9]|[2-9][0-9])px/.test(css)) {
    warn("control-radius", "Local CSS contains large border-radius values; verify against Milo control/container radii.", cssFile);
  }
}

const report = {
  target: targetRoot,
  sourceVersion,
  ciDirs: ciDirs.map(rel),
  checkedHtmlFiles: htmlFiles.map(rel),
  failures,
  warnings
};

console.log(JSON.stringify(report, null, 2));
if (failures.length > 0) process.exitCode = 1;