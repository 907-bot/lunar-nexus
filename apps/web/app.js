/**
 * NEXUS-LUNAR Layer 1: Lunar Data Explorer Client Engine
 * Features:
 * - REST API integration for multi-mission lunar observations
 * - Dual-Theme System (Dark Lunar Obsidian / Light Solar Albedo)
 * - Interactive 2D Lunar Projection Surface Map (Equirectangular IAU2000)
 * - Interactive 3D Lunar Digital Globe & Surface Visualization (Spherical IAU2000)
 * - Real-time 3D Footprint Projection, Solar Illumination Vectors, and Landmark Craters
 * - Overlapping Candidate Pair Discovery Engine
 */

// Application State
const state = {
  theme: localStorage.getItem('nexus_lunar_theme') || 'dark',
  viewMode: '2D', // '2D' or '3D'
  observations: [],
  filteredObservations: [],
  selectedObservation: null,
  activeSensor: 'ALL',
  searchQuery: '',
  maxResolution: 10.0,
  sortBy: 'res-asc',
  stats: null,
  overlappingPairs: [],
  
  // 2D Map Viewport (Center lon/lat & zoom)
  map: {
    centerLon: 26.0,
    centerLat: -73.5, // Default focus: Lunar South Pole (Boguslawsky target)
    zoom: 8.0,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    hoveredObs: null,
  },

  // 3D Lunar Globe State
  globe: {
    yaw: -0.45,        // Orientation facing Boguslawsky (26° Lon)
    pitch: -0.72,      // Tilted downwards so Lunar South Pole is prominent
    targetYaw: -0.45,
    targetPitch: -0.72,
    zoom: 1.05,
    autoOrbit: false,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    lastMouseX: 0,
    lastMouseY: 0,
    hoveredObs: null,
    pulsePhase: 0,
  }
};

// DOM Elements
const elements = {
  html: document.documentElement,
  themeToggleBtn: document.getElementById('btn-theme-toggle'),
  themeLabel: document.getElementById('theme-label'),
  statTotalObs: document.getElementById('stat-total-obs'),
  statResRange: document.getElementById('stat-res-range'),
  badgePairCount: document.getElementById('badge-pair-count'),
  btnTogglePairMode: document.getElementById('btn-toggle-pair-mode'),
  modalPairBackdrop: document.getElementById('modal-pair-backdrop'),
  btnClosePairModal: document.getElementById('btn-close-pair-modal'),
  modalPairsContainer: document.getElementById('modal-pairs-container'),
  
  // View Mode Buttons (2D / 3D)
  btnMode2D: document.getElementById('btn-mode-2d'),
  btnMode3D: document.getElementById('btn-mode-3d'),
  btnToggleOrbit: document.getElementById('btn-toggle-orbit'),

  // Filters & Search
  inputSearch: document.getElementById('input-search'),
  btnClearSearch: document.getElementById('btn-clear-search'),
  sensorChipsContainer: document.getElementById('sensor-chips-container'),
  btnResetFilters: document.getElementById('btn-reset-filters'),
  sliderRes: document.getElementById('slider-res'),
  labelResFilter: document.getElementById('label-res-filter'),
  selectSort: document.getElementById('select-sort'),
  filteredCountLabel: document.getElementById('filtered-count-label'),
  observationList: document.getElementById('observation-list'),
  
  // Sensor Counts
  countAll: document.getElementById('count-all'),
  countOhrc: document.getElementById('count-ohrc'),
  countLronac: document.getElementById('count-lronac'),
  countTmc2: document.getElementById('count-tmc2'),
  
  // Map Canvases
  canvas2D: document.getElementById('lunar-map-canvas'),
  canvas3D: document.getElementById('lunar-3d-canvas'),
  canvasContainer: document.getElementById('canvas-container'),
  hudMouseCoords: document.getElementById('hud-mouse-coords'),
  mapTooltip: document.getElementById('map-tooltip'),
  btnFocusSouthPole: document.getElementById('btn-focus-south-pole'),
  btnZoomIn: document.getElementById('btn-zoom-in'),
  btnZoomOut: document.getElementById('btn-zoom-out'),
  btnResetMap: document.getElementById('btn-reset-map'),
  
  // Inspector
  inspectorPanel: document.getElementById('inspector-panel'),
  btnCloseInspector: document.getElementById('btn-close-inspector'),
  inspectSensorTag: document.getElementById('inspect-sensor-tag'),
  inspectProductId: document.getElementById('inspect-product-id'),
  inspectResBadge: document.getElementById('inspect-res-badge'),
  inspectPreviewImg: document.getElementById('inspect-preview-img'),
  
  // Solar Dial
  dialSunVector: document.getElementById('dial-sun-vector'),
  dialSunHead: document.getElementById('dial-sun-head'),
  solarVectorLabel: document.getElementById('solar-vector-label'),
  mIncidence: document.getElementById('m-incidence'),
  mAzimuth: document.getElementById('m-azimuth'),
  mZenith: document.getElementById('m-zenith'),
  mPhase: document.getElementById('m-phase'),
  mEmission: document.getElementById('m-emission'),
  
  // Geo & Provenance
  mLatSpan: document.getElementById('m-lat-span'),
  mLonSpan: document.getElementById('m-lon-span'),
  pMission: document.getElementById('p-mission'),
  pSensor: document.getElementById('p-sensor'),
  pTime: document.getElementById('p-time'),
  pPath: document.getElementById('p-path'),
  btnFindPairsForThis: document.getElementById('btn-find-pairs-for-this'),
};

// Known Lunar Landmark Craters for map and 3D globe orientation
const LUNAR_LANDMARKS = [
  { name: 'Boguslawsky', lat: -72.9, lon: 26.2, radius: 97, primary: true, desc: 'Target Site (South Pole)' },
  { name: 'Shackleton', lat: -89.9, lon: 0.0, radius: 21, primary: true, desc: 'Lunar South Pole Rim' },
  { name: 'Manzinus', lat: -67.7, lon: 26.8, radius: 98 },
  { name: 'Tycho', lat: -43.3, lon: -11.2, radius: 86, desc: 'Ray Crater' },
  { name: 'Clavius', lat: -58.4, lon: -14.4, radius: 225 },
  { name: 'Copernicus', lat: 9.6, lon: -20.1, radius: 93 },
  { name: 'Apollo 17 Site', lat: 20.2, lon: 30.8, radius: 30, desc: 'Taurus-Littrow' },
];

// Major Lunar Maria (Basaltic volcanic plains) for realistic 3D sphere texturing
const LUNAR_MARIA = [
  { name: 'Oceanus Procellarum', lon: -40, lat: 20, rLon: 35, rLat: 30 },
  { name: 'Mare Imbrium', lon: -16, lat: 33, rLon: 22, rLat: 18 },
  { name: 'Mare Serenitatis', lon: 18, lat: 28, rLon: 16, rLat: 14 },
  { name: 'Mare Tranquillitatis', lon: 31, lat: 8, rLon: 18, rLat: 15 },
  { name: 'Mare Crisium', lon: 59, lat: 17, rLon: 14, rLat: 12 },
  { name: 'Mare Nubium', lon: -16, lat: -21, rLon: 18, rLat: 16 },
  { name: 'Mare Humorum', lon: -39, lat: -24, rLon: 12, rLat: 11 },
  { name: 'Mare Fecunditatis', lon: 51, lat: -3, rLon: 18, rLat: 15 },
  { name: 'Mare Nectaris', lon: 35, lat: -15, rLon: 12, rLat: 11 },
];

/* ==========================================================================
   1. Theme Management (Dark & Light Mode)
   ========================================================================== */

function applyTheme(theme) {
  state.theme = theme;
  elements.html.setAttribute('data-theme', theme);
  elements.themeLabel.textContent = theme === 'dark' ? 'DARK' : 'LIGHT';
  localStorage.setItem('nexus_lunar_theme', theme);
  
  if (state.viewMode === '2D') {
    render2DLunarMap();
  }
}

function toggleTheme() {
  const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
}

elements.themeToggleBtn.addEventListener('click', toggleTheme);

window.addEventListener('keydown', (e) => {
  if ((e.key === 't' || e.key === 'T') && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
    toggleTheme();
  }
});

/* ==========================================================================
   2. Data Fetching & API Services
   ========================================================================== */

async function initData() {
  applyTheme(state.theme);
  setup2DCanvas();
  setup3DCanvas();
  
  // Set initial view mode
  setViewMode('2D');
  
  try {
    await Promise.all([
      fetchCatalogStats(),
      fetchObservations(),
      fetchOverlappingPairs(),
    ]);
  } catch (err) {
    console.error('Data initialization error:', err);
  }

  // Start 3D animation loop
  start3DAnimationLoop();
}

async function fetchCatalogStats() {
  try {
    const res = await fetch('/api/v1/catalog/stats');
    if (!res.ok) return;
    const stats = await res.json();
    state.stats = stats;
    
    elements.statTotalObs.textContent = `${stats.total_observations} Products`;
    if (stats.resolution_range) {
      elements.statResRange.textContent = `${stats.resolution_range.min_m}m – ${stats.resolution_range.max_m}m`;
    }
  } catch (e) {
    console.warn('Could not load stats:', e);
  }
}

async function fetchObservations() {
  try {
    const res = await fetch('/api/v1/observations?limit=100');
    if (!res.ok) throw new Error('Failed to fetch observations');
    const data = await res.json();
    state.observations = data.items || [];
    
    updateSensorCounts();
    applyFilters();
    
    if (state.observations.length > 0 && !state.selectedObservation) {
      selectObservation(state.observations[0], false);
    }
  } catch (e) {
    console.error('Error fetching observations:', e);
    elements.observationList.innerHTML = `<div class="loading-state">Error loading catalog: ${e.message}</div>`;
  }
}

async function fetchOverlappingPairs() {
  try {
    const res = await fetch('/api/v1/pairs/overlapping?source=OHRC&reference=LRO_NAC');
    if (!res.ok) return;
    const data = await res.json();
    state.overlappingPairs = data.pairs || [];
    elements.badgePairCount.textContent = state.overlappingPairs.length;
  } catch (e) {
    console.warn('Could not load overlapping pairs:', e);
  }
}

function updateSensorCounts() {
  let ohrc = 0, lronac = 0, tmc2 = 0;
  state.observations.forEach(o => {
    if (o.sensor === 'OHRC') ohrc++;
    else if (o.sensor === 'LRO_NAC') lronac++;
    else if (o.sensor === 'TMC2') tmc2++;
  });
  
  elements.countAll.textContent = state.observations.length;
  elements.countOhrc.textContent = ohrc;
  elements.countLronac.textContent = lronac;
  elements.countTmc2.textContent = tmc2;
}

/* ==========================================================================
   3. Filtering & List Presentation
   ========================================================================== */

function applyFilters() {
  let list = [...state.observations];
  
  if (state.activeSensor !== 'ALL') {
    list = list.filter(o => o.sensor === state.activeSensor);
  }
  
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    list = list.filter(o => 
      (o.product_id && o.product_id.toLowerCase().includes(q)) ||
      (o.sensor && o.sensor.toLowerCase().includes(q)) ||
      (o.mission && o.mission.toLowerCase().includes(q))
    );
  }
  
  list = list.filter(o => {
    const r = o.spatial_resolution_m;
    return r == null || r <= state.maxResolution;
  });
  
  if (state.sortBy === 'res-asc') {
    list.sort((a, b) => (a.spatial_resolution_m || 999) - (b.spatial_resolution_m || 999));
  } else if (state.sortBy === 'time-desc') {
    list.sort((a, b) => new Date(b.acquisition_time || 0) - new Date(a.acquisition_time || 0));
  } else if (state.sortBy === 'sensor') {
    list.sort((a, b) => a.sensor.localeCompare(b.sensor));
  }
  
  state.filteredObservations = list;
  elements.filteredCountLabel.textContent = `Showing ${list.length} of ${state.observations.length} observations`;
  renderObservationList();
  
  if (state.viewMode === '2D') {
    render2DLunarMap();
  }
}

function renderObservationList() {
  if (state.filteredObservations.length === 0) {
    elements.observationList.innerHTML = `<div class="loading-state">No matching lunar observations found.</div>`;
    return;
  }
  
  elements.observationList.innerHTML = '';
  
  state.filteredObservations.forEach(obs => {
    const isSelected = state.selectedObservation && state.selectedObservation.product_id === obs.product_id;
    const card = document.createElement('div');
    card.className = `obs-card ${isSelected ? 'selected' : ''}`;
    card.dataset.productId = obs.product_id;
    
    let badgeClass = 'badge-ohrc';
    if (obs.sensor === 'LRO_NAC') badgeClass = 'badge-lronac';
    else if (obs.sensor === 'TMC2') badgeClass = 'badge-tmc2';
    
    const previewUrl = `/api/v1/observations/${encodeURIComponent(obs.product_id)}/preview`;
    const incidence = obs.geometry?.incidence_angle_deg != null ? `${obs.geometry.incidence_angle_deg.toFixed(1)}° inc` : '--';
    const res = obs.spatial_resolution_m != null ? `${obs.spatial_resolution_m}m` : '--';
    
    card.innerHTML = `
      <div class="obs-thumb-wrap">
        <img class="obs-thumb-img" src="${previewUrl}" alt="Thumb" onerror="this.onerror=null; this.parentElement.innerHTML='<span class=\\'obs-thumb-placeholder\\'>${obs.sensor}</span>';">
      </div>
      <div class="obs-details">
        <div class="obs-header-row">
          <span class="obs-sensor-badge ${badgeClass}">${obs.sensor}</span>
          <span class="obs-res-tag">${res}</span>
        </div>
        <div class="obs-pid" title="${obs.product_id}">${obs.product_id}</div>
        <div class="obs-meta-row">
          <span>${obs.mission}</span>
          <span>${incidence}</span>
        </div>
      </div>
    `;
    
    card.addEventListener('click', () => {
      selectObservation(obs, true);
    });
    
    elements.observationList.appendChild(card);
  });
}

function selectObservation(obs, panToCenter = true) {
  state.selectedObservation = obs;
  
  document.querySelectorAll('.obs-card').forEach(c => {
    c.classList.toggle('selected', c.dataset.productId === obs.product_id);
  });
  
  populateInspector(obs);
  
  if (panToCenter && obs.bbox) {
    const centerLon = (obs.bbox.min_lon + obs.bbox.max_lon) / 2.0;
    const centerLat = (obs.bbox.min_lat + obs.bbox.max_lat) / 2.0;
    
    // 2D Map Pan
    state.map.centerLon = centerLon;
    state.map.centerLat = centerLat;
    
    // 3D Globe Smooth Rotation to Target
    const targetYaw = -centerLon * (Math.PI / 180.0);
    const targetPitch = centerLat * (Math.PI / 180.0);
    state.globe.targetYaw = targetYaw;
    state.globe.targetPitch = targetPitch;
  }
  
  if (state.viewMode === '2D') {
    render2DLunarMap();
  }
}

function populateInspector(obs) {
  elements.inspectorPanel.classList.remove('collapsed');
  elements.inspectSensorTag.textContent = `${obs.mission} // ${obs.sensor}`;
  elements.inspectProductId.textContent = obs.product_id;
  elements.inspectProductId.title = obs.product_id;
  elements.inspectResBadge.textContent = `${obs.spatial_resolution_m ?? '--'}m / pixel`;
  
  const previewUrl = `/api/v1/observations/${encodeURIComponent(obs.product_id)}/preview`;
  elements.inspectPreviewImg.src = previewUrl;
  elements.inspectPreviewImg.onerror = () => {
    elements.inspectPreviewImg.style.display = 'none';
  };
  elements.inspectPreviewImg.onload = () => {
    elements.inspectPreviewImg.style.display = 'block';
  };
  
  const geom = obs.geometry || {};
  const az = geom.solar_azimuth_deg != null ? geom.solar_azimuth_deg : 45.0;
  const inc = geom.incidence_angle_deg != null ? `${geom.incidence_angle_deg.toFixed(1)}°` : '--';
  const zen = geom.solar_zenith_deg != null ? `${geom.solar_zenith_deg.toFixed(1)}°` : '--';
  const ph = geom.phase_angle_deg != null ? `${geom.phase_angle_deg.toFixed(1)}°` : '--';
  const em = geom.emission_angle_deg != null ? `${geom.emission_angle_deg.toFixed(1)}°` : '--';
  
  elements.mIncidence.textContent = inc;
  elements.mAzimuth.textContent = geom.solar_azimuth_deg != null ? `${geom.solar_azimuth_deg.toFixed(1)}°` : '--';
  elements.mZenith.textContent = zen;
  elements.mPhase.textContent = ph;
  elements.mEmission.textContent = em;
  elements.solarVectorLabel.textContent = `Sun Azimuth: ${az.toFixed(1)}°`;
  
  const rad = (az - 90) * (Math.PI / 180.0);
  const cx = 60, cy = 60, r = 40;
  const vx = cx + r * Math.cos(rad);
  const vy = cy + r * Math.sin(rad);
  
  elements.dialSunVector.setAttribute('x2', vx);
  elements.dialSunVector.setAttribute('y2', vy);
  elements.dialSunHead.setAttribute('cx', vx);
  elements.dialSunHead.setAttribute('cy', vy);
  
  const bb = obs.bbox || {};
  elements.mLatSpan.textContent = `${bb.min_lat?.toFixed(2)}° to ${bb.max_lat?.toFixed(2)}°`;
  elements.mLonSpan.textContent = `${bb.min_lon?.toFixed(2)}° to ${bb.max_lon?.toFixed(2)}°`;
  
  elements.pMission.textContent = obs.mission || '--';
  elements.pSensor.textContent = obs.sensor || '--';
  elements.pTime.textContent = obs.acquisition_time ? obs.acquisition_time.replace('T', ' ').slice(0, 19) : 'Undated';
  elements.pPath.textContent = obs.primary_local_rel || obs.preview_local_rel || 'Archived in PDS';
}

/* ==========================================================================
   4. View Mode Switching (2D Map vs 3D Lunar Globe)
   ========================================================================== */

function setViewMode(mode) {
  state.viewMode = mode;
  
  if (mode === '2D') {
    elements.btnMode2D.classList.add('active');
    elements.btnMode3D.classList.remove('active');
    elements.canvas2D.style.display = 'block';
    elements.canvas3D.style.display = 'none';
    elements.btnToggleOrbit.style.display = 'none';
    render2DLunarMap();
  } else {
    elements.btnMode3D.classList.add('active');
    elements.btnMode2D.classList.remove('active');
    elements.canvas2D.style.display = 'none';
    elements.canvas3D.style.display = 'block';
    elements.btnToggleOrbit.style.display = 'inline-flex';
    updateOrbitButtonText();
    render3DLunarGlobe();
  }
}

elements.btnMode2D.addEventListener('click', () => setViewMode('2D'));
elements.btnMode3D.addEventListener('click', () => setViewMode('3D'));

elements.btnToggleOrbit.addEventListener('click', () => {
  state.globe.autoOrbit = !state.globe.autoOrbit;
  updateOrbitButtonText();
});

function updateOrbitButtonText() {
  elements.btnToggleOrbit.textContent = state.globe.autoOrbit ? 'Auto Orbit: ON' : 'Auto Orbit: OFF';
  elements.btnToggleOrbit.classList.toggle('text-accent', state.globe.autoOrbit);
}

/* ==========================================================================
   5. Interactive 2D Lunar Surface Footprint Map Engine
   ========================================================================== */

function setup2DCanvas() {
  const canvas = elements.canvas2D;
  const ctx = canvas.getContext('2d');
  
  function resize() {
    const rect = elements.canvasContainer.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    if (state.viewMode === '2D') render2DLunarMap();
  }
  
  window.addEventListener('resize', resize);
  setTimeout(resize, 50);
  
  canvas.addEventListener('mousedown', (e) => {
    state.map.isDragging = true;
    state.map.dragStartX = e.clientX;
    state.map.dragStartY = e.clientY;
  });
  
  window.addEventListener('mousemove', (e) => {
    if (state.viewMode !== '2D') return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const coords = screenToLonLat(mouseX, mouseY, rect.width, rect.height);
    elements.hudMouseCoords.textContent = `LAT: ${coords.lat.toFixed(2)}° | LON: ${coords.lon.toFixed(2)}°`;
    
    if (state.map.isDragging) {
      const dx = e.clientX - state.map.dragStartX;
      const dy = e.clientY - state.map.dragStartY;
      state.map.dragStartX = e.clientX;
      state.map.dragStartY = e.clientY;
      
      const lonSpan = 360 / state.map.zoom;
      const latSpan = 180 / state.map.zoom;
      
      state.map.centerLon -= (dx / rect.width) * lonSpan;
      state.map.centerLat += (dy / rect.height) * latSpan;
      state.map.centerLat = Math.max(-89.5, Math.min(89.5, state.map.centerLat));
      render2DLunarMap();
    } else {
      check2DFootprintHover(mouseX, mouseY, rect.width, rect.height, e.clientX, e.clientY);
    }
  });
  
  window.addEventListener('mouseup', () => {
    state.map.isDragging = false;
  });
  
  canvas.addEventListener('wheel', (e) => {
    if (state.viewMode !== '2D') return;
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.25 : 0.8;
    state.map.zoom = Math.max(1.0, Math.min(60.0, state.map.zoom * zoomFactor));
    render2DLunarMap();
  }, { passive: false });
  
  canvas.addEventListener('click', () => {
    if (state.viewMode === '2D' && state.map.hoveredObs) {
      selectObservation(state.map.hoveredObs, false);
    }
  });
}

function lonLatToScreen(lon, lat, width, height) {
  const lonSpan = 360 / state.map.zoom;
  const latSpan = 180 / state.map.zoom;
  const minLon = state.map.centerLon - lonSpan / 2;
  const maxLat = state.map.centerLat + latSpan / 2;
  const x = ((lon - minLon) / lonSpan) * width;
  const y = ((maxLat - lat) / latSpan) * height;
  return { x, y };
}

function screenToLonLat(x, y, width, height) {
  const lonSpan = 360 / state.map.zoom;
  const latSpan = 180 / state.map.zoom;
  const minLon = state.map.centerLon - lonSpan / 2;
  const maxLat = state.map.centerLat + latSpan / 2;
  const lon = minLon + (x / width) * lonSpan;
  const lat = maxLat - (y / height) * latSpan;
  return { lon, lat };
}

function render2DLunarMap() {
  const canvas = elements.canvas2D;
  const ctx = canvas.getContext('2d');
  const rect = elements.canvasContainer.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  
  if (width === 0 || height === 0) return;
  const isDark = state.theme === 'dark';
  
  ctx.fillStyle = isDark ? '#06080d' : '#e2e8f0';
  ctx.fillRect(0, 0, width, height);
  
  draw2DMapGrid(ctx, width, height, isDark);
  draw2DLandmarks(ctx, width, height, isDark);
  draw2DFootprints(ctx, width, height, isDark);
}

function draw2DMapGrid(ctx, width, height, isDark) {
  ctx.lineWidth = 1;
  ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.06)';
  ctx.fillStyle = isDark ? '#64748b' : '#94a3b8';
  ctx.font = '10px "JetBrains Mono", monospace';
  
  const lonSpan = 360 / state.map.zoom;
  const latSpan = 180 / state.map.zoom;
  
  let step = 10;
  if (state.map.zoom > 15) step = 1;
  else if (state.map.zoom > 5) step = 5;
  else if (state.map.zoom < 2) step = 30;
  
  const minLon = Math.floor((state.map.centerLon - lonSpan / 2) / step) * step;
  const maxLon = Math.ceil((state.map.centerLon + lonSpan / 2) / step) * step;
  const minLat = Math.floor((state.map.centerLat - latSpan / 2) / step) * step;
  const maxLat = Math.ceil((state.map.centerLat + latSpan / 2) / step) * step;
  
  for (let lon = minLon; lon <= maxLon; lon += step) {
    const p1 = lonLatToScreen(lon, 90, width, height);
    ctx.beginPath();
    ctx.moveTo(p1.x, 0);
    ctx.lineTo(p1.x, height);
    ctx.stroke();
    ctx.fillText(`${lon}°`, p1.x + 4, height - 8);
  }
  
  for (let lat = minLat; lat <= maxLat; lat += step) {
    if (lat < -90 || lat > 90) continue;
    const p = lonLatToScreen(0, lat, width, height);
    ctx.beginPath();
    ctx.moveTo(0, p.y);
    ctx.lineTo(width, p.y);
    ctx.stroke();
    
    if (lat === 0) {
      ctx.strokeStyle = isDark ? 'rgba(0, 240, 255, 0.2)' : 'rgba(2, 132, 199, 0.2)';
      ctx.stroke();
      ctx.fillText('LUNAR EQUATOR 0°', 10, p.y - 4);
      ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.06)';
    } else if (lat === -70 || lat === -80) {
      ctx.fillText(`${lat}° (South Polar Domain)`, 10, p.y - 4);
    } else {
      ctx.fillText(`${lat}°`, 10, p.y - 4);
    }
  }
}

function draw2DLandmarks(ctx, width, height, isDark) {
  LUNAR_LANDMARKS.forEach(crater => {
    const pos = lonLatToScreen(crater.lon, crater.lat, width, height);
    if (pos.x < -100 || pos.x > width + 100 || pos.y < -100 || pos.y > height + 100) return;
    
    ctx.strokeStyle = crater.primary ? (isDark ? '#38bdf8' : '#0284c7') : (isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)');
    ctx.lineWidth = crater.primary ? 2 : 1;
    ctx.setLineDash([3, 3]);
    
    const displayRadius = Math.max(8, (crater.radius / 15.0) * (state.map.zoom / 4.0));
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, displayRadius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    
    ctx.fillStyle = crater.primary ? (isDark ? '#00f0ff' : '#0284c7') : (isDark ? '#94a3b8' : '#64748b');
    ctx.font = `${crater.primary ? '600' : '400'} 10px "JetBrains Mono", monospace`;
    ctx.fillText(`⌖ ${crater.name}`, pos.x + displayRadius + 4, pos.y + 4);
  });
}

function draw2DFootprints(ctx, width, height, isDark) {
  const obsList = state.filteredObservations.length > 0 ? state.filteredObservations : state.observations;
  
  obsList.forEach(obs => {
    const isSelected = state.selectedObservation && state.selectedObservation.product_id === obs.product_id;
    if (!isSelected) {
      renderSingle2DFootprint(ctx, obs, width, height, false);
    }
  });
  
  if (state.selectedObservation) {
    renderSingle2DFootprint(ctx, state.selectedObservation, width, height, true);
  }
}

function renderSingle2DFootprint(ctx, obs, width, height, isSelected) {
  const bb = obs.bbox;
  if (!bb) return;
  
  const tl = lonLatToScreen(bb.min_lon, bb.max_lat, width, height);
  const br = lonLatToScreen(bb.max_lon, bb.min_lat, width, height);
  const w = br.x - tl.x;
  const h = br.y - tl.y;
  
  let strokeColor = '#00f0ff';
  let fillColor = 'rgba(0, 240, 255, 0.15)';
  if (obs.sensor === 'LRO_NAC') {
    strokeColor = '#f43f5e';
    fillColor = 'rgba(244, 63, 94, 0.15)';
  } else if (obs.sensor === 'TMC2') {
    strokeColor = '#10b981';
    fillColor = 'rgba(16, 185, 129, 0.15)';
  }
  
  ctx.save();
  if (isSelected) {
    ctx.lineWidth = 3;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = fillColor.replace('0.15', '0.35');
    ctx.shadowColor = strokeColor;
    ctx.shadowBlur = 12;
  } else {
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = fillColor;
  }
  
  ctx.fillRect(tl.x, tl.y, w, h);
  ctx.strokeRect(tl.x, tl.y, w, h);
  
  const markerLen = Math.min(10, Math.min(w, h) / 3);
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = strokeColor;
  
  ctx.beginPath();
  ctx.moveTo(tl.x, tl.y + markerLen); ctx.lineTo(tl.x, tl.y); ctx.lineTo(tl.x + markerLen, tl.y);
  ctx.moveTo(tl.x + w - markerLen, tl.y); ctx.lineTo(tl.x + w, tl.y); ctx.lineTo(tl.x + w, tl.y + markerLen);
  ctx.moveTo(tl.x, tl.y + h - markerLen); ctx.lineTo(tl.x, tl.y + h); ctx.lineTo(tl.x + markerLen, tl.y + h);
  ctx.moveTo(tl.x + w - markerLen, tl.y + h); ctx.lineTo(tl.x + w, tl.y + h); ctx.lineTo(tl.x + w, tl.y + h - markerLen);
  ctx.stroke();
  
  if (state.map.zoom >= 3.0) {
    ctx.fillStyle = strokeColor;
    ctx.font = '600 9px "JetBrains Mono", monospace';
    ctx.fillText(`${obs.sensor} [${obs.spatial_resolution_m}m]`, tl.x + 4, tl.y + 12);
  }
  
  ctx.restore();
}

function check2DFootprintHover(screenX, screenY, width, height, clientX, clientY) {
  let matched = null;
  const obsList = state.filteredObservations.length > 0 ? state.filteredObservations : state.observations;
  
  for (let i = obsList.length - 1; i >= 0; i--) {
    const obs = obsList[i];
    const bb = obs.bbox;
    if (!bb) continue;
    
    const tl = lonLatToScreen(bb.min_lon, bb.max_lat, width, height);
    const br = lonLatToScreen(bb.max_lon, bb.min_lat, width, height);
    
    if (screenX >= tl.x && screenX <= br.x && screenY >= tl.y && screenY <= br.y) {
      matched = obs;
      break;
    }
  }
  
  state.map.hoveredObs = matched;
  
  if (matched) {
    elements.canvas2D.style.cursor = 'pointer';
    elements.mapTooltip.style.display = 'block';
    elements.mapTooltip.style.left = `${clientX}px`;
    elements.mapTooltip.style.top = `${clientY}px`;
    elements.mapTooltip.innerHTML = `
      <strong>${matched.sensor}</strong> (${matched.spatial_resolution_m}m)<br>
      <span style="opacity:0.8">${matched.product_id}</span>
    `;
  } else {
    elements.canvas2D.style.cursor = state.map.isDragging ? 'grabbing' : 'grab';
    elements.mapTooltip.style.display = 'none';
  }
}

/* ==========================================================================
   6. 3D Lunar Digital Globe & Surface Visualization Engine
   ========================================================================== */

function setup3DCanvas() {
  const canvas = elements.canvas3D;
  const ctx = canvas.getContext('2d');
  
  function resize() {
    const rect = elements.canvasContainer.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    if (state.viewMode === '3D') render3DLunarGlobe();
  }
  
  window.addEventListener('resize', resize);
  setTimeout(resize, 50);
  
  // 3D Globe Drag & Rotate
  canvas.addEventListener('mousedown', (e) => {
    state.globe.isDragging = true;
    state.globe.dragStartX = e.clientX;
    state.globe.dragStartY = e.clientY;
    state.globe.lastMouseX = e.clientX;
    state.globe.lastMouseY = e.clientY;
  });
  
  window.addEventListener('mousemove', (e) => {
    if (state.viewMode !== '3D') return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Find lunar coordinate directly under cursor on the 3D globe
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const R = Math.min(rect.width, rect.height) * 0.38 * state.globe.zoom;
    const dx = mouseX - cx;
    const dy = mouseY - cy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    
    if (dist <= R) {
      const lonLat = screen3DToLonLat(dx, dy, R);
      if (lonLat) {
        elements.hudMouseCoords.textContent = `LAT: ${lonLat.lat.toFixed(2)}° | LON: ${lonLat.lon.toFixed(2)}° (3D SPHERE)`;
      }
    } else {
      elements.hudMouseCoords.textContent = `ORBIT VIEW // SPACE REGION`;
    }
    
    if (state.globe.isDragging) {
      const deltaX = e.clientX - state.globe.lastMouseX;
      const deltaY = e.clientY - state.globe.lastMouseY;
      state.globe.lastMouseX = e.clientX;
      state.globe.lastMouseY = e.clientY;
      
      state.globe.yaw += deltaX * 0.007;
      state.globe.pitch += deltaY * 0.007;
      
      // Clamp pitch to avoid gimbal flip
      state.globe.pitch = Math.max(-Math.PI / 2 + 0.05, Math.min(Math.PI / 2 - 0.05, state.globe.pitch));
      state.globe.targetYaw = state.globe.yaw;
      state.globe.targetPitch = state.globe.pitch;
    } else {
      check3DFootprintHover(mouseX, mouseY, rect.width, rect.height, e.clientX, e.clientY);
    }
  });
  
  window.addEventListener('mouseup', () => {
    state.globe.isDragging = false;
  });
  
  // 3D Wheel Zoom
  canvas.addEventListener('wheel', (e) => {
    if (state.viewMode !== '3D') return;
    e.preventDefault();
    const zoomDelta = e.deltaY < 0 ? 1.15 : 0.88;
    state.globe.zoom = Math.max(0.6, Math.min(4.5, state.globe.zoom * zoomDelta));
  }, { passive: false });
  
  // 3D Footprint Click Selection
  canvas.addEventListener('click', () => {
    if (state.viewMode === '3D' && state.globe.hoveredObs) {
      selectObservation(state.globe.hoveredObs, false);
    }
  });
}

// 3D Spherical Trigonometry Projection
function project3D(lonDeg, latDeg, R) {
  const lambda = lonDeg * (Math.PI / 180.0);
  const phi = latDeg * (Math.PI / 180.0);
  
  // Standard 3D Cartesian coordinates on unit sphere
  const x0 = R * Math.cos(phi) * Math.sin(lambda);
  const y0 = R * Math.sin(phi);
  const z0 = R * Math.cos(phi) * Math.cos(lambda);
  
  // 1. Yaw rotation around Y-axis
  const cosY = Math.cos(state.globe.yaw);
  const sinY = Math.sin(state.globe.yaw);
  const x1 = x0 * cosY + z0 * sinY;
  const z1 = -x0 * sinY + z0 * cosY;
  const y1 = y0;
  
  // 2. Pitch rotation around X-axis
  const cosP = Math.cos(state.globe.pitch);
  const sinP = Math.sin(state.globe.pitch);
  const y2 = y1 * cosP - z1 * sinP;
  const z2 = y1 * sinP + z1 * cosP;
  const x2 = x1;
  
  return { x: x2, y: y2, z: z2, isVisible: z2 > 0 };
}

function screen3DToLonLat(dx, dy, R) {
  const x2 = dx;
  const y2 = -dy;
  const rSq = dx * dx + dy * dy;
  if (rSq > R * R) return null;
  const z2 = Math.sqrt(R * R - rSq);
  
  // Inverse Pitch rotation around X
  const cosP = Math.cos(-state.globe.pitch);
  const sinP = Math.sin(-state.globe.pitch);
  const y1 = y2 * cosP - z2 * sinP;
  const z1 = y2 * sinP + z2 * cosP;
  const x1 = x2;
  
  // Inverse Yaw rotation around Y
  const cosY = Math.cos(-state.globe.yaw);
  const sinY = Math.sin(-state.globe.yaw);
  const x0 = x1 * cosY + z1 * sinY;
  const z0 = -x1 * sinY + z1 * cosY;
  const y0 = y1;
  
  const phi = Math.asin(Math.max(-1, Math.min(1, y0 / R)));
  const lambda = Math.atan2(x0, z0);
  
  return {
    lat: phi * (180.0 / Math.PI),
    lon: lambda * (180.0 / Math.PI),
  };
}

// 3D Animation & Rendering Loop (Runs at 60 FPS)
function start3DAnimationLoop() {
  function loop() {
    if (state.viewMode === '3D') {
      // Auto-Orbit if enabled
      if (state.globe.autoOrbit && !state.globe.isDragging) {
        state.globe.yaw += 0.003;
        state.globe.targetYaw = state.globe.yaw;
      } else {
        // Smooth camera damping interpolation
        state.globe.yaw += (state.globe.targetYaw - state.globe.yaw) * 0.08;
        state.globe.pitch += (state.globe.targetPitch - state.globe.pitch) * 0.08;
      }
      
      state.globe.pulsePhase += 0.04;
      render3DLunarGlobe();
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}

function render3DLunarGlobe() {
  const canvas = elements.canvas3D;
  const ctx = canvas.getContext('2d');
  const rect = elements.canvasContainer.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  
  if (width === 0 || height === 0) return;
  const isDark = state.theme === 'dark';
  
  const cx = width / 2;
  const cy = height / 2;
  const R = Math.min(width, height) * 0.38 * state.globe.zoom;
  
  // 1. Draw Deep Space Background with Starfield in Dark Mode
  ctx.fillStyle = isDark ? '#04060a' : '#e6eaf2';
  ctx.fillRect(0, 0, width, height);
  
  if (isDark) {
    drawSpaceStarfield(ctx, width, height);
  }
  
  // 2. Draw Outer Limb Glow (Atmospheric/Celestial Horizon Halo)
  drawLimbGlow(ctx, cx, cy, R, isDark);
  
  // 3. Draw 3D Shaded Lunar Sphere Body
  drawLunarSphereBody(ctx, cx, cy, R, isDark);
  
  // 4. Draw 3D Basaltic Lunar Maria (Dark volcanic plains)
  draw3DLunarMaria(ctx, cx, cy, R, isDark);
  
  // 5. Draw 3D Latitude & Longitude Coordinate Wireframe Grid
  draw3DCoordinateGrid(ctx, cx, cy, R, isDark);
  
  // 6. Draw 3D Observation Footprints Draped on Lunar Sphere
  draw3DFootprints(ctx, cx, cy, R, isDark);
  
  // 7. Draw 3D Landmark Craters & Beacon Stalks
  draw3DLandmarkCraters(ctx, cx, cy, R, isDark);
}

function drawSpaceStarfield(ctx, width, height) {
  ctx.save();
  ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
  // Subtle static stars
  const starSeeds = [
    [0.12, 0.18], [0.25, 0.82], [0.38, 0.15], [0.85, 0.22],
    [0.91, 0.76], [0.08, 0.65], [0.72, 0.88], [0.61, 0.12],
    [0.44, 0.92], [0.18, 0.42], [0.82, 0.54], [0.55, 0.08],
  ];
  starSeeds.forEach(([sx, sy]) => {
    ctx.fillRect(sx * width, sy * height, 1.2, 1.2);
  });
  ctx.restore();
}

function drawLimbGlow(ctx, cx, cy, R, isDark) {
  ctx.save();
  const glowR = R * 1.08;
  const gradient = ctx.createRadialGradient(cx, cy, R * 0.92, cx, cy, glowR);
  
  if (isDark) {
    gradient.addColorStop(0, 'rgba(0, 240, 255, 0.15)');
    gradient.addColorStop(0.5, 'rgba(56, 189, 248, 0.08)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
  } else {
    gradient.addColorStop(0, 'rgba(2, 132, 199, 0.12)');
    gradient.addColorStop(0.6, 'rgba(14, 165, 233, 0.05)');
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
  }
  
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(cx, cy, glowR, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawLunarSphereBody(ctx, cx, cy, R, isDark) {
  ctx.save();
  
  // Calculate Sun Vector from Active Observation Geometry
  let sunAz = 45.0;
  if (state.selectedObservation?.geometry?.solar_azimuth_deg != null) {
    sunAz = state.selectedObservation.geometry.solar_azimuth_deg;
  }
  const sunRad = sunAz * (Math.PI / 180.0);
  const lightOffsetX = Math.cos(sunRad) * R * 0.38;
  const lightOffsetY = -Math.sin(sunRad) * R * 0.38;
  
  // Spherical Shading Gradient
  const sphereGrad = ctx.createRadialGradient(
    cx + lightOffsetX, cy + lightOffsetY, R * 0.1,
    cx, cy, R
  );
  
  if (isDark) {
    sphereGrad.addColorStop(0, '#c7d2de'); // Anorthositic bright highlands
    sphereGrad.addColorStop(0.35, '#828d9c');
    sphereGrad.addColorStop(0.7, '#3c4554');
    sphereGrad.addColorStop(0.95, '#181e28');
    sphereGrad.addColorStop(1.0, '#090d14'); // Shadow terminator limb
  } else {
    sphereGrad.addColorStop(0, '#ffffff');
    sphereGrad.addColorStop(0.35, '#e2e8f0');
    sphereGrad.addColorStop(0.7, '#94a3b8');
    sphereGrad.addColorStop(0.95, '#64748b');
    sphereGrad.addColorStop(1.0, '#334155');
  }
  
  ctx.fillStyle = sphereGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  
  // Perimeter Rim stroke
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = isDark ? 'rgba(0, 240, 255, 0.4)' : 'rgba(2, 132, 199, 0.4)';
  ctx.stroke();
  
  ctx.restore();
}

function draw3DLunarMaria(ctx, cx, cy, R, isDark) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, R - 1, 0, Math.PI * 2);
  ctx.clip(); // Clip within lunar sphere
  
  const mareColor = isDark ? 'rgba(20, 26, 36, 0.45)' : 'rgba(71, 85, 105, 0.35)';
  ctx.fillStyle = mareColor;
  
  LUNAR_MARIA.forEach(mare => {
    const center = project3D(mare.lon, mare.lat, R);
    if (!center.isVisible) return;
    
    const screenX = cx + center.x;
    const screenY = cy - center.y;
    const rScaledX = (mare.rLon / 90.0) * R * (center.z / R);
    const rScaledY = (mare.rLat / 90.0) * R * (center.z / R);
    
    ctx.beginPath();
    ctx.ellipse(screenX, screenY, Math.max(4, rScaledX), Math.max(4, rScaledY), 0, 0, Math.PI * 2);
    ctx.fill();
  });
  
  ctx.restore();
}

function draw3DCoordinateGrid(ctx, cx, cy, R, isDark) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, R - 0.5, 0, Math.PI * 2);
  ctx.clip(); // Clip grid strictly within front hemisphere
  
  ctx.lineWidth = 1;
  ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.09)';
  
  // 1. Longitude Meridians every 30°
  for (let lon = -180; lon < 180; lon += 30) {
    ctx.beginPath();
    let started = false;
    for (let lat = -90; lat <= 90; lat += 3) {
      const p = project3D(lon, lat, R);
      if (p.isVisible) {
        const sx = cx + p.x;
        const sy = cy - p.y;
        if (!started) { ctx.moveTo(sx, sy); started = true; }
        else { ctx.lineTo(sx, sy); }
      } else {
        started = false;
      }
    }
    ctx.stroke();
  }
  
  // 2. Latitude Parallels every 30°
  for (let lat = -60; lat <= 60; lat += 30) {
    ctx.beginPath();
    let started = false;
    for (let lon = -180; lon <= 180; lon += 4) {
      const p = project3D(lon, lat, R);
      if (p.isVisible) {
        const sx = cx + p.x;
        const sy = cy - p.y;
        if (!started) { ctx.moveTo(sx, sy); started = true; }
        else { ctx.lineTo(sx, sy); }
      } else {
        started = false;
      }
    }
    
    if (lat === 0) {
      // Equator in bright accent
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = isDark ? 'rgba(0, 240, 255, 0.35)' : 'rgba(2, 132, 199, 0.35)';
      ctx.stroke();
      ctx.lineWidth = 1;
      ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.09)';
    } else {
      ctx.stroke();
    }
  }
  
  // 3. Highlight South Polar Circle (-70° / -80°)
  [-70, -80].forEach(polarLat => {
    ctx.beginPath();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = isDark ? 'rgba(245, 158, 11, 0.4)' : 'rgba(217, 119, 6, 0.4)';
    let started = false;
    for (let lon = -180; lon <= 180; lon += 4) {
      const p = project3D(lon, polarLat, R);
      if (p.isVisible) {
        const sx = cx + p.x;
        const sy = cy - p.y;
        if (!started) { ctx.moveTo(sx, sy); started = true; }
        else { ctx.lineTo(sx, sy); }
      } else {
        started = false;
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);
  });
  
  ctx.restore();
}

function draw3DFootprints(ctx, cx, cy, R, isDark) {
  const obsList = state.filteredObservations.length > 0 ? state.filteredObservations : state.observations;
  
  obsList.forEach(obs => {
    const isSelected = state.selectedObservation && state.selectedObservation.product_id === obs.product_id;
    if (!isSelected) {
      renderSingle3DFootprint(ctx, obs, cx, cy, R, false, isDark);
    }
  });
  
  if (state.selectedObservation) {
    renderSingle3DFootprint(ctx, state.selectedObservation, cx, cy, R, true, isDark);
  }
}

function renderSingle3DFootprint(ctx, obs, cx, cy, R, isSelected, isDark) {
  const bb = obs.bbox;
  if (!bb) return;
  
  // Calculate 4 corners in 3D
  const corners = [
    project3D(bb.min_lon, bb.max_lat, R),
    project3D(bb.max_lon, bb.max_lat, R),
    project3D(bb.max_lon, bb.min_lat, R),
    project3D(bb.min_lon, bb.min_lat, R),
  ];
  
  // Visible if at least one corner is on the front hemisphere
  const anyVisible = corners.some(c => c.isVisible);
  if (!anyVisible) return;
  
  const centerLon = (bb.min_lon + bb.max_lon) / 2.0;
  const centerLat = (bb.min_lat + bb.max_lat) / 2.0;
  const center = project3D(centerLon, centerLat, R);
  if (!center.isVisible) return;
  
  let strokeColor = '#00f0ff';
  let fillColor = 'rgba(0, 240, 255, 0.2)';
  if (obs.sensor === 'LRO_NAC') {
    strokeColor = '#f43f5e';
    fillColor = 'rgba(244, 63, 94, 0.2)';
  } else if (obs.sensor === 'TMC2') {
    strokeColor = '#10b981';
    fillColor = 'rgba(16, 185, 129, 0.2)';
  }
  
  ctx.save();
  
  // Draw curved spherical footprint polygon
  ctx.beginPath();
  corners.forEach((c, idx) => {
    const sx = cx + c.x;
    const sy = cy - c.y;
    if (idx === 0) ctx.moveTo(sx, sy);
    else ctx.lineTo(sx, sy);
  });
  ctx.closePath();
  
  if (isSelected) {
    ctx.lineWidth = 3;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = fillColor.replace('0.2', '0.45');
    ctx.shadowColor = strokeColor;
    ctx.shadowBlur = 14;
  } else {
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = fillColor;
  }
  
  ctx.fill();
  ctx.stroke();
  
  // 3D Center Pin with Pulsing Wave
  const csx = cx + center.x;
  const csy = cy - center.y;
  const pulseR = 6 + (Math.sin(state.globe.pulsePhase) + 1) * 4;
  
  ctx.beginPath();
  ctx.arc(csx, csy, pulseR, 0, Math.PI * 2);
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 1;
  ctx.stroke();
  
  ctx.beginPath();
  ctx.arc(csx, csy, 3, 0, Math.PI * 2);
  ctx.fillStyle = strokeColor;
  ctx.fill();
  
  // If selected, project a holographic vertical telemetry beacon stalk outwards
  if (isSelected) {
    const normalMultiplier = 1.18;
    const topX = cx + center.x * normalMultiplier;
    const topY = cy - center.y * normalMultiplier;
    
    ctx.beginPath();
    ctx.setLineDash([2, 2]);
    ctx.moveTo(csx, csy);
    ctx.lineTo(topX, topY);
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.setLineDash([]);
    
    // HUD Flag Label in 3D
    ctx.fillStyle = isDark ? 'rgba(14, 18, 27, 0.9)' : 'rgba(255, 255, 255, 0.9)';
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(topX + 6, topY - 14, 120, 24, 4);
    ctx.fill();
    ctx.stroke();
    
    ctx.fillStyle = strokeColor;
    ctx.font = '700 9px "JetBrains Mono", monospace';
    ctx.fillText(`${obs.sensor} // ${obs.spatial_resolution_m}m`, topX + 12, topY + 2);
  }
  
  ctx.restore();
}

function draw3DLandmarkCraters(ctx, cx, cy, R, isDark) {
  ctx.save();
  
  LUNAR_LANDMARKS.forEach(crater => {
    const p = project3D(crater.lon, crater.lat, R);
    if (!p.isVisible) return;
    
    const sx = cx + p.x;
    const sy = cy - p.y;
    
    // Crater circular rim in 3D perspective
    const perspectiveScale = Math.max(0.2, p.z / R);
    const rimRadius = Math.max(4, (crater.radius / 18.0) * state.globe.zoom * perspectiveScale);
    
    ctx.beginPath();
    ctx.arc(sx, sy, rimRadius, 0, Math.PI * 2);
    ctx.strokeStyle = crater.primary ? (isDark ? '#00f0ff' : '#0284c7') : (isDark ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.3)');
    ctx.lineWidth = crater.primary ? 2 : 1;
    ctx.stroke();
    
    // Center dot
    ctx.beginPath();
    ctx.arc(sx, sy, crater.primary ? 3 : 2, 0, Math.PI * 2);
    ctx.fillStyle = crater.primary ? (isDark ? '#00f0ff' : '#0284c7') : (isDark ? '#94a3b8' : '#64748b');
    ctx.fill();
    
    // Label
    ctx.fillStyle = crater.primary ? (isDark ? '#38bdf8' : '#0284c7') : (isDark ? '#94a3b8' : '#64748b');
    ctx.font = `${crater.primary ? '700' : '500'} 9px "JetBrains Mono", monospace`;
    ctx.fillText(`⌖ ${crater.name}`, sx + rimRadius + 4, sy + 3);
  });
  
  ctx.restore();
}

function check3DFootprintHover(mouseX, mouseY, width, height, clientX, clientY) {
  const cx = width / 2;
  const cy = height / 2;
  const R = Math.min(width, height) * 0.38 * state.globe.zoom;
  
  let matched = null;
  const obsList = state.filteredObservations.length > 0 ? state.filteredObservations : state.observations;
  
  for (let i = obsList.length - 1; i >= 0; i--) {
    const obs = obsList[i];
    const bb = obs.bbox;
    if (!bb) continue;
    
    const centerLon = (bb.min_lon + bb.max_lon) / 2.0;
    const centerLat = (bb.min_lat + bb.max_lat) / 2.0;
    const p = project3D(centerLon, centerLat, R);
    if (!p.isVisible) continue;
    
    const sx = cx + p.x;
    const sy = cy - p.y;
    const dist = Math.sqrt((mouseX - sx) ** 2 + (mouseY - sy) ** 2);
    
    if (dist <= 22) {
      matched = obs;
      break;
    }
  }
  
  state.globe.hoveredObs = matched;
  
  if (matched) {
    elements.canvas3D.style.cursor = 'pointer';
    elements.mapTooltip.style.display = 'block';
    elements.mapTooltip.style.left = `${clientX}px`;
    elements.mapTooltip.style.top = `${clientY}px`;
    elements.mapTooltip.innerHTML = `
      <strong>3D // ${matched.sensor}</strong> (${matched.spatial_resolution_m}m)<br>
      <span style="opacity:0.8">${matched.product_id}</span>
    `;
  } else {
    elements.canvas3D.style.cursor = state.globe.isDragging ? 'grabbing' : 'grab';
    elements.mapTooltip.style.display = 'none';
  }
}

/* ==========================================================================
   7. Controls & Event Listeners
   ========================================================================== */

elements.inputSearch.addEventListener('input', (e) => {
  state.searchQuery = e.target.value.trim();
  elements.btnClearSearch.style.display = state.searchQuery ? 'block' : 'none';
  applyFilters();
});

elements.btnClearSearch.addEventListener('click', () => {
  elements.inputSearch.value = '';
  state.searchQuery = '';
  elements.btnClearSearch.style.display = 'none';
  applyFilters();
});

elements.sensorChipsContainer.addEventListener('click', (e) => {
  const chip = e.target.closest('.chip');
  if (!chip) return;
  
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  chip.classList.add('active');
  state.activeSensor = chip.dataset.sensor;
  applyFilters();
});

elements.btnResetFilters.addEventListener('click', () => {
  state.activeSensor = 'ALL';
  state.searchQuery = '';
  state.maxResolution = 10.0;
  elements.inputSearch.value = '';
  elements.sliderRes.value = 10.0;
  elements.labelResFilter.textContent = '≤ 10.0m';
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('active', c.dataset.sensor === 'ALL'));
  applyFilters();
});

elements.sliderRes.addEventListener('input', (e) => {
  state.maxResolution = parseFloat(e.target.value);
  elements.labelResFilter.textContent = `≤ ${state.maxResolution}m`;
  applyFilters();
});

elements.selectSort.addEventListener('change', (e) => {
  state.sortBy = e.target.value;
  applyFilters();
});

// South Pole Camera Jump
elements.btnFocusSouthPole.addEventListener('click', () => {
  // 2D Map
  state.map.centerLon = 26.0;
  state.map.centerLat = -73.5;
  state.map.zoom = 12.0;
  if (state.viewMode === '2D') render2DLunarMap();
  
  // 3D Globe
  state.globe.targetYaw = -26.0 * (Math.PI / 180.0);
  state.globe.targetPitch = -73.5 * (Math.PI / 180.0);
  state.globe.zoom = 1.35;
});

// Zoom Controls
elements.btnZoomIn.addEventListener('click', () => {
  if (state.viewMode === '2D') {
    state.map.zoom = Math.min(60.0, state.map.zoom * 1.5);
    render2DLunarMap();
  } else {
    state.globe.zoom = Math.min(4.5, state.globe.zoom * 1.25);
  }
});

elements.btnZoomOut.addEventListener('click', () => {
  if (state.viewMode === '2D') {
    state.map.zoom = Math.max(1.0, state.map.zoom / 1.5);
    render2DLunarMap();
  } else {
    state.globe.zoom = Math.max(0.6, state.globe.zoom / 1.25);
  }
});

elements.btnResetMap.addEventListener('click', () => {
  if (state.viewMode === '2D') {
    state.map.centerLon = 26.0;
    state.map.centerLat = -73.5;
    state.map.zoom = 8.0;
    render2DLunarMap();
  } else {
    state.globe.targetYaw = -0.45;
    state.globe.targetPitch = -0.72;
    state.globe.zoom = 1.05;
  }
});

elements.btnCloseInspector.addEventListener('click', () => {
  elements.inspectorPanel.classList.add('collapsed');
});

// Pair Overlap Modal
elements.btnTogglePairMode.addEventListener('click', () => {
  renderPairModal();
  elements.modalPairBackdrop.style.display = 'flex';
});

elements.btnFindPairsForThis.addEventListener('click', () => {
  renderPairModal();
  elements.modalPairBackdrop.style.display = 'flex';
});

elements.btnClosePairModal.addEventListener('click', () => {
  elements.modalPairBackdrop.style.display = 'none';
});

elements.modalPairBackdrop.addEventListener('click', (e) => {
  if (e.target === elements.modalPairBackdrop) {
    elements.modalPairBackdrop.style.display = 'none';
  }
});

function renderPairModal() {
  if (state.overlappingPairs.length === 0) {
    elements.modalPairsContainer.innerHTML = `<div class="loading-state">No overlapping co-observation pairs discovered yet.</div>`;
    return;
  }
  
  elements.modalPairsContainer.innerHTML = '';
  
  state.overlappingPairs.forEach(pair => {
    const card = document.createElement('div');
    card.className = 'pair-card';
    
    const srcPreview = `/api/v1/observations/${encodeURIComponent(pair.source_product_id)}/preview`;
    const refPreview = `/api/v1/observations/${encodeURIComponent(pair.reference_product_id)}/preview`;
    
    card.innerHTML = `
      <div class="pair-card-header">
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <span class="obs-sensor-badge badge-ohrc">${pair.source_sensor}</span>
          <span style="font-family:var(--font-mono); font-size:0.75rem;">⟷</span>
          <span class="obs-sensor-badge badge-lronac">${pair.reference_sensor}</span>
        </div>
        <div class="suitability-badge">
          Layer 3 Suitability: ${pair.registration_suitability_score}/100
        </div>
      </div>
      
      <div class="pair-comparison-row">
        <div class="pair-item-card">
          <div style="font-family:var(--font-mono); font-size:0.6875rem; font-weight:600; color:var(--color-ohrc);">
            SOURCE: Chandrayaan-2 (${pair.source_resolution_m}m)
          </div>
          <img class="pair-img-preview" src="${srcPreview}" alt="Source observation" onerror="this.src='';">
          <div style="font-family:var(--font-mono); font-size:0.625rem; word-break:break-all;">${pair.source_product_id}</div>
        </div>
        
        <div class="pair-center-indicator">
          <span style="font-size:0.625rem; color:var(--text-muted);">OVERLAP</span>
          <div class="overlap-percent-dial">${pair.overlap_percent_of_source}%</div>
          <span style="font-size:0.5625rem; color:var(--text-muted); text-align:center;">Solar Δ: ${pair.solar_incidence_diff_deg}°</span>
        </div>
        
        <div class="pair-item-card">
          <div style="font-family:var(--font-mono); font-size:0.6875rem; font-weight:600; color:var(--color-lronac);">
            REFERENCE: NASA LRO NAC (${pair.reference_resolution_m}m)
          </div>
          <img class="pair-img-preview" src="${refPreview}" alt="Reference observation" onerror="this.src='';">
          <div style="font-family:var(--font-mono); font-size:0.625rem; word-break:break-all;">${pair.reference_product_id}</div>
        </div>
      </div>
      
      <div class="pair-meta-footer">
        <span>Intersection BBox: Lat [${pair.intersection_bbox.min_lat}° to ${pair.intersection_bbox.max_lat}°], Lon [${pair.intersection_bbox.min_lon}° to ${pair.intersection_bbox.max_lon}°]</span>
        <button class="btn btn-primary btn-inspect-pair-btn" data-src="${pair.source_product_id}">
          Focus on Map
        </button>
      </div>
    `;
    
    card.querySelector('.btn-inspect-pair-btn').addEventListener('click', () => {
      elements.modalPairBackdrop.style.display = 'none';
      const srcObs = state.observations.find(o => o.product_id === pair.source_product_id);
      if (srcObs) {
        selectObservation(srcObs, true);
      }
    });
    
    elements.modalPairsContainer.appendChild(card);
  });
}

// Start Application on Load
document.addEventListener('DOMContentLoaded', initData);
