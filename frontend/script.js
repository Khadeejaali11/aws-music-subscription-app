requestAnimationFrame(() => document.body.classList.remove("page-enter"));

const transitionTo = (url) => {
  document.body.classList.add("page-exit");
  setTimeout(() => (window.location.href = url), 400);
};

document.addEventListener("click", (e) => {
  const a = e.target.closest("a");
  if (a && a.href && !a.target && !a.hash) {
    e.preventDefault();
    transitionTo(a.href);
  }
});

window.addEventListener("pageshow", (e) => {
  if (e.persisted) document.body.classList.remove("page-exit");
});

const waveform = document.getElementById("waveform");
const BAR_COUNT = 48;

if (waveform) {
  for (let i = 0; i < BAR_COUNT; i++) {
    const bar = document.createElement("div");
    bar.className = "bar";

    const fromEdge = Math.min(i, BAR_COUNT - 1 - i);
    if (fromEdge < 4) bar.style.animationName = "wave-sm";
    else if (fromEdge < 9) bar.style.animationName = "wave-md";
    else bar.style.animationName = "wave-lg";

    bar.style.animationDuration = `${(Math.random() * 0.5 + 0.25).toFixed(2)}s`;
    bar.style.animationDelay = `${(Math.random() * 0.5).toFixed(2)}s`;
    bar.style.transformOrigin = "center";

    waveform.appendChild(bar);
  }
}

const emailEl    = document.getElementById("email");
const passwordEl = document.getElementById("password");
const errorBox   = document.getElementById("error-box");
const loginBtn   = document.getElementById("login-btn");

if (emailEl && passwordEl) {
  [emailEl, passwordEl].forEach((el) =>
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        if (window.location.pathname.includes("register.html")) {
          handleRegister();
        } else {
          handleLogin();
        }
      }
    })
  );

  [emailEl, passwordEl].forEach((el) =>
    el.addEventListener("input", () => {
      if (errorBox) errorBox.classList.remove("visible");
    })
  );
}

async function handleLogin() {
  const email    = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const btn      = document.getElementById("login-btn");

  hideError();

  if (!email || !password) {
    showError("email or password is invalid");
    return;
  }

  if (btn) btn.classList.add("loading");

  try {
    const res  = await fetch(`${BACKEND_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (data.success) {
      sessionStorage.setItem("email", email);
      sessionStorage.setItem("username", data.user_name);
      transitionTo("main.html");
    } else {
      showError("email or password is invalid");
    }
  } catch (err) {
    console.error("Login failed:", err);
    showError("Could not connect to backend");
  } finally {
    if (btn) btn.classList.remove("loading");
  }
}

async function handleRegister() {
  const email    = document.getElementById("email").value.trim();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const btn      = document.getElementById("register-btn") || document.getElementById("login-btn");

  hideError();

  if (!email || !username || !password) {
    showError("Please fill in all fields.");
    return;
  }

  if (btn) btn.classList.add("loading");

  try {
    const res  = await fetch(`${BACKEND_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, username, password })
    });
    const data = await res.json();

    if (data.success) {
      transitionTo("login.html");
    } else {
      showError(data.message || "The email already exists");
    }
  } catch (err) {
    console.error("Register failed:", err);
    showError("Could not connect to backend");
  } finally {
    if (btn) btn.classList.remove("loading");
  }
}

function logout() {
  sessionStorage.clear();
  transitionTo("login.html");
}

function showError(msg) {
  const errorText = document.getElementById("error-text");
  const errorBox  = document.getElementById("error-box");

  if (errorText) errorText.textContent = msg;
  if (errorBox)  errorBox.classList.add("visible");

  const card = document.querySelector(".card");
  if (card) {
    card.style.animation = "none";
    card.offsetHeight;
    card.style.animation = "shake 0.4s ease";
  }
}

function hideError() {
  const errorBox = document.getElementById("error-box");
  if (errorBox) errorBox.classList.remove("visible");
}

if (window.location.pathname.includes("main.html")) {
  if (!sessionStorage.getItem("email")) {
    window.location.href = "login.html";
  } else {
    const usernameDisplay = document.getElementById("username-display");
    if (usernameDisplay) {
      usernameDisplay.textContent = sessionStorage.getItem("username") || "User";
    }
  }
}

if (window.location.pathname.includes("register.html")) {
  ["email", "username", "password"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter") handleRegister();
      });
      el.addEventListener("input", hideError);
    }
  });
}

/* ============================================================
   MAIN PAGE
============================================================ */
let searchDebounceTimer = null;

if (window.location.pathname.includes("main.html")) {
  document.body.classList.add("main-page");

  const usernameDisplay = document.getElementById("username-display");
  if (usernameDisplay) {
    usernameDisplay.textContent = sessionStorage.getItem("username") || "User";
  }

  const storedEmail = sessionStorage.getItem("email");
  if (storedEmail) loadSubscriptions(storedEmail);

  const searchInput = document.getElementById("search-title");
  const searchBtn   = document.getElementById("search-btn");
  const searchExtra = document.getElementById("search-extra");

  const expandSearch = () => {
    searchInput.classList.add("expanded");
    searchExtra.classList.add("visible");
    searchInput.focus();
    collapseLibrary();
  };

  const collapseSearch = () => {
    searchInput.classList.remove("expanded");
    searchExtra.classList.remove("visible");
    searchInput.value = "";
    ["search-artist","search-album","search-year"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });
    const grid          = document.getElementById("results-grid");
    const resultsHeader = document.getElementById("results-header");
    const panelSearch   = document.querySelector(".panel-search");
    if (grid)          grid.innerHTML = "";
    if (resultsHeader) resultsHeader.classList.remove("visible");
    if (panelSearch)   panelSearch.classList.remove("results-showing");
  };

  searchBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (!searchInput.classList.contains("expanded")) {
      expandSearch();
    } else {
      clearTimeout(searchDebounceTimer);
      searchSongs();
    }
  });

  searchInput.addEventListener("click", () => {
    if (!searchInput.classList.contains("expanded")) expandSearch();
  });

  document.addEventListener("click", (e) => {
    if (
      !e.target.closest(".search-wrapper") &&
      !e.target.closest(".search-extra") &&
      !e.target.closest(".results-grid") &&
      !e.target.closest(".results-header") &&
      !e.target.closest(".panel-library") &&
      !e.target.closest(".navbar")
    ) {
      collapseSearch();
    }
  });

  // Live search — debounced 400ms
  ["search-title", "search-artist", "search-album", "search-year"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
          const title  = document.getElementById("search-title").value.trim();
          const artist = document.getElementById("search-artist")?.value.trim() || "";
          const album  = document.getElementById("search-album")?.value.trim()  || "";
          const year   = document.getElementById("search-year")?.value.trim()   || "";
          if (title || artist || album || year) searchSongs();
        }, 400);
      });

      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          clearTimeout(searchDebounceTimer);
          searchSongs();
        }
      });
    }
  });
}

function collapseLibrary() {
  const dashboard = document.getElementById("dashboard");
  if (dashboard) dashboard.classList.add("library-minimised");
}

function expandLibrary() {
  const dashboard = document.getElementById("dashboard");
  if (dashboard) dashboard.classList.remove("library-minimised");
}

async function loadSubscriptions(email) {
  try {
    const res   = await fetch(`${BACKEND_URL}/subscriptions/${encodeURIComponent(email)}`);
    const data  = await res.json();
    const songs = data.subscriptions || [];
    renderSubscriptions(songs);
  } catch (err) {
    console.error("Load subscriptions failed:", err);
    renderSubscriptions([]);
  }
}

function renderSubscriptions(songs) {
  const list       = document.getElementById("subscription-list");
  const emptyState = document.getElementById("empty-state");
  const countEl    = document.getElementById("sub-count");
  const collapsed  = document.getElementById("collapsed-count");

  if (!list) return;

  list.innerHTML = "";

  const label = `${songs.length} song${songs.length !== 1 ? "s" : ""}`;
  if (countEl)   countEl.textContent   = label;
  if (collapsed) collapsed.textContent = songs.length;

  if (songs.length === 0) {
    if (emptyState) emptyState.style.display = "flex";
    list.style.display = "none";
    return;
  }

  if (emptyState) emptyState.style.display = "none";
  list.style.display = "flex";

  songs.forEach((song, i) => {
    list.appendChild(createSubscriptionCard(song, i));
  });
}

function createSubscriptionCard(song, index) {
  const card = document.createElement("div");
  card.className = "song-card";
  card.style.animationDelay = `${index * 0.05}s`;

  card.innerHTML = `
    <img class="song-img" src="${song.image_url || ""}" alt="${song.artist || ""}" onerror="this.style.opacity='0.3'" />
    <div class="song-info">
      <div class="song-title">${song.title || ""}</div>
      <div class="song-meta">${song.artist || ""} · ${song.album || ""}</div>
      <div class="song-year">${song.year || ""}</div>
    </div>
    <button
      class="btn-remove"
      aria-label="Remove ${song.title || ""} from library"
      onclick="removeSubscription('${esc(song.title)}','${esc(song.artist)}','${esc(song.album)}','${esc(song.year)}')"
    >Remove</button>
  `;

  return card;
}

async function searchSongs() {
  const title  = document.getElementById("search-title").value.trim();
  const artist = document.getElementById("search-artist")?.value.trim() || "";
  const album  = document.getElementById("search-album")?.value.trim()  || "";
  const year   = document.getElementById("search-year")?.value.trim()   || "";

  const emptyMsg      = document.getElementById("search-empty-msg");
  const noResult      = document.getElementById("search-no-result");
  const resultsGrid   = document.getElementById("results-grid");
  const panelSearch   = document.querySelector(".panel-search");
  const resultsHeader = document.getElementById("results-header");

  emptyMsg.style.display = "none";
  noResult.style.display = "none";

  if (!title && !artist && !album && !year) {
    emptyMsg.style.display = "block";
    return;
  }

  // Smooth fade existing results while loading
  resultsGrid.classList.add("updating");

  try {
    const params = new URLSearchParams();
    if (title)  params.append("title", title);
    if (artist) params.append("artist", artist);
    if (album)  params.append("album", album);
    if (year)   params.append("year", year);

    const res   = await fetch(`${BACKEND_URL}/music/search?${params.toString()}`);
    const data  = await res.json();
    const songs = data.results || [];

    resultsGrid.classList.remove("updating");
    resultsGrid.innerHTML = "";

    if (songs.length === 0) {
      noResult.style.display = "block";
      return;
    }

    // Build query label
    const parts = [];
    if (title)  parts.push(title);
    if (artist) parts.push(artist);
    if (album)  parts.push(album);
    if (year)   parts.push(year);
    const queryLabel = parts.join(", ");

    document.getElementById("results-query-text").innerHTML =
      `Search results for <span>"${queryLabel}"</span>`;
    document.getElementById("results-count-text").textContent =
      `${songs.length} song${songs.length !== 1 ? "s" : ""} found`;

    resultsHeader.classList.add("visible");
    panelSearch.classList.add("results-showing");
    

    renderResults(songs);

  } catch (err) {
    console.error("Search failed:", err);
    resultsGrid.classList.remove("updating");
    noResult.style.display = "block";
  }
}

function refineSearch() {
  const panelSearch   = document.querySelector(".panel-search");
  const resultsHeader = document.getElementById("results-header");
  const searchInput   = document.getElementById("search-title");
  const searchExtra   = document.getElementById("search-extra");
  const resultsGrid   = document.getElementById("results-grid");

  panelSearch.classList.remove("results-showing");
  resultsHeader.classList.remove("visible");
  resultsGrid.innerHTML = "";

  setTimeout(() => {
    searchInput.classList.add("expanded");
    searchExtra.classList.add("visible");
    searchInput.focus();
  }, 100);
}

function renderResults(songs) {
  const grid = document.getElementById("results-grid");
  grid.innerHTML = "";

  const subList  = document.getElementById("subscription-list");
  const subCards = subList ? subList.querySelectorAll(".song-card") : [];
  const subKeys  = new Set();

  subCards.forEach((card) => {
    const t = card.querySelector(".song-title")?.textContent;
    const a = card.querySelector(".song-meta")?.textContent.split(" · ")[0];
    if (t && a) subKeys.add(`${t}__${a}`);
  });

  songs.forEach((song, i) => {
    const row = document.createElement("div");
    row.className = "song-row";
    row.style.animationDelay = `${i * 0.04}s`;

    const isSubscribed = subKeys.has(`${song.title}__${song.artist}`);

    row.innerHTML = `
      <img class="row-img" src="${song.image_url || ""}" alt="${song.artist || ""}" onerror="this.style.opacity='0.3'" />
      <div class="row-info">
        <div class="row-title">${song.title || ""}</div>
        <div class="row-meta">
          ${song.artist || ""}
          <span class="dot">·</span>
          ${song.album || ""}
          <span class="dot">·</span>
          ${song.year || ""}
        </div>
      </div>
      <div class="row-actions">
        ${isSubscribed
          ? `<button class="btn-row-subscribed" disabled aria-label="Already in library">✓ Saved</button>`
          : `<button class="btn-row-subscribe" aria-label="Subscribe to ${song.title || ""}"
               onclick="subscribeToSong('${esc(song.title)}','${esc(song.artist)}','${esc(song.album)}','${esc(song.year)}','${esc(song.image_url)}')">
               + Subscribe
             </button>`
        }
      </div>
    `;

    grid.appendChild(row);
  });
}

async function subscribeToSong(title, artist, album, year, image_url) {
  const email = sessionStorage.getItem("email");

  try {
    await fetch(`${BACKEND_URL}/subscriptions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, title, artist, album, year, image_url })
    });

    await loadSubscriptions(email);
    await searchSongs();
  } catch (err) {
    console.error("Subscribe failed:", err);
  }
}

async function removeSubscription(title, artist, album, year) {
  const email = sessionStorage.getItem("email");

  try {
    await fetch(`${BACKEND_URL}/subscriptions`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, title, artist, album, year })
    });

    await loadSubscriptions(email);
    await searchSongs();
  } catch (err) {
    console.error("Remove failed:", err);
  }
}

function esc(str) {
  return String(str || "")
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, "&quot;");
}