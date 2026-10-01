const topStatus = document.querySelector("#top-status");
const brandSubtitle = document.querySelector("#brand-subtitle");
const metrics = document.querySelector("#metrics");
const channels = document.querySelector("#channels");
const configState = document.querySelector("#config-state");
const pollCopy = document.querySelector("#poll-copy");
const lastResult = document.querySelector("#last-result");
const runs = document.querySelector("#runs");
const days = document.querySelector("#days");
const timetable = document.querySelector("#timetable");
const activityLog = document.querySelector("#activity-log");
const activityCount = document.querySelector("#activity-count");
const checkNow = document.querySelector("#check-now");
const refreshTimetable = document.querySelector("#refresh-timetable");
const snapshotStamp = document.querySelector("#snapshot-stamp");
const profileContext = document.querySelector("#profile-context");
const settingsForm = document.querySelector("#settings-form");
const pollInterval = document.querySelector("#poll-interval");
const transitPollInterval = document.querySelector("#transit-poll-interval");
const emailRecipients = document.querySelector("#email-recipients");
const daySwitch = document.querySelector("#day-switch");
const tenantSelect = document.querySelector("#tenant-select");
const tenantForm = document.querySelector("#tenant-form");
const tenantNew = document.querySelector("#tenant-new");
const tenantSendInvite = document.querySelector("#tenant-send-invite");
const tenantSaveState = document.querySelector("#tenant-save-state");
const tenantId = document.querySelector("#tenant-id");
const tenantName = document.querySelector("#tenant-name");
const tenantParentEmail = document.querySelector("#tenant-parent-email");
const tenantActive = document.querySelector("#tenant-active");
const tenantStudentFirstName = document.querySelector("#tenant-student-first-name");
const tenantStudentLastInitial = document.querySelector("#tenant-student-last-initial");
const tenantSchoolLabel = document.querySelector("#tenant-school-label");
const tenantClassLabel = document.querySelector("#tenant-class-label");
const tenantWebuntisServer = document.querySelector("#tenant-webuntis-server");
const tenantWebuntisSchool = document.querySelector("#tenant-webuntis-school");
const tenantWebuntisElementType = document.querySelector("#tenant-webuntis-element-type");
const tenantWebuntisElementId = document.querySelector("#tenant-webuntis-element-id");
const tenantWebuntisClassName = document.querySelector("#tenant-webuntis-class-name");
const tenantWebuntisSchoolNumber = document.querySelector("#tenant-webuntis-school-number");
const tenantEmailRecipients = document.querySelector("#tenant-email-recipients");
const tenantInviteResult = document.querySelector("#tenant-invite-result");
const loginForm = document.querySelector("#login-form");
const loginUsername = document.querySelector("#login-username");
const loginPassword = document.querySelector("#login-password");
const loginError = document.querySelector("#login-error");
const oidcLogin = document.querySelector("#oidc-login");
const legacyLoginCopy = document.querySelector("#legacy-login-copy");
const logoutButton = document.querySelector("#logout-button");
const setupForm = document.querySelector("#setup-form");
const setupUsername = document.querySelector("#setup-username");
const setupPassword = document.querySelector("#setup-password");
const setupError = document.querySelector("#setup-error");
const setupProfileContext = document.querySelector("#setup-profile-context");
const homeworkList = document.querySelector("#homework-list");
const homeworkForm = document.querySelector("#homework-form");
const homeworkText = document.querySelector("#homework-text");
const homeworkSubject = document.querySelector("#homework-subject");
const homeworkDueDate = document.querySelector("#homework-due-date");
const homeworkStamp = document.querySelector("#homework-stamp");
const homeworkSummary = document.querySelector("#homework-summary");
const refreshHomework = document.querySelector("#refresh-homework");
const examsList = document.querySelector("#exams-list");
const examsStamp = document.querySelector("#exams-stamp");
const examsSummary = document.querySelector("#exams-summary");
const refreshExams = document.querySelector("#refresh-exams");
const transitStamp = document.querySelector("#transit-stamp");
const transitDaySwitch = document.querySelector("#transit-day-switch");
const transitWarnings = document.querySelector("#transit-warnings");
const transitRecommendations = document.querySelector("#transit-recommendations");
const transitOutbound = document.querySelector("#transit-outbound");
const transitReturn = document.querySelector("#transit-return");
const refreshTransit = document.querySelector("#refresh-transit");
const transitDayDetails = document.querySelector("#transit-day-details");
const transitFullCount = document.querySelector("#transit-full-count");
const manualLessonForm = document.querySelector("#manual-lesson-form");
const manualLessonTitle = document.querySelector("#manual-lesson-title");
const manualLessonRepeat = document.querySelector("#manual-lesson-repeat");
const manualLessonWeekday = document.querySelector("#manual-lesson-weekday");
const manualLessonWeekdayField = document.querySelector("#manual-lesson-weekday-field");
const manualLessonDate = document.querySelector("#manual-lesson-date");
const manualLessonDateField = document.querySelector("#manual-lesson-date-field");
const manualLessonStart = document.querySelector("#manual-lesson-start");
const manualLessonEnd = document.querySelector("#manual-lesson-end");
const manualLessonRoom = document.querySelector("#manual-lesson-room");
const manualLessonNote = document.querySelector("#manual-lesson-note");
const manualLessonList = document.querySelector("#manual-lesson-list");
const manualLessonSummary = document.querySelector("#manual-lesson-summary");
const parentProfileForm = document.querySelector("#parent-profile-form");
const parentProfileContext = document.querySelector("#parent-profile-context");
const parentProfileState = document.querySelector("#parent-profile-state");
const parentWebuntisServer = document.querySelector("#parent-webuntis-server");
const parentWebuntisSchool = document.querySelector("#parent-webuntis-school");
const parentWebuntisUsername = document.querySelector("#parent-webuntis-username");
const parentWebuntisPassword = document.querySelector("#parent-webuntis-password");
const parentWebuntisAppSecret = document.querySelector("#parent-webuntis-app-secret");
const parentWebuntisElementType = document.querySelector("#parent-webuntis-element-type");
const parentWebuntisElementId = document.querySelector("#parent-webuntis-element-id");
const parentWebuntisClassName = document.querySelector("#parent-webuntis-class-name");
const parentWebuntisSchoolNumber = document.querySelector("#parent-webuntis-school-number");
const parentTransitOutboundOrigins = document.querySelector("#parent-transit-outbound-origins");
const parentTransitOutboundDestinations = document.querySelector("#parent-transit-outbound-destinations");
const parentTransitReturnOrigins = document.querySelector("#parent-transit-return-origins");
const parentTransitReturnDestinations = document.querySelector("#parent-transit-return-destinations");
const parentTransitArriveBefore = document.querySelector("#parent-transit-arrive-before");
const parentTransitArriveWindow = document.querySelector("#parent-transit-arrive-window");
const parentTransitDepartAfter = document.querySelector("#parent-transit-depart-after");
const parentTransitDepartWindow = document.querySelector("#parent-transit-depart-window");
const parentTransitDayStart = document.querySelector("#parent-transit-day-start");
const parentTransitDayEnd = document.querySelector("#parent-transit-day-end");
const parentTransitDirectOnly = document.querySelector("#parent-transit-direct-only");
let timetableMode = "actual";
let timetableWeek = initialTimetableWeek();
let timetableLayout = "day";
let homeworkMode = "open";
let transitView = "recommended";
let selectedDayKey = "";
let selectedTenantId = "";
let latestTenantAdmin = { tenants: [] };
let latestSchedule = {};
let latestHomework = {};
let latestExams = {};
let latestManualLessons = {};
let latestParentProfile = {};
let latestTransit = {};
let latestInviteResult = {};
let tenantFormDirty = false;
let parentProfileDirty = false;
let settingsFormDirty = false;
let transitRetryTimer = 0;
let transitQuickRequestId = 0;
let transitFullRequestId = 0;
let transitCountdownTimer = 0;
let transitFullLoadingDate = "";
let transitProfileRefreshPending = false;
let transitStopState = {
  outbound_origins: [],
  outbound_destinations: [],
  return_origins: [],
  return_destinations: [],
};
let transitStopSelection = {
  outbound_origins: null,
  outbound_destinations: null,
  return_origins: null,
  return_destinations: null,
};
let transitStopTimers = {
  outbound_origins: 0,
  outbound_destinations: 0,
  return_origins: 0,
  return_destinations: 0,
};
let transitStopLookupIds = {
  outbound_origins: 0,
  outbound_destinations: 0,
  return_origins: 0,
  return_destinations: 0,
};
const isAdminPage = Boolean(metrics || channels || configState || runs);

const FIXED_SLOTS = [
  { label: "08:00-08:45", start: "08:00", end: "08:45" },
  { label: "08:50-09:35", start: "08:50", end: "09:35" },
  { label: "09:55-10:40", start: "09:55", end: "10:40" },
  { label: "10:40-11:25", start: "10:40", end: "11:25" },
  { label: "11:45-12:30", start: "11:45", end: "12:30" },
  { label: "12:30-13:15", start: "12:30", end: "13:15" },
  { label: "13:25-14:10", start: "13:25", end: "14:10" },
  { label: "14:15-15:00", start: "14:15", end: "15:00" },
  { label: "15:10-15:55", start: "15:10", end: "15:55" },
  { label: "16:00-16:45", start: "16:00", end: "16:45" },
];

document.querySelectorAll(".ci-tab").forEach((tab) => {
  tab.addEventListener("click", async () => {
    document.querySelectorAll(".ci-tab").forEach((item) => {
      item.setAttribute("aria-selected", String(item === tab));
    });
    document.querySelectorAll(".tab-view").forEach((view) => {
      view.hidden = view.dataset.view !== tab.dataset.tab;
    });
    if (tab.dataset.tab === "transit") {
      const loaded = await refreshTransitData(
        transitProfileRefreshPending,
        false,
        transitView === "full",
      );
      if (loaded) transitProfileRefreshPending = false;
    }
  });
});

if (checkNow) {
  checkNow.addEventListener("click", async () => {
  checkNow.disabled = true;
  lastResult.textContent = "Prüfung läuft...";
  try {
    const result = await fetchJson(`/api/check${adminTenantQuery()}`, { method: "POST" });
    lastResult.textContent = `${result.message} ${formatChannels(result.notified_channels)}`;
    await refresh();
  } catch (error) {
    lastResult.textContent = error.message;
  } finally {
    checkNow.disabled = false;
  }
  });
}

if (refreshTimetable) {
  refreshTimetable.addEventListener("click", async () => {
  refreshTimetable.disabled = true;
  try {
    await refresh();
  } finally {
    refreshTimetable.disabled = false;
  }
  });
}

if (logoutButton) {
  logoutButton.addEventListener("click", async () => {
    await fetchJson("/api/logout", { method: "POST" });
    window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname || "/app")}`);
  });
}

if (loginForm) {
  configureLoginPage();
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    loginError.textContent = "";
    try {
      const result = await fetchJson("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: loginUsername.value,
          password: loginPassword.value,
        }),
      });
      const requestedNext = new URLSearchParams(window.location.search).get("next");
      let next = requestedNext || result.next || "/app";
      if (result.role === "admin") {
        next = "/admin";
      } else if (result.role === "parent" && next.startsWith("/admin")) {
        next = "/app";
      }
      window.location.assign(next.startsWith("/") ? next : "/app");
    } catch (_error) {
      loginError.textContent = "Benutzername oder Passwort falsch.";
    }
  });
}

async function configureLoginPage() {
  const requestedNext = new URLSearchParams(window.location.search).get("next") || "/app";
  if (oidcLogin) {
    oidcLogin.setAttribute("href", `/auth/login?next=${encodeURIComponent(requestedNext)}`);
  }
  try {
    const mode = await fetchJson("/api/auth/mode");
    if (oidcLogin) oidcLogin.hidden = !mode.oidc_enabled;
    loginForm.hidden = !mode.parent_login_enabled && !mode.legacy_enabled;
    if (legacyLoginCopy) {
      legacyLoginCopy.hidden = !mode.parent_login_enabled && (!mode.legacy_enabled || !mode.oidc_enabled);
    }
    if (!mode.oidc_enabled && !mode.legacy_enabled && !mode.parent_login_enabled && loginError) {
      loginError.textContent = "Anmeldung ist noch nicht konfiguriert.";
    }
  } catch (_error) {
    if (oidcLogin) oidcLogin.hidden = true;
  }
}

if (setupForm) {
  loadSetupContext();
  setupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setupError.textContent = "";
    try {
      const result = await fetchJson("/api/setup/accept", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: setupToken(),
          username: setupUsername.value,
          password: setupPassword.value,
        }),
      });
      window.location.assign(result.next || "/app");
    } catch (error) {
      setupError.textContent = error.message || "Einrichtung fehlgeschlagen.";
    }
  });
}

if (parentProfileForm) {
  parentProfileForm.addEventListener("input", () => {
    parentProfileDirty = true;
  });
  parentProfileForm.addEventListener("change", () => {
    parentProfileDirty = true;
  });
  parentProfileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const result = await fetchJson("/api/parent/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parentProfilePayloadFromForm()),
    });
    latestParentProfile = result;
    parentProfileDirty = false;
    fillParentProfileForm(result.tenant || {});
    invalidateTransitData();
    setParentProfileState("Profil gespeichert.");
    await refresh();
  });
}

document.querySelectorAll("[data-stop-input]").forEach((input) => {
  input.addEventListener("input", () => {
    const field = input.dataset.stopInput || "";
    parentProfileDirty = true;
    transitStopSelection[field] = null;
    setStopAddEnabled(field, false);
    scheduleStopSuggestions(field, input.value);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addStopFromInput(input.dataset.stopInput || "");
    }
  });
});

document.querySelectorAll("[data-stop-add]").forEach((button) => {
  button.addEventListener("click", () => {
    addStopFromInput(button.dataset.stopAdd || "");
  });
});

if (tenantSelect) {
  tenantSelect.addEventListener("change", async () => {
    selectedTenantId = tenantSelect.value;
    latestInviteResult = {};
    tenantFormDirty = false;
    fillTenantForm(selectedTenant());
    renderInviteResult(latestInviteResult);
    await refresh();
  });
}

if (tenantNew) {
  tenantNew.addEventListener("click", () => {
    selectedTenantId = "";
    latestInviteResult = {};
    tenantFormDirty = false;
    fillTenantForm(null);
    renderInviteResult(latestInviteResult);
    setTenantSaveState("Neues Profil");
  });
}

if (tenantSendInvite) {
  tenantSendInvite.addEventListener("click", async () => {
    if (tenantFormDirty) {
      setTenantSaveState("Bitte erst Profil speichern.");
      return;
    }
    if (!tenantId.value) {
      setTenantSaveState("Profil zuerst speichern.");
      return;
    }
    const result = await fetchJson(`/api/tenants/${encodeURIComponent(tenantId.value)}/invite`, {
      method: "POST",
    });
    latestTenantAdmin = result;
    latestInviteResult = result.invite || {};
    renderTenantAdmin();
    renderInviteResult(latestInviteResult);
    setTenantSaveState(result.invite?.sent ? "Einladung gesendet." : "Einladung vorbereitet.");
  });
}

if (refreshHomework) {
  refreshHomework.addEventListener("click", async () => {
    refreshHomework.disabled = true;
    try {
      await refreshHomeworkData();
    } finally {
      refreshHomework.disabled = false;
    }
  });
}

if (refreshExams) {
  refreshExams.addEventListener("click", async () => {
    refreshExams.disabled = true;
    try {
      await refreshExamsData(true);
    } finally {
      refreshExams.disabled = false;
    }
  });
}

if (refreshTransit) {
  refreshTransit.addEventListener("click", async () => {
    refreshTransit.disabled = true;
    try {
      await refreshTransitData(true, false, transitView === "full");
    } finally {
      refreshTransit.disabled = false;
    }
  });
}

if (homeworkForm) {
  homeworkForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      text: homeworkText.value,
      subject: homeworkSubject.value || null,
      due_date: homeworkDueDate.value || null,
    };
    const result = await fetchJson(apiPath("/homework/manual"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    homeworkForm.reset();
    latestHomework = result;
    renderHomework(latestHomework);
  });
}

if (manualLessonRepeat) {
  manualLessonRepeat.addEventListener("change", updateManualLessonMode);
  updateManualLessonMode();
}

if (manualLessonForm) {
  manualLessonForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const recurring = manualLessonRepeat.value !== "false";
    const payload = {
      title: manualLessonTitle.value,
      recurring,
      weekday: recurring ? Number(manualLessonWeekday.value) : null,
      date: recurring ? null : manualLessonDate.value || null,
      start: manualLessonStart.value,
      end: manualLessonEnd.value,
      room: manualLessonRoom.value || null,
      note: manualLessonNote.value || null,
    };
    const result = await fetchJson(apiPath("/manual-lessons"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    latestManualLessons = result;
    resetManualLessonForm();
    renderManualLessons(latestManualLessons);
    await refresh();
  });
}

document.querySelectorAll("[data-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    timetableMode = button.dataset.mode || "actual";
    document.querySelectorAll("[data-mode]").forEach((item) => {
      item.setAttribute("aria-pressed", String(item === button));
    });
    renderTimetable(latestSchedule);
  });
});

document.querySelectorAll("[data-week]").forEach((button) => {
  button.addEventListener("click", () => {
    timetableWeek = button.dataset.week || "current";
    selectedDayKey = "";
    updateWeekButtons();
    renderTimetable(latestSchedule);
    renderTransitDaySwitch();
    if (isTransitVisible()) {
      refreshTransitData();
    }
  });
});

document.querySelectorAll("[data-layout]").forEach((button) => {
  button.addEventListener("click", () => {
    timetableLayout = button.dataset.layout || "week";
    updateLayoutButtons();
    renderTimetable(latestSchedule);
  });
});

document.querySelectorAll("[data-transit-view]").forEach((button) => {
  button.addEventListener("click", async () => {
    transitView = button.dataset.transitView || "recommended";
    updateTransitViewButtons();
    renderTransitView();
    const date = selectedDayKey || isoDate(new Date());
    if (transitView === "full"
        && !(latestTransit.date === date && latestTransit.full_day)
        && transitFullLoadingDate !== date) {
      transitFullLoadingDate = date;
      if (transitFullCount) transitFullCount.textContent = "Tagesfahrplan wird geladen...";
      if (transitOutbound) transitOutbound.innerHTML = `<div class="empty-state">Hinfahrten werden geladen...</div>`;
      if (transitReturn) transitReturn.innerHTML = `<div class="empty-state">Rückfahrten werden geladen...</div>`;
      const loaded = await refreshTransitData(false, true, true);
      transitFullLoadingDate = "";
      if (!loaded
          && transitFullCount
          && transitFullCount.textContent === "Tagesfahrplan wird geladen...") {
        transitFullCount.textContent = "Tagesfahrplan nicht erreichbar";
      }
    }
  });
});

document.querySelectorAll("[data-homework-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    homeworkMode = button.dataset.homeworkMode || "open";
    updateHomeworkModeButtons();
    renderHomework(latestHomework);
  });
});

updateWeekButtons();
updateLayoutButtons();
updateTransitViewButtons();
updateHomeworkModeButtons();

if (settingsForm) {
  settingsForm.addEventListener("input", () => {
    settingsFormDirty = true;
  });
  settingsForm.addEventListener("change", () => {
    settingsFormDirty = true;
  });
  settingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const minutes = Number(pollInterval.value);
    const transitMinutes = Number(transitPollInterval.value);
    const result = await fetchJson(`/api/settings${adminTenantQuery()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        poll_interval_minutes: minutes,
        transit_poll_interval_minutes: transitMinutes,
        email_recipients: emailRecipients ? emailRecipients.value : undefined,
      }),
    });
    settingsFormDirty = false;
    pollInterval.value = result.poll_interval_minutes;
    transitPollInterval.value = result.transit_poll_interval_minutes;
    if (emailRecipients) emailRecipients.value = (result.email_recipients || []).join(", ");
    await refresh();
  });
}

if (tenantForm) {
  tenantForm.addEventListener("input", () => {
    tenantFormDirty = true;
  });
  tenantForm.addEventListener("change", () => {
    tenantFormDirty = true;
  });
  tenantForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = tenantId.value;
    const result = await fetchJson(id ? `/api/tenants/${encodeURIComponent(id)}` : "/api/tenants", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tenantPayloadFromForm()),
    });
    latestTenantAdmin = result;
    if (!selectedTenantId) {
      selectedTenantId = result.tenants[result.tenants.length - 1]?.id || "";
    }
    latestInviteResult = {};
    tenantFormDirty = false;
    renderTenantAdmin();
    renderInviteResult(latestInviteResult);
    await refresh();
    setTenantSaveState("Profil gespeichert.");
  });
}

async function refresh() {
  if (!isAdminPage) {
    const [schedule, homework, exams, manualLessons, parentProfile] = await Promise.all([
      fetchJson(apiPath("/schedule")),
      fetchJson(apiPath("/homework")),
      fetchJson(apiPath("/exams")),
      fetchJson(apiPath("/manual-lessons")),
      fetchJson("/api/parent/profile").catch(() => null),
    ]);
    latestSchedule = schedule.days || {};
    latestHomework = homework;
    latestExams = exams;
    latestManualLessons = manualLessons;
    latestParentProfile = parentProfile || latestParentProfile;
    if (topStatus) topStatus.textContent = "Live";
    const profile = schedule.profile || homework.profile || parentProfile?.tenant?.display || {};
    renderProfileContext(profile);
    if (!parentProfileDirty) {
      fillParentProfileForm(parentProfile?.tenant || {});
    }
    renderSnapshotStamp(schedule.timestamp);
    renderTimetable(latestSchedule);
    renderTransitDaySwitch();
    renderHomework(latestHomework);
    renderExams(latestExams);
    renderManualLessons(latestManualLessons);
    return;
  }

  const [status, runData, tenantData] = await Promise.all([
    fetchJson(`/api/status${adminTenantQuery()}`),
    fetchJson(`/api/runs${adminTenantQuery()}`),
    fetchJson("/api/tenants"),
  ]);
  latestTenantAdmin = tenantData;
  renderStatus(status);
  renderTenantAdmin();
  renderSnapshotStamp(status.snapshot_timestamp);
  renderRuns(runData.runs || []);
}

function renderProfileContext(profile) {
  const details = compact([
    profile.student_name,
    profile.school,
    profile.class ? `Klasse ${profile.class}` : "",
  ]);
  const text = details.join(" - ");
  if (profileContext) profileContext.textContent = text;
  if (brandSubtitle && text) brandSubtitle.textContent = text;
}

async function loadSetupContext() {
  if (!setupProfileContext) return;
  try {
    const context = await fetchJson(`/api/setup/context?token=${encodeURIComponent(setupToken())}`);
    const profile = context.profile || {};
    const details = compact([
      profile.student_name,
      profile.school,
      profile.class ? `Klasse ${profile.class}` : "",
      context.email,
    ]);
    setupProfileContext.textContent = details.join(" | ");
  } catch (error) {
    setupProfileContext.textContent = error.message || "Einladung ist ungültig oder abgelaufen.";
    if (setupForm) {
      Array.from(setupForm.elements).forEach((element) => {
        element.disabled = true;
      });
    }
  }
}

function setupToken() {
  return new URLSearchParams(window.location.search).get("token") || "";
}

function fillParentProfileForm(tenant) {
  if (!parentProfileForm) return;
  const profile = tenant.display || {};
  const details = compact([
    profile.student_name,
    profile.school,
    profile.class ? `Klasse ${profile.class}` : "",
  ]);
  if (parentProfileContext) parentProfileContext.textContent = details.join(" | ");
  parentWebuntisServer.value = tenant.webuntis?.server || "";
  parentWebuntisSchool.value = tenant.webuntis?.school || "";
  parentWebuntisUsername.value = tenant.webuntis?.username || "";
  parentWebuntisPassword.value = "";
  parentWebuntisPassword.placeholder = tenant.webuntis?.has_password ? "********" : "";
  parentWebuntisAppSecret.value = "";
  parentWebuntisAppSecret.placeholder = tenant.webuntis?.has_app_secret ? "********" : "";
  parentWebuntisElementType.value = tenant.webuntis?.element_type || 5;
  parentWebuntisElementId.value = tenant.webuntis?.element_id || "";
  parentWebuntisClassName.value = tenant.webuntis?.class_name || "";
  parentWebuntisSchoolNumber.value = tenant.webuntis?.school_number || "";
  const transit = tenant.transit || {};
  setStopValues("outbound_origins", transit.outbound_origins, transit.validation?.groups?.outbound_origins);
  setStopValues("outbound_destinations", transit.outbound_destinations, transit.validation?.groups?.outbound_destinations);
  setStopValues("return_origins", transit.return_origins, transit.validation?.groups?.return_origins);
  setStopValues("return_destinations", transit.return_destinations, transit.validation?.groups?.return_destinations);
  parentTransitArriveBefore.value = transit.arrive_min_before ?? 10;
  parentTransitArriveWindow.value = transit.arrive_window_minutes ?? 60;
  parentTransitDepartAfter.value = transit.depart_min_after ?? 5;
  parentTransitDepartWindow.value = transit.depart_window_minutes ?? 90;
  parentTransitDayStart.value = transit.day_start || "05:00";
  parentTransitDayEnd.value = transit.day_end || "20:00";
  parentTransitDirectOnly.checked = Boolean(transit.direct_connections_only);
  parentProfileDirty = false;
}

function setStopValues(field, values = [], validation = []) {
  const validationByInput = new Map((validation || []).map((item) => [item.input, item]));
  transitStopState[field] = (Array.isArray(values) ? values : [])
    .map((value) => validationByInput.get(value) || stopItemFromValue(value))
    .filter((item) => item.name || item.input);
  transitStopSelection[field] = null;
  const input = document.querySelector(`[data-stop-input="${field}"]`);
  const suggestions = document.querySelector(`[data-stop-suggestions="${field}"]`);
  if (input) input.value = "";
  if (suggestions) suggestions.innerHTML = "";
  setStopAddEnabled(field, false);
  syncStopField(field);
  renderStopChips(field);
  renderStopValidation(field, validation);
}

function stopItemFromValue(value) {
  const [name, id = ""] = String(value || "").split("|", 2);
  return {
    input: String(value || "").trim(),
    name: name.trim(),
    id: id.trim(),
    value: String(value || "").trim(),
    status: id ? "valid" : "unchecked",
  };
}

function stopValue(item) {
  if (item.value) return item.value;
  return item.id ? `${item.name}|${item.id}` : item.name;
}

function syncStopField(field) {
  const element = stopTextarea(field);
  if (!element) return;
  element.value = (transitStopState[field] || []).map(stopValue).join("\n");
}

function stopTextarea(field) {
  return {
    outbound_origins: parentTransitOutboundOrigins,
    outbound_destinations: parentTransitOutboundDestinations,
    return_origins: parentTransitReturnOrigins,
    return_destinations: parentTransitReturnDestinations,
  }[field] || null;
}

function renderStopChips(field) {
  const container = document.querySelector(`[data-stop-chips="${field}"]`);
  if (!container) return;
  const items = transitStopState[field] || [];
  container.innerHTML = items
    .map((item, index) => `
      <span class="stop-chip" data-status="${escapeHtml(item.status || "unchecked")}">
        <span>${escapeHtml(item.name || item.input)}</span>
        <button type="button" data-stop-remove="${escapeHtml(field)}" data-stop-index="${index}" aria-label="Haltestelle entfernen">×</button>
      </span>
    `)
    .join("");
  container.querySelectorAll("[data-stop-remove]").forEach((button) => {
    button.addEventListener("click", () => {
      const targetField = button.dataset.stopRemove || "";
      const index = Number(button.dataset.stopIndex || -1);
      transitStopState[targetField] = (transitStopState[targetField] || []).filter((_item, itemIndex) => itemIndex !== index);
      syncStopField(targetField);
      renderStopChips(targetField);
      renderStopValidation(targetField);
      parentProfileDirty = true;
    });
  });
}

function renderStopValidation(field, validation) {
  const container = document.querySelector(`[data-stop-validation="${field}"]`);
  if (!container) return;
  const items = validation || transitStopState[field] || [];
  container.innerHTML = items
    .filter((item) => item.status && item.status !== "valid" && item.status !== "unchecked")
    .map((item) => {
      const text = item.status === "ambiguous"
        ? `${item.name || item.input}: mehrere Treffer`
        : `${item.name || item.input}: nicht gefunden`;
      return `<span class="ci-badge" data-tone="warn">${escapeHtml(text)}</span>`;
    })
    .join("");
}

async function renderStopSuggestions(field, query) {
  const container = document.querySelector(`[data-stop-suggestions="${field}"]`);
  if (!container) return;
  const lookupId = (transitStopLookupIds[field] || 0) + 1;
  transitStopLookupIds[field] = lookupId;
  const text = String(query || "").trim();
  if (text.length < 2) {
    container.innerHTML = "";
    return;
  }
  container.innerHTML = `<span class="ci-small">Suche Haltestellen...</span>`;
  try {
    const result = await fetchJson(`/api/transit/stops?q=${encodeURIComponent(text)}&limit=6`);
    if (transitStopLookupIds[field] !== lookupId) return;
    const items = result.items || [];
    container.innerHTML = items.length
      ? items.map((item) => `
          <button class="ci-button stop-suggestion" type="button" data-stop-suggestion="${escapeHtml(field)}" data-stop-value="${escapeHtml(item.value)}" data-stop-name="${escapeHtml(item.name)}" data-stop-id="${escapeHtml(item.id)}">
            <span>${escapeHtml(item.name)}</span>
            <small>${escapeHtml(item.detail || item.id || "")}</small>
          </button>
        `).join("")
      : `<span class="ci-small">Keine passende Haltestelle gefunden.</span>`;
    container.querySelectorAll("[data-stop-suggestion]").forEach((button) => {
      button.addEventListener("click", () => {
        const item = {
          input: button.dataset.stopValue || "",
          value: button.dataset.stopValue || "",
          name: button.dataset.stopName || "",
          id: button.dataset.stopId || "",
          status: "valid",
        };
        selectStopSuggestion(field, item);
      });
    });
  } catch (error) {
    if (transitStopLookupIds[field] !== lookupId) return;
    container.innerHTML = `<span class="ci-small">${escapeHtml(error.message)}</span>`;
  }
}

function scheduleStopSuggestions(field, query) {
  if (!(field in transitStopTimers)) return;
  window.clearTimeout(transitStopTimers[field]);
  transitStopTimers[field] = window.setTimeout(() => {
    renderStopSuggestions(field, query);
  }, 250);
}

function selectStopSuggestion(field, item) {
  if (!field || !(field in transitStopSelection) || !item?.id) return;
  transitStopSelection[field] = item;
  const input = document.querySelector(`[data-stop-input="${field}"]`);
  const suggestions = document.querySelector(`[data-stop-suggestions="${field}"]`);
  if (input) input.value = item.name || item.input || "";
  if (suggestions) {
    suggestions.innerHTML = `<span class="stop-selected">Ausgewählt: ${escapeHtml(item.name || item.input)}</span>`;
  }
  setStopAddEnabled(field, true);
}

function addStopFromInput(field) {
  const item = transitStopSelection[field];
  if (!item?.id) return;
  addStopItem(field, item);
}

function addStopItem(field, item) {
  if (!field || !(field in transitStopState)) return;
  const value = stopValue(item);
  const existing = new Set((transitStopState[field] || []).map(stopValue));
  if (!existing.has(value)) {
    transitStopState[field] = [...(transitStopState[field] || []), { ...item, value }];
  }
  const input = document.querySelector(`[data-stop-input="${field}"]`);
  const suggestions = document.querySelector(`[data-stop-suggestions="${field}"]`);
  if (input) input.value = "";
  if (suggestions) suggestions.innerHTML = "";
  transitStopSelection[field] = null;
  setStopAddEnabled(field, false);
  syncStopField(field);
  renderStopChips(field);
  renderStopValidation(field);
  parentProfileDirty = true;
}

function setStopAddEnabled(field, enabled) {
  const button = document.querySelector(`[data-stop-add="${field}"]`);
  if (button) button.disabled = !enabled;
}

function parentProfilePayloadFromForm() {
  return {
    webuntis: {
      server: parentWebuntisServer.value,
      school: parentWebuntisSchool.value,
      username: parentWebuntisUsername.value,
      password: parentWebuntisPassword.value || null,
      app_secret: parentWebuntisAppSecret.value || null,
      school_number: parentWebuntisSchoolNumber.value,
      element_type: Number(parentWebuntisElementType.value || 5),
      element_id: parentWebuntisElementId.value ? Number(parentWebuntisElementId.value) : null,
      class_name: parentWebuntisClassName.value,
    },
    transit: {
      outbound_origins: parentTransitOutboundOrigins.value,
      outbound_destinations: parentTransitOutboundDestinations.value,
      return_origins: parentTransitReturnOrigins.value,
      return_destinations: parentTransitReturnDestinations.value,
      arrive_min_before: Number(parentTransitArriveBefore.value || 10),
      arrive_window_minutes: Number(parentTransitArriveWindow.value || 60),
      depart_min_after: Number(parentTransitDepartAfter.value || 5),
      depart_window_minutes: Number(parentTransitDepartWindow.value || 90),
      day_start: parentTransitDayStart.value || "05:00",
      day_end: parentTransitDayEnd.value || "20:00",
      direct_connections_only: parentTransitDirectOnly.checked,
    },
  };
}

function setParentProfileState(message) {
  if (!parentProfileState) return;
  parentProfileState.textContent = message;
  window.setTimeout(() => {
    if (parentProfileState.textContent === message) {
      parentProfileState.textContent = "";
    }
  }, 3000);
}

function invalidateTransitData() {
  transitProfileRefreshPending = true;
  latestTransit = {};
  transitFullLoadingDate = "";
  transitQuickRequestId += 1;
  transitFullRequestId += 1;
  clearTransitRetry();
  const date = selectedDayKey || isoDate(new Date());
  resetTransitView(date);
}

async function refreshHomeworkData() {
  const homework = await fetchJson(apiPath("/homework"));
  latestHomework = homework;
  renderHomework(latestHomework);
}

async function refreshExamsData(forceRefresh = false) {
  const query = forceRefresh ? "?refresh=1" : "";
  const exams = await fetchJson(`${apiPath("/exams")}${query}`);
  latestExams = exams;
  renderExams(latestExams);
}

async function refreshTransitData(forceRefresh = false, silent = false, includeFullDay = false) {
  if (!transitRecommendations) return;
  renderTransitDaySwitch();
  const date = selectedDayKey || isoDate(new Date());
  const requestId = includeFullDay ? ++transitFullRequestId : ++transitQuickRequestId;
  const requestIsCurrent = () => {
    const latestRequestId = includeFullDay ? transitFullRequestId : transitQuickRequestId;
    const currentDate = selectedDayKey || isoDate(new Date());
    return requestId === latestRequestId && currentDate === date;
  };
  if (!silent) resetTransitView(date);
  try {
    const refreshQuery = forceRefresh ? "&refresh=1" : "";
    const fullQuery = includeFullDay ? "&full=1" : "";
    let transit = await fetchJson(`${apiPath("/transit")}?date=${encodeURIComponent(date)}${refreshQuery}${fullQuery}`);
    if (!requestIsCurrent() || transit.date !== date) {
      return false;
    }
    if (!transit.full_day && latestTransit.date === transit.date && latestTransit.full_day) {
      transit = {
        ...transit,
        outbound: latestTransit.outbound || [],
        return: latestTransit.return || [],
        full_day: true,
        full_day_cached: true,
      };
    }
    latestTransit = transit;
    renderTransit(transit);
    return true;
  } catch (error) {
    if (!requestIsCurrent()) {
      return false;
    }
    if (silent) {
      if (includeFullDay && transitFullCount) {
        transitFullCount.textContent = `Tagesfahrplan nicht erreichbar: ${error.message}`;
      }
      return false;
    }
    latestTransit = {};
    if (transitStamp) transitStamp.textContent = "Fahrplan nicht erreichbar.";
    if (transitWarnings) transitWarnings.innerHTML = `<div class="notice-row">${escapeHtml(error.message)}</div>`;
    if (transitRecommendations) transitRecommendations.innerHTML = "";
    if (transitOutbound) transitOutbound.innerHTML = "";
    if (transitReturn) transitReturn.innerHTML = "";
    if (transitFullCount) transitFullCount.textContent = "";
    renderTransitView();
    return false;
  }
}

function resetTransitView(date) {
  clearTransitRetry();
  if (transitStamp) {
    transitStamp.textContent = `${formatDate(date)} | Fahrplan wird geladen...`;
  }
  if (transitWarnings) transitWarnings.innerHTML = "";
  if (transitRecommendations) {
    transitRecommendations.innerHTML = `
      <article class="transit-card transit-recommendation">
        <span class="ci-section-kicker">Empfehlung hin</span>
        <div class="empty-state">Wird geladen...</div>
      </article>
      <article class="transit-card transit-recommendation">
        <span class="ci-section-kicker">Empfehlung zurück</span>
        <div class="empty-state">Wird geladen...</div>
      </article>
    `;
  }
  if (transitOutbound) transitOutbound.innerHTML = `<div class="empty-state">Wird geladen...</div>`;
  if (transitReturn) transitReturn.innerHTML = `<div class="empty-state">Wird geladen...</div>`;
  if (transitFullCount) transitFullCount.textContent = "";
  renderTransitView();
}

function updateManualLessonMode() {
  if (!manualLessonRepeat) return;
  const recurring = manualLessonRepeat.value !== "false";
  if (manualLessonWeekdayField) manualLessonWeekdayField.hidden = !recurring;
  if (manualLessonDateField) manualLessonDateField.hidden = recurring;
  if (manualLessonDate) manualLessonDate.required = !recurring;
}

function resetManualLessonForm() {
  if (!manualLessonForm) return;
  manualLessonForm.reset();
  manualLessonRepeat.value = "true";
  manualLessonStart.value = "14:15";
  manualLessonEnd.value = "15:00";
  updateManualLessonMode();
}

async function fetchJson(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const response = await fetch(safeFetchUrl(url), { ...options, headers });
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = payload.detail || "";
    } catch (_error) {
      detail = "";
    }
    throw new Error(detail || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

function safeFetchUrl(url) {
  if (!url.startsWith("/")) {
    return url;
  }
  return `${window.location.protocol}//${window.location.host}${url}`;
}

function apiPath(path) {
  const tenantId = tenantIdFromPath();
  if (!tenantId) {
    return `/api${path}`;
  }
  return `/api/t/${encodeURIComponent(tenantId)}${path}`;
}

function tenantIdFromPath() {
  const match = window.location.pathname.match(/^\/t\/([^/]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

function adminTenantQuery() {
  return selectedTenantId ? `?tenant_id=${encodeURIComponent(selectedTenantId)}` : "";
}

function renderStatus(status) {
  const ready = status.webuntis_ready;
  if (topStatus) topStatus.textContent = ready ? "Ready" : "Setup";
  selectedTenantId = selectedTenantId || status.tenant_id || "";
  renderTenantSelect(status.tenants || [], selectedTenantId);
  if (pollCopy) pollCopy.textContent = `Stundenplan alle ${status.poll_interval_minutes} Minuten, Busverbindungen alle ${status.transit_poll_interval_minutes} Minuten. Schulwochen: ${formatDate(status.window_start)} bis ${formatDate(status.window_end)}.`;
  if (!settingsFormDirty) {
    if (pollInterval) pollInterval.value = status.poll_interval_minutes;
    if (transitPollInterval) transitPollInterval.value = status.transit_poll_interval_minutes;
    if (emailRecipients) emailRecipients.value = (status.email_recipients || []).join(", ");
  }

  const latestRun = (status.runs || [])[0];
  if (lastResult) {
    lastResult.textContent = latestRun
      ? `${latestRun.message} ${formatChannels(latestRun.notified_channels)}`
      : "Noch kein Lauf protokolliert.";
  }

  if (metrics) {
    metrics.innerHTML = [
      metric(status.lesson_count, "Stunden im Snapshot"),
      metric((status.tenants || []).length, "Profile"),
      metric((status.runs || []).length, "Läufe geladen"),
    ].join("");
  }

  const availableChannels = [
    ["email", "E-Mail"],
    ["whatsapp", "WhatsApp"],
    ["webhook", "Webhook"],
  ];
  if (channels) {
    channels.innerHTML = availableChannels
      .map(([key, label]) => channelRow(label, status.channels.includes(key)))
      .join("");
  }

  if (configState) {
    configState.innerHTML = ready
      ? [
          configItem("WebUntis", "vollständig"),
          configItem("Auth", status.auth_mode),
          configItem("Element", `${status.element_type}/${status.element_id}`),
        ].join("")
      : configItem("Fehlt", status.missing_fields.join(", "));
  }
}

function renderTenantAdmin() {
  if (!tenantForm) return;
  if (!selectedTenantId) {
    selectedTenantId = latestTenantAdmin.tenants?.[0]?.id || "";
  }
  renderTenantSelect(latestTenantAdmin.tenants || [], selectedTenantId);
  if (tenantFormDirty) {
    return;
  }
  fillTenantForm(selectedTenant());
}

function selectedTenant() {
  return (latestTenantAdmin.tenants || []).find((tenant) => tenant.id === selectedTenantId) || null;
}

function fillTenantForm(tenant) {
  if (!tenantForm) return;
  tenantId.value = tenant?.id || "";
  tenantName.value = tenant?.name || "";
  tenantParentEmail.value = tenant?.parent_email || "";
  tenantActive.checked = tenant ? Boolean(tenant.active) : true;
  tenantStudentFirstName.value = tenant?.display_admin?.student_first_name || "";
  if (tenantStudentLastInitial) {
    tenantStudentLastInitial.value = tenant?.display_admin?.student_last_name || tenant?.display_admin?.student_last_initial || "";
  }
  tenantSchoolLabel.value = tenant?.display_admin?.school || "";
  tenantClassLabel.value = tenant?.display_admin?.class || "";
  tenantWebuntisServer.value = tenant?.webuntis?.server || "";
  tenantWebuntisSchool.value = tenant?.webuntis?.school || "";
  tenantWebuntisElementType.value = tenant?.webuntis?.element_type || 5;
  tenantWebuntisElementId.value = tenant?.webuntis?.element_id || "";
  tenantWebuntisClassName.value = tenant?.webuntis?.class_name || "";
  tenantWebuntisSchoolNumber.value = tenant?.webuntis?.school_number || "";
  tenantEmailRecipients.value = (tenant?.email_recipients || []).join(", ");
  if (tenantSelect && tenant?.id) tenantSelect.value = tenant.id;
  tenantFormDirty = false;
}

function tenantPayloadFromForm() {
  return {
    name: tenantName.value,
    parent_email: tenantParentEmail.value,
    active: tenantActive.checked,
    display: {
      student_first_name: tenantStudentFirstName.value,
      student_last_name: tenantStudentLastInitial?.value || "",
      student_last_initial: tenantStudentLastInitial?.value || "",
      school: tenantSchoolLabel.value,
      class_name: tenantClassLabel.value,
    },
    webuntis: {
      server: tenantWebuntisServer.value,
      school: tenantWebuntisSchool.value,
      school_number: tenantWebuntisSchoolNumber.value,
      element_type: Number(tenantWebuntisElementType.value || 5),
      element_id: tenantWebuntisElementId.value ? Number(tenantWebuntisElementId.value) : null,
      class_name: tenantWebuntisClassName.value,
    },
    email: {
      recipients: tenantEmailRecipients.value,
    },
  };
}

function setTenantSaveState(message) {
  if (!tenantSaveState) return;
  tenantSaveState.textContent = message;
  window.setTimeout(() => {
    if (tenantSaveState.textContent === message) {
      tenantSaveState.textContent = "";
    }
  }, 3000);
}

function renderInviteResult(invite) {
  if (!tenantInviteResult) return;
  if (!invite || !invite.setup_url) {
    tenantInviteResult.innerHTML = "";
    return;
  }
  const title = invite.sent ? "Einladung wurde per E-Mail versendet." : "Einladung wurde vorbereitet.";
  const detail = invite.error
    ? `Mailversand nicht erfolgreich: ${invite.error}`
    : "Der Link ist einmalig für die Einrichtung gedacht.";
  tenantInviteResult.innerHTML = `
    <div class="notice-row">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
      <input type="text" readonly value="${escapeHtml(invite.setup_url)}">
    </div>
  `;
}

function renderTenantSelect(tenants, activeId) {
  if (!tenantSelect) return;
  const currentOptions = Array.from(tenantSelect.options)
    .map((option) => `${option.value}:${option.textContent}`)
    .join("|");
  const nextOptions = tenants.map((tenant) => `${tenant.id}:${tenant.name}`).join("|");
  if (currentOptions !== nextOptions) {
    tenantSelect.innerHTML = tenants
      .map((tenant) => `<option value="${escapeHtml(tenant.id)}">${escapeHtml(tenant.name)}</option>`)
      .join("");
  }
  tenantSelect.value = activeId;
}

function renderSchedule(groupedDays) {
  if (!days) return;
  const entries = Object.entries(groupedDays).filter(([day]) => isSchoolDay(day));
  if (!entries.length) {
    days.innerHTML = `<div class="empty-state">Noch kein Stundenplan-Snapshot vorhanden.</div>`;
    return;
  }

  days.innerHTML = entries
    .map(([day, lessons]) => `
      <section class="day-section">
        <div class="day-header">
          <h2>${escapeHtml(formatDate(day))}</h2>
          <span class="ci-badge">${lessons.length} Stunden</span>
        </div>
        <div class="lesson-list">
          ${lessons.map(renderLesson).join("")}
        </div>
      </section>
    `)
    .join("");
}

function renderTimetable(groupedDays) {
  if (!timetable) return;
  const weekDays = weekEntries(groupedDays, timetableWeek);
  ensureSelectedDay(weekDays);
  renderDaySwitch(weekDays);
  const entries = timetableLayout === "day"
    ? weekDays.filter(([day]) => day === selectedDayKey)
    : weekDays;

  timetable.style.setProperty("--day-count", entries.length);
  timetable.innerHTML = `
    <div class="tt-desktop-grid">
      ${[
        `<div class="tt-head tt-corner">Zeit</div>`,
        ...entries.map(([day]) => `
          <div class="tt-head">
            <span>${escapeHtml(weekday(day))}</span>
            <small>${escapeHtml(shortDate(day))}</small>
          </div>
        `),
        ...FIXED_SLOTS.flatMap((slot) => [
          `<div class="tt-time">${escapeHtml(slot.label)}</div>`,
          ...entries.map(([, lessons]) => renderTimetableCell(slot, lessons)),
        ]),
      ].join("")}
    </div>
    <div class="tt-mobile-list">
      ${entries.map(([day, lessons]) => renderMobileDay(day, lessons)).join("")}
    </div>
  `;
}

function renderHomework(data) {
  if (!homeworkList) return;
  const items = homeworkMode === "completed"
    ? data.completed || []
    : data.open || [];

  if (homeworkStamp) {
    homeworkStamp.textContent = data.timestamp
      ? `Stand: ${formatDateTime(data.timestamp)}`
      : "Stand: noch nicht geladen";
  }
  if (homeworkSummary) {
    homeworkSummary.innerHTML = `
      <span>${escapeHtml(String((data.open || []).length))} offen</span>
      <span>${escapeHtml(String((data.completed || []).length))} erledigt</span>
      <span>${escapeHtml(String(data.webuntis_count || 0))} aus WebUntis</span>
      <span>${escapeHtml(String(data.manual_count || 0))} eigene</span>
      ${data.expired_count ? `<span>${escapeHtml(String(data.expired_count))} abgelaufen</span>` : ""}
      ${data.source_error ? `<span class="homework-error">WebUntis nicht erreichbar</span>` : ""}
    `;
  }

  if (!items.length) {
    homeworkList.innerHTML = `<div class="empty-state">${homeworkMode === "completed" ? "Keine erledigten Hausaufgaben sichtbar." : "Keine offenen Hausaufgaben."}</div>`;
    return;
  }

  homeworkList.innerHTML = items.map(renderHomeworkItem).join("");
  homeworkList.querySelectorAll("[data-homework-complete]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      const id = button.dataset.homeworkComplete || "";
      const result = await fetchJson(`${apiPath("/homework")}/${encodeURIComponent(id)}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed: homeworkMode !== "completed" }),
      });
      latestHomework = result;
      renderHomework(latestHomework);
    });
  });
  homeworkList.querySelectorAll("[data-homework-delete]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      const id = button.dataset.homeworkDelete || "";
      const result = await fetchJson(`${apiPath("/homework")}/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      latestHomework = result;
      renderHomework(latestHomework);
    });
  });
}

function renderHomeworkItem(item) {
  const subject = joinOr(item.subject, item.source === "manual" ? "Eigene Aufgabe" : "ohne Fach");
  const due = item.due_date ? formatDate(item.due_date) : "kein Datum";
  const teacher = joinOr(item.teacher, "");
  const source = item.source === "webuntis" ? "WebUntis" : "Eigen";
  const completed = Boolean(item.completed);
  const expired = Boolean(item.is_expired);
  const stateLabel = completed ? "erledigt" : expired ? "abgelaufen" : "offen";
  const stateTone = completed ? "success" : expired ? "danger" : "warn";
  return `
    <article class="homework-item" data-source="${escapeHtml(item.source || "")}" data-completed="${String(completed)}" data-expired="${String(expired)}">
      <div class="homework-main">
        <div class="homework-title-row">
          <strong>${escapeHtml(subject)}</strong>
          <span class="ci-badge" data-tone="${stateTone}">${escapeHtml(stateLabel)}</span>
        </div>
        <p>${escapeHtml(item.text || item.remark || "")}</p>
        ${item.remark && item.text ? `<small>${escapeHtml(item.remark)}</small>` : ""}
        <div class="homework-meta">
          <span>Bis ${escapeHtml(due)}</span>
          ${teacher ? `<span>${escapeHtml(teacher)}</span>` : ""}
          <span>${escapeHtml(source)}</span>
        </div>
      </div>
      <div class="homework-item-actions">
        <button class="ci-button secondary-button" type="button" data-homework-complete="${escapeHtml(item.id)}">${completed ? "Wieder offen" : "Erledigt"}</button>
        ${item.source === "manual" ? `<button class="ci-icon-button danger-button" type="button" title="Löschen" data-homework-delete="${escapeHtml(item.id)}"><svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/></svg></button>` : ""}
      </div>
    </article>
  `;
}

function renderExams(data) {
  if (!examsList) return;
  const items = data.items || [];
  if (examsStamp) {
    examsStamp.textContent = data.timestamp
      ? `Stand: ${formatDateTime(data.timestamp)}`
      : "Stand: noch nicht geladen";
  }
  if (examsSummary) {
    examsSummary.innerHTML = `
      <span>${escapeHtml(String(items.length))} anstehend</span>
      ${data.iserv_ready ? `<span>IServ verbunden</span>` : `<span class="homework-error">IServ nicht konfiguriert</span>`}
      ${data.source_error ? `<span class="homework-error">Klausurplan nicht erreichbar</span>` : ""}
    `;
  }
  if (data.source_error && !items.length) {
    examsList.innerHTML = `<div class="notice-row">${escapeHtml(data.source_error)}</div>`;
    return;
  }
  if (!items.length) {
    examsList.innerHTML = `<div class="empty-state">Keine anstehenden Klassenarbeiten gefunden.</div>`;
    return;
  }
  examsList.innerHTML = items.map(renderExamItem).join("");
}

function renderExamItem(item) {
  const start = parseDateTimeParts(item.start);
  const end = parseDateTimeParts(item.end);
  const time = compact([
    start.time,
    end.time && end.time !== start.time ? end.time : "",
  ]).join("-");
  const meta = compact([
    start.date,
    time,
    item.group,
  ]);
  return `
    <article class="exam-item">
      <div class="exam-date">
        <strong>${escapeHtml(start.weekday || "")}</strong>
        <span>${escapeHtml(start.shortDate || start.date || "")}</span>
      </div>
      <div class="exam-main">
        <div class="homework-title-row">
          <strong>${escapeHtml(item.title || "Klassenarbeit")}</strong>
          <span class="ci-badge" data-tone="warn">Klassenarbeit</span>
        </div>
        <div class="homework-meta">
          ${meta.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}
        </div>
        ${item.description ? `<p>${escapeHtml(item.description)}</p>` : ""}
      </div>
    </article>
  `;
}

function renderManualLessons(data) {
  if (!manualLessonList) return;
  const items = data.items || [];
  if (manualLessonSummary) {
    const recurringCount = items.filter((item) => item.recurring).length;
    const singleCount = items.length - recurringCount;
    manualLessonSummary.innerHTML = `
      <span>${escapeHtml(String(items.length))} Termine</span>
      <span>${escapeHtml(String(recurringCount))} wöchentlich</span>
      <span>${escapeHtml(String(singleCount))} einmalig</span>
    `;
  }

  if (!items.length) {
    manualLessonList.innerHTML = `<div class="empty-state">Keine eigenen Termine angelegt.</div>`;
    return;
  }

  manualLessonList.innerHTML = items.map(renderManualLessonItem).join("");
  manualLessonList.querySelectorAll("[data-manual-lesson-delete]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      const id = button.dataset.manualLessonDelete || "";
      const result = await fetchJson(`${apiPath("/manual-lessons")}/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      latestManualLessons = result;
      renderManualLessons(latestManualLessons);
      await refresh();
    });
  });
}

function renderManualLessonItem(item) {
  const rhythm = item.recurring
    ? `Wöchentlich ${weekdayName(Number(item.weekday))}`
    : formatDate(item.date);
  const meta = compact([
    rhythm,
    `${item.start}-${item.end}`,
    item.room,
  ]);
  return `
    <article class="manual-lesson-item">
      <div class="manual-lesson-main">
        <div class="homework-title-row">
          <strong>${escapeHtml(item.title || "Eigener Termin")}</strong>
          <span class="ci-badge" data-tone="success">${escapeHtml(item.recurring ? "wöchentlich" : "einmalig")}</span>
        </div>
        ${item.note ? `<p>${escapeHtml(item.note)}</p>` : ""}
        <div class="homework-meta">
          ${meta.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}
        </div>
      </div>
      <div class="homework-item-actions">
        <button class="ci-icon-button danger-button" type="button" title="Löschen" data-manual-lesson-delete="${escapeHtml(item.id)}"><svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/></svg></button>
      </div>
    </article>
  `;
}

function renderTransit(data) {
  if (!transitRecommendations) return;
  const feed = data.feed || {};
  clearTransitRetry();
  if (["downloading", "preparing"].includes(feed.status || "")) {
    transitRetryTimer = window.setTimeout(() => {
      if (isTransitVisible()) {
        refreshTransitData();
      }
    }, 15000);
  }
  const isGeofox = feed.provider === "geofox";
  const providerLabel = isGeofox
    ? (feed.live ? "Live-Daten" : "Geofox-Fahrplan | keine Live-Prognose")
    : (feed.fallback ? "Soll-Fahrplan | Live-Daten nicht verfügbar" : "Soll-Fahrplan");
  const sourceStamp = feed.requested_at || feed.downloaded_at;
  const feedStamp = sourceStamp
    ? `Stand ${formatDateTime(sourceStamp)}`
    : "Fahrplandaten noch nicht geladen";
  if (transitStamp) {
    transitStamp.textContent = `${formatDate(data.date)} | ${providerLabel} | ${feedStamp}`;
  }
  if (transitWarnings) {
    const warnings = data.warnings || [];
    transitWarnings.innerHTML = warnings.length
      ? warnings.map((warning) => `<div class="notice-row">${escapeHtml(warning)}</div>`).join("")
      : "";
  }
  const day = data.day || {};
  const context = compact([
    day.first_lesson_start ? `Beginn ${day.first_lesson_start}` : "",
    day.last_lesson_end ? `Ende ${day.last_lesson_end}` : "",
    (data.settings || {}).enabled ? "" : "Haltestellen im Profil eintragen",
  ]).join(" | ");
  transitRecommendations.innerHTML = `
    <article class="transit-card transit-recommendation">
      <span class="ci-section-kicker">Empfehlung hin</span>
      ${renderTransitConnection(data.recommendation?.outbound, "Keine passende Hinfahrt gefunden.", data.date, true)}
    </article>
    <article class="transit-card transit-recommendation">
      <span class="ci-section-kicker">Empfehlung zurück</span>
      ${renderTransitConnection(data.recommendation?.return, "Keine passende Rückfahrt gefunden.", data.date, true)}
    </article>
    ${context ? `<p class="transit-context">${escapeHtml(context)}</p>` : ""}
  `;
  if (data.full_day && transitOutbound) {
    transitOutbound.innerHTML = renderTransitList(data.outbound || [], "Keine Hinfahrten im Tagesfenster.");
  }
  if (data.full_day && transitReturn) {
    transitReturn.innerHTML = renderTransitList(data.return || [], "Keine Rückfahrten im Tagesfenster.");
  }
  if (data.full_day && transitFullCount) {
    const total = (data.outbound || []).length + (data.return || []).length;
    transitFullCount.textContent = total ? `${total} Fahrten` : "";
  } else if (transitFullCount && transitFullLoadingDate !== data.date) {
    transitFullCount.textContent = "Wird beim Öffnen geladen";
  }
  renderTransitView();
  updateTransitCountdowns();
}

function clearTransitRetry() {
  if (transitRetryTimer) {
    window.clearTimeout(transitRetryTimer);
    transitRetryTimer = 0;
  }
}

function renderTransitList(items, emptyText) {
  return items.length
    ? items.map((item) => renderTransitConnection(item, "")).join("")
    : `<div class="empty-state">${escapeHtml(emptyText)}</div>`;
}

function renderTransitConnection(item, emptyText, serviceDate = "", recommendation = false) {
  if (!item) {
    return `<div class="empty-state">${escapeHtml(emptyText)}</div>`;
  }
  const route = compact([
    item.from?.name,
    item.to?.name,
  ]).join(" -> ");
  const delayMinutes = Math.round(Number(item.delay_seconds || 0) / 60);
  const status = item.cancelled
    ? "Fällt aus"
    : item.realtime
      ? (delayMinutes ? `${delayMinutes > 0 ? "+" : ""}${delayMinutes} Min` : "Live")
      : "Sollzeit";
  const plannedTimes = item.realtime && (
    item.planned_departure !== item.departure || item.planned_arrival !== item.arrival
  )
    ? `Plan ${item.planned_departure}-${item.planned_arrival}`
    : "";
  const platform = item.realtime_platform || item.platform;
  const departureChanged = Boolean(item.planned_departure && item.departure && item.planned_departure !== item.departure);
  const arrivalChanged = Boolean(item.planned_arrival && item.arrival && item.planned_arrival !== item.arrival);
  const platformChanged = Boolean(item.realtime_platform && item.platform && item.realtime_platform !== item.platform);
  const hasChange = Boolean(item.cancelled || delayMinutes || departureChanged || arrivalChanged || platformChanged);
  const changeDetails = compact([
    item.cancelled ? "Diese Fahrt fällt aus." : "",
    departureChanged ? `Abfahrt geändert: ${item.planned_departure} → ${item.departure}` : "",
    arrivalChanged ? `Ankunft geändert: ${item.planned_arrival} → ${item.arrival}` : "",
    !item.cancelled && delayMinutes ? `${delayMinutes > 0 ? `${delayMinutes} Min später` : `${Math.abs(delayMinutes)} Min früher`}` : "",
    platformChanged ? `Steig geändert: ${item.platform} → ${item.realtime_platform}` : "",
  ]);
  const announcement = (item.announcements || [])[0];
  const departureDateTime = serviceDate && item.departure
    ? `${serviceDate}T${item.departure}:00`
    : "";
  const countdown = recommendation && departureDateTime && !item.cancelled
    ? `<span class="transit-countdown" data-transit-departure="${escapeHtml(departureDateTime)}">Abfahrtszeit wird berechnet</span>`
    : "";
  return `
    <div class="transit-connection${item.cancelled ? " is-cancelled" : ""}${hasChange && !item.cancelled ? " has-live-change" : ""}">
      <div class="transit-line">
        <strong>${escapeHtml(item.line || "Bus")}</strong>
        <div class="transit-line-status">
          ${hasChange ? `<span class="ci-badge" data-tone="${item.cancelled ? "danger" : "warn"}">Geändert</span>` : ""}
          <span class="transit-time${departureChanged || arrivalChanged ? " is-changed" : ""}">${escapeHtml(item.departure)}-${escapeHtml(item.arrival)}</span>
        </div>
      </div>
      ${countdown}
      ${changeDetails.length ? `<div class="transit-change-list" data-tone="${item.cancelled ? "danger" : "warn"}">${changeDetails.map((detail) => `<span>${escapeHtml(detail)}</span>`).join("")}</div>` : ""}
      <div class="transit-route">${escapeHtml(route)}</div>
      <small>${escapeHtml(compact([
        item.headsign,
        `${item.duration_minutes || 0} min`,
        status,
        plannedTimes,
        platform ? `Steig ${platform}` : "",
      ]).join(" | "))}</small>
      ${announcement ? `<div class="notice-row">${escapeHtml(announcement.summary || announcement.description || "Fahrplanhinweis")}</div>` : ""}
      ${recommendation ? renderVehicleStatus(item.vehicle) : ""}
    </div>
  `;
}

function renderVehicleStatus(vehicle) {
  if (!vehicle) return "";
  if (vehicle.status !== "available") {
    return `<div class="vehicle-status" data-status="${escapeHtml(vehicle.status || "unavailable")}">${escapeHtml(vehicle.message || "Keine echte Fahrzeugposition verfügbar.")}</div>`;
  }
  const track = Array.isArray(vehicle.track) ? vehicle.track : [];
  const position = vehicle.position || {};
  if (track.length < 2 || !Number.isFinite(Number(position.longitude)) || !Number.isFinite(Number(position.latitude))) {
    return `<div class="vehicle-status" data-status="unavailable">Keine verwertbare Fahrzeugposition verfügbar.</div>`;
  }
  const longitudes = track.map((point) => Number(point[0]));
  const latitudes = track.map((point) => Number(point[1]));
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const x = (value) => 12 + ((Number(value) - minLongitude) / Math.max(0.000001, maxLongitude - minLongitude)) * 296;
  const y = (value) => 78 - ((Number(value) - minLatitude) / Math.max(0.000001, maxLatitude - minLatitude)) * 66;
  const points = track.map((point) => `${x(point[0]).toFixed(1)},${y(point[1]).toFixed(1)}`).join(" ");
  const markerX = x(position.longitude).toFixed(1);
  const markerY = y(position.latitude).toFixed(1);
  const delay = Number(vehicle.delay_minutes || 0);
  const details = compact([
    "Live-Position",
    compact([vehicle.from, vehicle.to]).join(" → "),
    delay ? `${delay > 0 ? "+" : ""}${delay} Min` : "pünktlich",
  ]).join(" · ");
  return `
    <div class="vehicle-status" data-status="available">
      <div class="vehicle-status-label">${escapeHtml(details)}</div>
      <svg class="vehicle-map" viewBox="0 0 320 90" role="img" aria-label="Schematische Live-Position des Busses">
        <polyline points="${escapeHtml(points)}" />
        <circle class="vehicle-stop" cx="${x(track[0][0]).toFixed(1)}" cy="${y(track[0][1]).toFixed(1)}" r="4" />
        <circle class="vehicle-stop" cx="${x(track.at(-1)[0]).toFixed(1)}" cy="${y(track.at(-1)[1]).toFixed(1)}" r="4" />
        <circle class="vehicle-marker" cx="${markerX}" cy="${markerY}" r="7" />
      </svg>
    </div>
  `;
}

function updateTransitCountdowns() {
  document.querySelectorAll("[data-transit-departure]").forEach((element) => {
    const departure = new Date(element.dataset.transitDeparture || "");
    const differenceMinutes = Math.ceil((departure.getTime() - Date.now()) / 60000);
    if (!Number.isFinite(differenceMinutes)) {
      element.textContent = "";
    } else if (differenceMinutes <= 0) {
      element.textContent = "Abgefahren";
    } else if (differenceMinutes < 60) {
      element.textContent = `Abfahrt in ${differenceMinutes} Min`;
    } else {
      const hours = Math.floor(differenceMinutes / 60);
      const minutes = differenceMinutes % 60;
      element.textContent = `Abfahrt in ${hours} Std${minutes ? ` ${minutes} Min` : ""}`;
    }
  });
}

function startTransitLiveUpdates() {
  if (!transitRecommendations) return;
  updateTransitCountdowns();
  transitCountdownTimer = window.setInterval(updateTransitCountdowns, 30000);
  window.setInterval(() => {
    const date = selectedDayKey || isoDate(new Date());
    if (isTransitVisible() && date === isoDate(new Date()) && document.visibilityState === "visible") {
      refreshTransitData(false, true);
    }
  }, 60000);
}

function renderTimetableCell(slot, lessons) {
  const items = timetableCardsForSlot(slot, lessons);
  if (!items.length) {
    return `<div class="tt-cell"><span class="tt-empty">-</span></div>`;
  }

  return `
    <div class="tt-cell">
      ${items.map((item) => renderTimetableItem(item, slot)).join("")}
    </div>
  `;
}

function timetableCardsForSlot(slot, lessons) {
  const overlapping = lessons.filter((lesson) => lessonOverlapsSlot(lesson, slot));
  if (timetableMode === "actual") {
    return overlapping
      .filter((lesson) => lesson.status !== "cancelled")
      .map((lesson) => ({ type: "lesson", lesson }));
  }
  return changeCardsForSlot(overlapping).sort((left, right) => (
    cardStart(left).localeCompare(cardStart(right))
      || cardTitle(left).localeCompare(cardTitle(right))
  ));
}

function changeCardsForSlot(items) {
  const cancelled = items.filter((lesson) => lesson.status === "cancelled");
  const active = items.filter((lesson) => lesson.status !== "cancelled");
  const changed = active.filter((lesson) => lesson.status !== "regular" || hasRemovedDetails(lesson));
  const regular = active.filter((lesson) => lesson.status === "regular" && !hasRemovedDetails(lesson));
  const cards = [];

  if (changed.length === 1) {
    cards.push({ type: "change", lesson: changed[0], cancelled });
  } else if (changed.length > 1) {
    changed.forEach((lesson, index) => {
      const pairedCancelled = cancelled.length === changed.length ? [cancelled[index]].filter(Boolean) : [];
      cards.push({ type: "change", lesson, cancelled: pairedCancelled });
    });
    if (cancelled.length && cancelled.length !== changed.length) {
      cards.push({ type: "change", lesson: null, cancelled });
    }
  } else if (cancelled.length) {
    cards.push({ type: "change", lesson: null, cancelled });
  }

  regular.forEach((lesson) => cards.push({ type: "lesson", lesson }));
  return cards;
}

function renderTimetableItem(item, slot) {
  return item.type === "change"
    ? renderChangeCard(item, slot)
    : renderTimetableCard(item.lesson, slot);
}

function renderTimetableCard(lesson, slot) {
  const originalTime = `${lesson.start}-${lesson.end}`;
  const spansSlot = originalTime !== slot.label;
  const isChangeMode = timetableMode === "changes";
  const isRegularInChangeMode = isChangeMode && lesson.status === "regular";
  const details = compact([
    isRegularInChangeMode ? "" : spansSlot ? originalTime : "",
    isRegularInChangeMode ? "" : teacherLabel(lesson),
    isRegularInChangeMode ? "" : joinOr(lesson.room, ""),
    isRegularInChangeMode ? "" : lesson.substitution_text,
    isRegularInChangeMode ? "" : lesson.lesson_text,
    isRegularInChangeMode ? "" : lesson.info,
  ]).join(" | ");

  return `
    <div class="tt-card" data-status="${escapeHtml(lesson.status)}" data-source="${escapeHtml(lesson.source || "")}" data-timetable-mode="${escapeHtml(timetableMode)}">
      <div class="tt-card-top">
        <strong>${escapeHtml(joinOr(lesson.subject, lesson.lesson_text || "Termin"))}</strong>
        ${isChangeMode ? `<span class="ci-badge" data-tone="${toneForStatus(lesson.status)}">${escapeHtml(statusLabel(lesson.status))}</span>` : ""}
      </div>
      ${details ? `<small>${escapeHtml(details)}</small>` : ""}
    </div>
  `;
}

function renderChangeCard(item, slot) {
  const summary = summarizeChangeCard(item, slot);
  return `
    <div class="tt-card" data-status="${escapeHtml(summary.status)}" data-timetable-mode="changes">
      <div class="tt-card-top">
        <strong>${escapeHtml(summary.title)}</strong>
        <span class="ci-badge" data-tone="${toneForStatus(summary.status)}">${escapeHtml(statusLabel(summary.status))}</span>
      </div>
      ${summary.lines.map((line) => `<small class="tt-change-line">${escapeHtml(line)}</small>`).join("")}
    </div>
  `;
}

function summarizeChangeCard(item, slot) {
  const lesson = item.lesson;
  const cancelled = item.cancelled || [];
  const removed = lesson?.removed || {};
  const cancelledSubjects = uniqueList(cancelled.flatMap((entry) => entry.subject || []));
  const currentSubjects = uniqueList(lesson?.subject || []);
  const removedSubjects = uniqueList([...(removed.subject || []), ...cancelledSubjects]);
  const oldSubject = joinOr(removedSubjects, "");
  const newSubject = joinOr(currentSubjects, "");
  const subjectChanged = Boolean(oldSubject && newSubject && normalizedValue(oldSubject) !== normalizedValue(newSubject));
  const status = lesson ? (lesson.status === "regular" ? "regular" : "changed") : "cancelled";
  const title = subjectChanged
    ? `${oldSubject} -> ${newSubject}`
    : newSubject || oldSubject || lesson?.lesson_text || "Termin";
  const lines = [];

  if (!subjectChanged && lesson) {
    const teacherChange = changedFieldLine("Lehrkraft", removed.teacher, lesson.teacher, "offen");
    const roomChange = changedFieldLine("Raum", removed.room, lesson.room, "offen");
    if (teacherChange) lines.push(teacherChange);
    if (roomChange) lines.push(roomChange);
  }

  if (!lines.length && !subjectChanged) {
    const notes = compact([
      ...cancelled.map((entry) => entry.substitution_text),
      lesson?.substitution_text,
    ]);
    lines.push(...uniqueList(notes));
  }

  return {
    status,
    title,
    lines,
    start: lesson?.start || cancelled[0]?.start || slot.start,
  };
}

function renderMobileDay(day, lessons) {
  return `
    <section class="tt-mobile-day">
      <h3>${escapeHtml(formatDate(day))}</h3>
      ${FIXED_SLOTS.map((slot) => renderMobileSlot(slot, lessons)).join("")}
    </section>
  `;
}

function renderMobileSlot(slot, lessons) {
  const items = timetableCardsForSlot(slot, lessons);
  return `
    <div class="tt-mobile-slot">
      <div class="tt-mobile-time">${escapeHtml(slot.label)}</div>
      <div class="tt-mobile-items">
        ${items.length ? items.map((item) => renderTimetableItem(item, slot)).join("") : `<span class="tt-empty">-</span>`}
      </div>
    </div>
  `;
}

function renderLesson(lesson) {
  const tone = toneForStatus(lesson.status);
  return `
    <div class="lesson-row">
      <div class="lesson-time">${escapeHtml(lesson.start)}-${escapeHtml(lesson.end)}</div>
      <div class="lesson-main">
        <strong>${escapeHtml(joinOr(lesson.subject, "ohne Fach"))}</strong>
        <small>${escapeHtml(joinOr(lesson.teacher, "Lehrkraft nicht veröffentlicht"))}</small>
      </div>
      <div class="lesson-room">
        <strong>${escapeHtml(joinOr(lesson.room, "ohne Raum"))}</strong>
        <small>${escapeHtml(compact([lesson.substitution_text, lesson.lesson_text, lesson.info]).join(" | "))}</small>
      </div>
      <span class="ci-badge" data-tone="${tone}">${escapeHtml(statusLabel(lesson.status))}</span>
    </div>
  `;
}

function renderRuns(items) {
  if (!activityLog || !activityCount) return;
  if (!items.length) {
    if (runs) runs.innerHTML = `<div class="empty-state">Noch keine Läufe.</div>`;
    activityLog.textContent = "Noch keine Läufe.";
    activityCount.textContent = "0 runs";
    return;
  }

  if (runs) {
    runs.innerHTML = items
      .map((item) => {
        const tone = ["error", "notify_error", "transit_error", "transit_notify_error"].includes(item.status)
          ? "danger"
          : ["changed", "transit_changed"].includes(item.status)
            ? "warn"
            : "success";
        return `
          <div class="ci-card-row">
            <span class="ci-badge" data-tone="${tone}">${escapeHtml(item.status)}</span>
            <div>
              <strong>${escapeHtml(item.message)}</strong>
              <small>${escapeHtml(formatDateTime(item.timestamp))}</small>
            </div>
            <small>${item.changes_count} Änderungen</small>
          </div>
        `;
      })
      .join("");
  }

  activityLog.textContent = items
    .map((item) => `${formatDateTime(item.timestamp)} | ${statusText(item)} | Änderungen: ${item.changes_count} | E-Mail: ${emailStatus(item)} | ${item.message}`)
    .join("\n");
  activityCount.textContent = `${items.length} runs`;
}

function metric(value, label) {
  return `<div class="metric"><strong>${escapeHtml(String(value))}</strong><span>${escapeHtml(label)}</span></div>`;
}

function channelRow(label, enabled) {
  const tone = enabled ? "success" : "warn";
  const text = enabled ? "aktiv" : "aus";
  return `
    <div class="ci-card-row channel-row">
      <span class="ci-badge" data-tone="${tone}">${text}</span>
      <div>
        <strong>${escapeHtml(label)}</strong>
        <small>${enabled ? "Benachrichtigung konfiguriert" : "Nicht konfiguriert"}</small>
      </div>
    </div>
  `;
}

function configItem(label, value) {
  return `<div class="config-item"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`;
}

function formatChannels(items = []) {
  return items.length ? `Gesendet über: ${items.join(", ")}.` : "";
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("de-DE", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" }).format(date);
}

function updateWeekButtons() {
  document.querySelectorAll("[data-week]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.week === timetableWeek));
    if (button.dataset.week === "current") {
      button.textContent = isWeekendToday() ? "Letzte Woche" : "Diese Woche";
    }
  });
}

function updateLayoutButtons() {
  document.querySelectorAll("[data-layout]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.layout === timetableLayout));
  });
}

function updateTransitViewButtons() {
  document.querySelectorAll("[data-transit-view]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.transitView === transitView));
  });
}

function renderTransitView() {
  const fullView = transitView === "full";
  if (transitRecommendations) transitRecommendations.hidden = fullView;
  if (transitDayDetails) transitDayDetails.hidden = !fullView;
}

function updateHomeworkModeButtons() {
  document.querySelectorAll("[data-homework-mode]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.homeworkMode === homeworkMode));
  });
}

function initialTimetableWeek() {
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("week");
  if (requested === "current" || requested === "next") {
    return requested;
  }
  const day = new Date().getDay();
  return day === 0 || day === 6 ? "next" : "current";
}

function isWeekendToday() {
  const day = new Date().getDay();
  return day === 0 || day === 6;
}

function weekEntries(groupedDays, weekKey) {
  const start = weekStart(weekKey);
  return [0, 1, 2, 3, 4].map((offset) => {
    const day = addDays(start, offset);
    const key = isoDate(day);
    return [key, groupedDays[key] || []];
  });
}

function ensureSelectedDay(weekDays) {
  if (weekDays.some(([day]) => day === selectedDayKey)) {
    return;
  }

  const todayKey = isoDate(new Date());
  const todayEntry = weekDays.find(([day]) => day === todayKey);
  selectedDayKey = todayEntry ? todayKey : weekDays[0]?.[0] || "";
}

function renderDaySwitch(weekDays) {
  if (!daySwitch) return;
  daySwitch.hidden = timetableLayout !== "day";
  daySwitch.innerHTML = weekDays
    .map(([day]) => `
      <button type="button" data-day="${escapeHtml(day)}" aria-pressed="${day === selectedDayKey}">
        <span>${escapeHtml(weekday(day))}</span>
        <small>${escapeHtml(shortDate(day))}</small>
      </button>
    `)
    .join("");
  daySwitch.querySelectorAll("[data-day]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedDayKey = button.dataset.day || selectedDayKey;
      renderTimetable(latestSchedule);
    });
  });
}

function renderTransitDaySwitch() {
  if (!transitDaySwitch) return;
  const weekDays = weekEntries(latestSchedule, timetableWeek);
  ensureSelectedDay(weekDays);
  transitDaySwitch.innerHTML = weekDays
    .map(([day]) => `
      <button type="button" data-transit-day="${escapeHtml(day)}" aria-pressed="${day === selectedDayKey}">
        <span>${escapeHtml(weekday(day))}</span>
        <small>${escapeHtml(shortDate(day))}</small>
      </button>
    `)
    .join("");
  transitDaySwitch.querySelectorAll("[data-transit-day]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedDayKey = button.dataset.transitDay || selectedDayKey;
      resetTransitView(selectedDayKey);
      renderTimetable(latestSchedule);
      refreshTransitData();
    });
  });
}

function isTransitVisible() {
  const view = document.querySelector('[data-view="transit"]');
  return Boolean(view && !view.hidden);
}

function weekStart(weekKey) {
  const today = new Date();
  const weekday = today.getDay() || 7;
  const monday = addDays(today, 1 - weekday);
  return weekKey === "next" ? addDays(monday, 7) : monday;
}

function addDays(date, days) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

function isoDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isSchoolDay(value) {
  const date = new Date(`${value}T00:00:00`);
  const day = date.getDay();
  return day >= 1 && day <= 5;
}

function statusText(item) {
  return {
    baseline: "Basis",
    unchanged: "Ohne Änderung",
    changed: "Geändert",
    notify_error: "Mailfehler",
    transit_changed: "Bus geändert",
    transit_notify_error: "Bus-Mailfehler",
    transit_error: "Busfehler",
    exam_changed: "Klassenarbeit",
    exam_notify_skipped: "Klassenarbeit ohne Mail",
    exam_error: "Klassenarbeiten-Fehler",
    error: "Fehler",
    config_missing: "Setup fehlt",
    inactive: "Deaktiviert",
  }[item.status] || item.status || "-";
}

function emailStatus(item) {
  if ((item.notified_channels || []).includes("email")) {
    return "versendet";
  }
  if (item.notification_error) {
    return `Fehler: ${item.notification_error}`;
  }
  return "nicht gesendet";
}

function linesFromList(items = []) {
  return Array.isArray(items) ? items.join("\n") : "";
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("de-DE", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function parseDateTimeParts(value) {
  if (!value) {
    return { date: "", shortDate: "", weekday: "", time: "" };
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return { date: value, shortDate: value, weekday: "", time: "" };
  }
  return {
    date: new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" }).format(date),
    shortDate: new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit" }).format(date),
    weekday: new Intl.DateTimeFormat("de-DE", { weekday: "short" }).format(date),
    time: new Intl.DateTimeFormat("de-DE", { hour: "2-digit", minute: "2-digit" }).format(date),
  };
}

function renderSnapshotStamp(value) {
  if (!snapshotStamp) return;
  snapshotStamp.textContent = value
    ? `Stand: ${formatDateTime(value)}`
    : "Stand: noch kein Snapshot";
}

function statusLabel(value) {
  return {
    regular: "planmäßig",
    changed: "geändert",
    cancelled: "entfällt",
  }[value] || value || "offen";
}

function toneForStatus(value) {
  return value === "cancelled" ? "danger" : value === "changed" ? "warn" : "success";
}

function joinOr(items, fallback) {
  return Array.isArray(items) && items.length ? items.join(", ") : fallback;
}

function teacherLabel(lesson) {
  if (lesson.source === "manual" && (!Array.isArray(lesson.teacher) || !lesson.teacher.length)) {
    return "";
  }
  return Array.isArray(lesson.teacher) && lesson.teacher.length
    ? lesson.teacher.join(", ")
    : "Lehrkraft nicht veröffentlicht";
}

function lessonOverlapsSlot(lesson, slot) {
  const lessonStart = minutes(lesson.start);
  const lessonEnd = minutes(lesson.end);
  const slotStart = minutes(slot.start);
  const slotEnd = minutes(slot.end);
  if ([lessonStart, lessonEnd, slotStart, slotEnd].some((value) => value === null)) {
    return false;
  }
  return lessonStart < slotEnd && lessonEnd > slotStart;
}

function minutes(value) {
  if (!value || !value.includes(":")) {
    return null;
  }
  const [hours, mins] = value.split(":").map(Number);
  if (!Number.isFinite(hours) || !Number.isFinite(mins)) {
    return null;
  }
  return hours * 60 + mins;
}

function weekday(value) {
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("de-DE", { weekday: "short" }).format(date);
}

function shortDate(value) {
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit" }).format(date);
}

function weekdayName(value) {
  return ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"][value] || "-";
}

function compact(items) {
  return items.filter((item) => item && String(item).trim());
}

function uniqueList(items) {
  return [...new Set(compact(items).map((item) => String(item).trim()))];
}

function hasRemovedDetails(lesson) {
  const removed = lesson.removed || {};
  return Boolean(
    (removed.subject || []).length
      || (removed.teacher || []).length
      || (removed.room || []).length
  );
}

function changedFieldLine(label, beforeItems = [], afterItems = [], fallback) {
  const before = joinOr(uniqueList(beforeItems), "");
  const after = joinOr(uniqueList(afterItems), fallback);
  if (!before || normalizedValue(before) === normalizedValue(after)) {
    return "";
  }
  return `${label}: ${before} -> ${after}`;
}

function normalizedValue(value) {
  return String(value || "").replace(/\s+/g, " ").trim().toLowerCase();
}

function cardStart(item) {
  return item.lesson?.start || item.cancelled?.[0]?.start || "";
}

function cardTitle(item) {
  return item.lesson
    ? joinOr(item.lesson.subject, item.lesson.lesson_text || "Termin")
    : joinOr((item.cancelled || []).flatMap((lesson) => lesson.subject || []), "Termin");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

startIdleLogoutTimer();
startTransitLiveUpdates();

if (!loginForm && !setupForm) {
  refresh();
  setInterval(refresh, 30000);
}

function startIdleLogoutTimer() {
  if (!logoutButton) return;
  const timeoutMs = 30 * 60 * 1000;
  let timer = window.setTimeout(logoutForIdle, timeoutMs);
  const reset = () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(logoutForIdle, timeoutMs);
  };
  ["click", "keydown", "touchstart", "scroll", "change"].forEach((eventName) => {
    window.addEventListener(eventName, reset, { passive: true });
  });
}

async function logoutForIdle() {
  try {
    await fetchJson("/api/logout", { method: "POST" });
  } finally {
    window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname || "/app")}`);
  }
}
