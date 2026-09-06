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
  setupPreviewControls();
  
  // Set initial view mode to 3D Lunar Globe
  setViewMode('3D');
  
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

    // Populate POC3 registration dropdowns with all observations
    populateRegistrationDropdowns(true);
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
    const img = elements.inspectPreviewImg;
    // For high aspect-ratio orbital strips (e.g. LRO NAC 1024x149), automatically fit width so craters are clear
    if (img.naturalHeight && img.naturalWidth && (img.naturalHeight / img.naturalWidth > 1.8)) {
      fitWidthPreview();
    } else {
      resetPreviewTransform();
    }
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

const previewState = {
  zoom: 1.0,
  panX: 0,
  panY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
};

function updatePreviewTransform() {
  const img = elements.inspectPreviewImg;
  if (!img) return;
  img.style.transform = `translate(${previewState.panX}px, ${previewState.panY}px) scale(${previewState.zoom})`;
  const hint = document.getElementById('viewport-zoom-hint');
  if (hint) {
    hint.textContent = `${Math.round(previewState.zoom * 100)}% • Drag to Pan`;
  }
}

function resetPreviewTransform() {
  previewState.zoom = 1.0;
  previewState.panX = 0;
  previewState.panY = 0;
  updatePreviewTransform();
}

function fitWidthPreview() {
  const vp = document.getElementById('image-viewport');
  const img = elements.inspectPreviewImg;
  if (!vp || !img || !img.naturalWidth) return;
  const vpRect = vp.getBoundingClientRect();
  const currentRenderedW = img.naturalWidth * (vpRect.height / img.naturalHeight);
  const targetZoom = Math.max(1.8, Math.min(7.0, vpRect.width / Math.max(currentRenderedW, 20)));
  previewState.zoom = targetZoom;
  previewState.panX = 0;
  previewState.panY = 0;
  updatePreviewTransform();
}

function setupPreviewControls() {
  const vp = document.getElementById('image-viewport');
  if (!vp) return;

  document.getElementById('btn-pv-zoom-in')?.addEventListener('click', () => {
    previewState.zoom = Math.min(8.0, previewState.zoom * 1.3);
    updatePreviewTransform();
  });

  document.getElementById('btn-pv-zoom-out')?.addEventListener('click', () => {
    previewState.zoom = Math.max(0.5, previewState.zoom * 0.75);
    updatePreviewTransform();
  });

  document.getElementById('btn-pv-fit-w')?.addEventListener('click', () => {
    fitWidthPreview();
  });

  document.getElementById('btn-pv-reset')?.addEventListener('click', () => {
    resetPreviewTransform();
  });

  // Wheel zoom
  vp.addEventListener('wheel', (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.85;
    previewState.zoom = Math.max(0.4, Math.min(10.0, previewState.zoom * factor));
    updatePreviewTransform();
  }, { passive: false });

  // Mouse Drag to Pan
  vp.addEventListener('mousedown', (e) => {
    previewState.isDragging = true;
    previewState.dragStartX = e.clientX - previewState.panX;
    previewState.dragStartY = e.clientY - previewState.panY;
  });

  window.addEventListener('mousemove', (e) => {
    if (!previewState.isDragging) return;
    previewState.panX = e.clientX - previewState.dragStartX;
    previewState.panY = e.clientY - previewState.dragStartY;
    updatePreviewTransform();
  });

  window.addEventListener('mouseup', () => {
    previewState.isDragging = false;
  });
}

/* ==========================================================================
   4. View Mode Switching (2D Map vs 3D Lunar Globe)
   ========================================================================== */

function setViewMode(mode) {
  state.viewMode = mode;
  const rect = elements.canvasContainer.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const w = rect.width || 800;
  const h = rect.height || 600;
  
  if (mode === '2D') {
    elements.btnMode2D.classList.add('active');
    elements.btnMode3D.classList.remove('active');
    elements.canvas2D.style.display = 'block';
    elements.canvas3D.style.display = 'none';
    elements.btnToggleOrbit.style.display = 'none';
    elements.canvas2D.width = w * dpr;
    elements.canvas2D.height = h * dpr;
    const ctx = elements.canvas2D.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    render2DLunarMap();
  } else {
    elements.btnMode3D.classList.add('active');
    elements.btnMode2D.classList.remove('active');
    elements.canvas2D.style.display = 'none';
    elements.canvas3D.style.display = 'block';
    elements.btnToggleOrbit.style.display = 'inline-flex';
    updateOrbitButtonText();
    elements.canvas3D.width = w * dpr;
    elements.canvas3D.height = h * dpr;
    const ctx = elements.canvas3D.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
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

const footprintImageCache = {};

function getFootprintImage(obs) {
  if (!obs || !obs.product_id) return null;
  if (footprintImageCache[obs.product_id]) {
    return footprintImageCache[obs.product_id];
  }
  const img = new Image();
  img.src = `/api/v1/observations/${encodeURIComponent(obs.product_id)}/preview`;
  img.onload = () => {
    if (state.viewMode === '2D') render2DLunarMap();
  };
  footprintImageCache[obs.product_id] = img;
  return img;
}

function draw2DLunarBasemap(ctx, width, height, isDark) {
  ctx.save();
  
  // 1. Lunar Surface Regolith Base (Textured Gray Tone)
  ctx.fillStyle = isDark ? '#080c14' : '#dbeafe';
  ctx.fillRect(0, 0, width, height);

  // 2. Volcanic Basaltic Maria (Dark plains)
  LUNAR_MARIA.forEach(mare => {
    const pCenter = lonLatToScreen(mare.lon, mare.lat, width, height);
    const pEdgeX = lonLatToScreen(mare.lon + mare.rLon, mare.lat, width, height);
    const pEdgeY = lonLatToScreen(mare.lon, mare.lat + mare.rLat, width, height);
    const rx = Math.abs(pEdgeX.x - pCenter.x);
    const ry = Math.abs(pEdgeY.y - pCenter.y);

    if (pCenter.x + rx < 0 || pCenter.x - rx > width || pCenter.y + ry < 0 || pCenter.y - ry > height) return;

    ctx.save();
    ctx.beginPath();
    ctx.ellipse(pCenter.x, pCenter.y, Math.max(8, rx), Math.max(8, ry), 0, 0, Math.PI * 2);
    ctx.fillStyle = isDark ? 'rgba(18, 25, 38, 0.75)' : 'rgba(148, 163, 184, 0.4)';
    ctx.fill();

    if (state.map.zoom >= 1.2) {
      ctx.strokeStyle = isDark ? 'rgba(56, 189, 248, 0.12)' : 'rgba(2, 132, 199, 0.15)';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.7)';
      ctx.font = 'italic 10px "Inter", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(mare.name, pCenter.x, pCenter.y);
    }
    ctx.restore();
  });

  // 3. Shaded Crater Landforms with Depth Shading
  LUNAR_LANDMARKS.forEach(crater => {
    const pos = lonLatToScreen(crater.lon, crater.lat, width, height);
    const radPx = Math.max(6, (crater.radius / 10.0) * (state.map.zoom / 3.0));
    if (pos.x + radPx < 0 || pos.x - radPx > width || pos.y + radPx < 0 || pos.y - radPx > height) return;

    ctx.save();
    const craterGrad = ctx.createRadialGradient(
      pos.x - radPx * 0.25, pos.y - radPx * 0.25, radPx * 0.1,
      pos.x, pos.y, radPx
    );
    if (isDark) {
      craterGrad.addColorStop(0, 'rgba(4, 6, 10, 0.9)');
      craterGrad.addColorStop(0.7, 'rgba(15, 23, 42, 0.65)');
      craterGrad.addColorStop(1.0, 'rgba(56, 189, 248, 0.22)');
    } else {
      craterGrad.addColorStop(0, 'rgba(100, 116, 139, 0.5)');
      craterGrad.addColorStop(0.7, 'rgba(148, 163, 184, 0.3)');
      craterGrad.addColorStop(1.0, 'rgba(2, 132, 199, 0.2)');
    }
    ctx.fillStyle = craterGrad;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radPx, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  });

  ctx.restore();
}

function render2DLunarMap() {
  const canvas = elements.canvas2D;
  const ctx = canvas.getContext('2d');
  const rect = elements.canvasContainer.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  
  if (width === 0 || height === 0) return;
  const isDark = state.theme === 'dark';
  
  draw2DLunarBasemap(ctx, width, height, isDark);
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

  // Render optical surface imagery inside footprint bounds
  const img = getFootprintImage(obs);
  if (img && img.complete && img.naturalWidth > 0) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(tl.x, tl.y, w, h);
    ctx.clip();
    ctx.globalAlpha = isSelected ? 0.95 : 0.72;
    ctx.drawImage(img, tl.x, tl.y, w, h);
    ctx.restore();
  }

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

  // Draw crater terrain relief and ejecta ray system on sphere body
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, R - 1, 0, Math.PI * 2);
  ctx.clip();
  
  const craterList = [
    { lon: -11.2, lat: -43.3, r: 85, rays: true },  // Tycho
    { lon: -20.1, lat: 9.6, r: 93, rays: true },   // Copernicus
    { lon: -14.4, lat: -58.4, r: 120 },            // Clavius
    { lon: 26.2, lat: -72.9, r: 95 },              // Boguslawsky
    { lon: 0.0, lat: -89.9, r: 40 },               // Shackleton
    { lon: 26.8, lat: -67.7, r: 98 },              // Manzinus
    { lon: -38.0, lat: 8.0, r: 40 },               // Kepler
    { lon: -47.0, lat: 23.0, r: 40 },              // Aristarchus
    { lon: 26.0, lat: -11.0, r: 100 },             // Theophilus
    { lon: -2.0, lat: -9.0, r: 150 },              // Ptolemaeus
    { lon: 61.0, lat: -9.0, r: 130 },              // Langrenus
  ];

  craterList.forEach(c => {
    const p = project3D(c.lon, c.lat, R);
    if (!p.isVisible) return;
    const px = cx + p.x;
    const py = cy - p.y;
    const zScale = p.z / R;
    const craterR = Math.max(3, (c.r / 15.0) * (R / 200.0) * zScale);

    if (c.rays) {
      ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.18)' : 'rgba(255, 255, 255, 0.4)';
      ctx.lineWidth = 1;
      for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 4) {
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(px + Math.cos(angle) * craterR * 4.5, py + Math.sin(angle) * craterR * 4.5);
        ctx.stroke();
      }
    }

    ctx.beginPath();
    ctx.ellipse(px, py, craterR, craterR * Math.max(0.3, zScale), 0, 0, Math.PI * 2);
    ctx.fillStyle = isDark ? 'rgba(10, 14, 22, 0.55)' : 'rgba(51, 65, 85, 0.35)';
    ctx.fill();

    ctx.beginPath();
    ctx.ellipse(px + lightOffsetX * 0.02, py + lightOffsetY * 0.02, craterR, craterR * Math.max(0.3, zScale), 0, 0, Math.PI * 2);
    ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.6)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
  });
  ctx.restore();
  
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
        <div style="display:flex; gap:0.5rem;">
          <button class="btn btn-outline btn-poc3-pair-btn" data-src="${pair.source_product_id}" data-ref="${pair.reference_product_id}">
            Register in POC 3 ➔
          </button>
          <button class="btn btn-primary btn-inspect-pair-btn" data-src="${pair.source_product_id}">
            Focus on Map
          </button>
        </div>
      </div>
    `;
    
    card.querySelector('.btn-inspect-pair-btn').addEventListener('click', () => {
      elements.modalPairBackdrop.style.display = 'none';
      const srcObs = state.observations.find(o => o.product_id === pair.source_product_id);
      if (srcObs) {
        selectObservation(srcObs, true);
      }
    });

    card.querySelector('.btn-poc3-pair-btn').addEventListener('click', () => {
      elements.modalPairBackdrop.style.display = 'none';
      switchModule('poc3');
      poc3SetSelectedPair(pair.source_product_id, pair.reference_product_id);
    });
    
    elements.modalPairsContainer.appendChild(card);
  });
}

/* ==========================================================================
   POC 3: Classical Registration Engine Client Controller
   Deterministic Scientific Registration & Multi-Viewport Suite
   ========================================================================== */

const ALGORITHM_DOCS = {
  SIFT: {
    name: "SIFT (Scale-Invariant Feature Transform)",
    desc: "Computes Difference-of-Gaussians (DoG) scale-space extrema with 128D gradient histograms. Invariant to uniform scale, rotation, and illumination shifts across crater slopes."
  },
  RootSIFT: {
    name: "RootSIFT (L1-Square-Root Hellinger Kernel)",
    desc: "Applies L1 normalization followed by square-rooting SIFT descriptors. Eliminates Euclidean distance distortion for extreme solar incidence angle variations."
  },
  ORB: {
    name: "ORB (Oriented FAST & Rotated BRIEF)",
    desc: "Ultra-fast 256-bit binary descriptors with intensity centroid orientation. Optimized for high-throughput spaceborne embedded registration at low computational overhead."
  },
  AKAZE: {
    name: "AKAZE (Accelerated Fast Explicit Diffusion)",
    desc: "Extracts keypoints in nonlinear scale spaces using Fast Explicit Diffusion (FED). Preserves lunar crater rim sharp boundaries without Gaussian blur artifacts."
  },
  PhaseCorrelation: {
    name: "Phase Correlation (2D FFT Translation)",
    desc: "Fourier-domain phase shift estimator with Hanning windowing. Computes sub-pixel translation (dx, dy) invariant to monotonic intensity drifts."
  }
};

const poc3State = {
  currentModule: 'layer1', // 'layer1' or 'poc3'
  selectedSourceId: null,
  selectedRefId: null,
  selectedMethod: 'SIFT',
  selectedTransform: 'Homography',
  ratioThresh: 0.75,
  ransacThresh: 3.0,
  activeViewTab: 'matches', // 'matches', 'checkerboard', 'warped', 'sidebyside', 'swipe'
  isExecuting: false,
  currentJob: null,
  
  // Interactive Viewport Pan & Zoom
  zoom: 1.0,
  panX: 0,
  panY: 0,
  isDraggingCanvas: false,
  dragStartX: 0,
  dragStartY: 0,

  // Swipe Comparator
  swipePercent: 50,
  isSwiping: false,
};

// Mode Switcher between Layer 1 Explorer and POC 3 Registration Engine
function switchModule(moduleName) {
  poc3State.currentModule = moduleName;

  const btnLayer1 = document.getElementById('btn-nav-layer1');
  const btnPoc3 = document.getElementById('btn-nav-poc3');
  const wsLayer1 = document.getElementById('layer1-workspace');
  const wsPoc3 = document.getElementById('poc3-workspace');
  const modTag = document.getElementById('app-module-tag');
  const modTitle = document.getElementById('app-module-title');

  if (moduleName === 'poc3') {
    btnLayer1?.classList.remove('active');
    btnPoc3?.classList.add('active');
    if (wsLayer1) wsLayer1.style.display = 'none';
    if (wsPoc3) wsPoc3.style.display = 'grid';
    if (modTag) modTag.textContent = 'POC 3 MICROSERVICE';
    if (modTitle) modTitle.textContent = 'NEXUS-LUNAR // CLASSICAL REGISTRATION';
    populateRegistrationDropdowns();
  } else {
    btnLayer1?.classList.add('active');
    btnPoc3?.classList.remove('active');
    if (wsLayer1) wsLayer1.style.display = 'grid';
    if (wsPoc3) wsPoc3.style.display = 'none';
    if (modTag) modTag.textContent = 'LAYER 1 MICROSERVICE';
    if (modTitle) modTitle.textContent = 'NEXUS-LUNAR // DATA EXPLORER';

    // Trigger canvas resize for 2D/3D map
    setTimeout(() => {
      resizeMapCanvas();
      renderMap();
      if (state.viewMode === '3D') renderGlobe();
    }, 50);
  }
}

// Populate Source and Reference Select Dropdowns with All Available Observations
function populateRegistrationDropdowns(force = false) {
  const selSrc = document.getElementById('reg-select-source');
  const selRef = document.getElementById('reg-select-reference');
  if (!selSrc || !selRef) return;

  if (!state.observations || state.observations.length === 0) return;

  // Don't skip if force is true or if dropdown has only 1 or 0 options
  if (!force && selSrc.options.length > 3 && selRef.options.length > 3) return;

  const currentSrc = selSrc.value || poc3State.selectedSourceId;
  const currentRef = selRef.value || poc3State.selectedRefId;

  selSrc.innerHTML = '';
  selRef.innerHTML = '';

  const isCh2 = (o) => {
    const m = String(o.mission || '').toUpperCase();
    const s = String(o.sensor || '').toUpperCase();
    return m.includes('CHANDRAYAAN') || s.startsWith('OHRC') || s.startsWith('TMC');
  };

  const ch2Obs = state.observations.filter(isCh2);
  const otherObs = state.observations.filter(o => !isCh2(o));

  // 1. Source Dropdown: Chandrayaan-2 (ISRO) Source Images first, followed by all other missions
  if (ch2Obs.length > 0) {
    const grpCh2 = document.createElement('optgroup');
    grpCh2.label = '── Chandrayaan-2 (ISRO) Source Images ──';
    ch2Obs.forEach(obs => {
      const opt = document.createElement('option');
      opt.value = obs.product_id;
      opt.textContent = `${obs.sensor} - ${obs.product_id} (${obs.spatial_resolution_m}m)`;
      grpCh2.appendChild(opt);
    });
    selSrc.appendChild(grpCh2);
  }

  if (otherObs.length > 0) {
    const grpOther = document.createElement('optgroup');
    grpOther.label = '── Other Lunar Observations (NASA LRO / SELENE) ──';
    otherObs.forEach(obs => {
      const opt = document.createElement('option');
      opt.value = obs.product_id;
      opt.textContent = `${obs.sensor} - ${obs.product_id} (${obs.spatial_resolution_m}m)`;
      grpOther.appendChild(opt);
    });
    selSrc.appendChild(grpOther);
  }

  // Fallback if no optgroups added
  if (selSrc.options.length === 0) {
    state.observations.forEach(obs => {
      const opt = document.createElement('option');
      opt.value = obs.product_id;
      opt.textContent = `${obs.sensor} - ${obs.product_id} (${obs.spatial_resolution_m}m)`;
      selSrc.appendChild(opt);
    });
  }

  // 2. Reference Dropdown: NASA LRO & SELENE first, followed by Chandrayaan-2 observations
  if (otherObs.length > 0) {
    const grpRef = document.createElement('optgroup');
    grpRef.label = '── NASA LRO & Reference Missions ──';
    otherObs.forEach(obs => {
      const opt = document.createElement('option');
      opt.value = obs.product_id;
      opt.textContent = `${obs.sensor} - ${obs.product_id} (${obs.spatial_resolution_m}m)`;
      grpRef.appendChild(opt);
    });
    selRef.appendChild(grpRef);
  }

  if (ch2Obs.length > 0) {
    const grpCh2Ref = document.createElement('optgroup');
    grpCh2Ref.label = '── Chandrayaan-2 Images ──';
    ch2Obs.forEach(obs => {
      const opt = document.createElement('option');
      opt.value = obs.product_id;
      opt.textContent = `${obs.sensor} - ${obs.product_id} (${obs.spatial_resolution_m}m)`;
      grpCh2Ref.appendChild(opt);
    });
    selRef.appendChild(grpCh2Ref);
  }

  if (selRef.options.length === 0) {
    state.observations.forEach(obs => {
      const opt = document.createElement('option');
      opt.value = obs.product_id;
      opt.textContent = `${obs.sensor} - ${obs.product_id} (${obs.spatial_resolution_m}m)`;
      selRef.appendChild(opt);
    });
  }

  // Restore selection or select default Boguslawsky pair
  if (currentSrc) {
    selSrc.value = currentSrc;
  }
  if (!selSrc.value && selSrc.options.length > 0) {
    poc3SetDefaultBoguslawskyPair();
  } else {
    poc3State.selectedSourceId = selSrc.value;
  }

  if (currentRef) {
    selRef.value = currentRef;
  }
  if (!selRef.value && selRef.options.length > 0) {
    poc3SetDefaultBoguslawskyPair();
  } else {
    poc3State.selectedRefId = selRef.value;
  }

  updateRegistrationPairDisplay();
}

function poc3SetDefaultBoguslawskyPair() {
  const selSrc = document.getElementById('reg-select-source');
  const selRef = document.getElementById('reg-select-reference');
  if (!selSrc || !selRef) return;

  const defaultSrc = "ch2_ohr_ncp_20230915t041230_boguslawsky_d18";
  const defaultRef = "M1345982701LR_BOGUSLAWSKY_REF";

  let foundSrc = false;
  let foundRef = false;

  for (let i = 0; i < selSrc.options.length; i++) {
    if (selSrc.options[i].value === defaultSrc) {
      selSrc.selectedIndex = i;
      foundSrc = true;
      break;
    }
  }

  for (let i = 0; i < selRef.options.length; i++) {
    if (selRef.options[i].value === defaultRef) {
      selRef.selectedIndex = i;
      foundRef = true;
      break;
    }
  }

  if (!foundSrc && selSrc.options.length > 0) selSrc.selectedIndex = 0;
  if (!foundRef && selRef.options.length > 0) selRef.selectedIndex = 0;

  poc3State.selectedSourceId = selSrc.value;
  poc3State.selectedRefId = selRef.value;

  updateRegistrationPairDisplay();
}

function updateRegistrationPairDisplay() {
  const srcId = poc3State.selectedSourceId;
  const refId = poc3State.selectedRefId;

  const srcObs = state.observations.find(o => o.product_id === srcId);
  const refObs = state.observations.find(o => o.product_id === refId);

  const dualSrcSub = document.getElementById('dual-src-sub');
  const dualRefSub = document.getElementById('dual-ref-sub');
  if (dualSrcSub && srcObs) {
    dualSrcSub.textContent = `${srcObs.sensor} - ${srcObs.product_id} (${srcObs.spatial_resolution_m}m)`;
  }
  if (dualRefSub && refObs) {
    dualRefSub.textContent = `${refObs.sensor} - ${refObs.product_id} (${refObs.spatial_resolution_m}m)`;
  }

  const swipeBottom = document.getElementById('swipe-img-bottom');
  const swipeTop = document.getElementById('swipe-img-top');
  if (swipeTop && srcObs) {
    swipeTop.src = `/api/v1/observations/${srcObs.product_id}/preview`;
  }
  if (swipeBottom && refObs) {
    swipeBottom.src = `/api/v1/observations/${refObs.product_id}/preview`;
  }
}

function poc3SetSelectedPair(srcId, refId) {
  populateRegistrationDropdowns(true);
  const selSrc = document.getElementById('reg-select-source');
  const selRef = document.getElementById('reg-select-reference');

  if (selSrc && srcId) {
    for (let i = 0; i < selSrc.options.length; i++) {
      if (selSrc.options[i].value === srcId) {
        selSrc.selectedIndex = i;
        break;
      }
    }
    poc3State.selectedSourceId = srcId;
  }

  if (selRef && refId) {
    for (let i = 0; i < selRef.options.length; i++) {
      if (selRef.options[i].value === refId) {
        selRef.selectedIndex = i;
        break;
      }
    }
    poc3State.selectedRefId = refId;
  }

  updateRegistrationPairDisplay();
}

// Execute Classical Registration Engine API Call
async function executeRegistration() {
  const selSrc = document.getElementById('reg-select-source');
  const selRef = document.getElementById('reg-select-reference');
  const srcId = selSrc ? selSrc.value : poc3State.selectedSourceId;
  const refId = selRef ? selRef.value : poc3State.selectedRefId;

  if (!srcId || !refId) {
    alert("Please select both a Source image and a Reference image.");
    return;
  }

  poc3State.isExecuting = true;
  const btnRun = document.getElementById('btn-execute-reg');
  const btnSpinner = document.getElementById('reg-spinner');
  const btnIcon = document.getElementById('reg-run-icon');
  const btnLabel = document.getElementById('reg-btn-label');
  const statusDot = document.querySelector('.reg-status-bar .status-dot');
  const statusText = document.getElementById('reg-status-text');
  const loadingOverlay = document.getElementById('reg-loading-overlay');
  const loadingStep = document.getElementById('reg-loading-step');

  if (btnRun) btnRun.disabled = true;
  if (btnSpinner) btnSpinner.style.display = 'inline-block';
  if (btnIcon) btnIcon.style.display = 'none';
  if (btnLabel) btnLabel.textContent = 'EXECUTING PIPELINE...';
  if (statusDot) {
    statusDot.className = 'status-dot working';
  }
  if (statusText) statusText.textContent = `Running ${poc3State.selectedMethod} registration...`;
  if (loadingOverlay) loadingOverlay.style.display = 'flex';
  if (loadingStep) loadingStep.textContent = `Extracting ${poc3State.selectedMethod} scale-space features & descriptors...`;

  const payload = {
    source_image: srcId,
    reference_image: refId,
    method: poc3State.selectedMethod,
    transform_type: poc3State.selectedTransform,
    ratio_thresh: poc3State.ratioThresh,
    ransac_thresh_px: poc3State.ransacThresh,
    max_features: 4000,
  };

  try {
    const response = await fetch('/api/v1/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || `HTTP ${response.status}`);
    }

    const data = await response.json();
    poc3State.currentJob = data;
    renderRegistrationResults(data);

    if (statusDot) statusDot.className = 'status-dot online';
    if (statusText) statusText.textContent = `Completed in ${data.metrics?.runtime_ms || '--'} ms`;
  } catch (error) {
    console.error("Registration failed:", error);
    alert(`Registration error: ${error.message}`);
    if (statusDot) statusDot.className = 'status-dot';
    if (statusText) statusText.textContent = `Error: ${error.message}`;
  } finally {
    poc3State.isExecuting = false;
    if (btnRun) btnRun.disabled = false;
    if (btnSpinner) btnSpinner.style.display = 'none';
    if (btnIcon) btnIcon.style.display = 'inline-block';
    if (btnLabel) btnLabel.textContent = 'RUN CLASSICAL REGISTRATION';
    if (loadingOverlay) loadingOverlay.style.display = 'none';
  }
}

// Render Registration Output Telemetry, Matrices, and Visualizers
function renderRegistrationResults(data) {
  const m = data.metrics || {};
  const artifacts = data.artifacts || {};

  // 1. Hide empty state
  const emptyState = document.getElementById('reg-empty-state');
  if (emptyState) emptyState.style.display = 'none';

  // 2. Scientific Telemetry HUD Readouts
  const jobBadge = document.getElementById('reg-job-id');
  if (jobBadge) jobBadge.textContent = `Job: ${data.job_id} (${data.method})`;

  const kpiMatch = document.getElementById('kpi-match-count');
  if (kpiMatch) kpiMatch.textContent = m.match_count != null ? m.match_count.toLocaleString() : '--';

  const kpiInlier = document.getElementById('kpi-inlier-count');
  if (kpiInlier) kpiInlier.textContent = m.inlier_count != null ? m.inlier_count.toLocaleString() : '--';

  const kpiRatio = document.getElementById('kpi-inlier-ratio');
  if (kpiRatio) kpiRatio.textContent = m.inlier_ratio_pct != null ? `${m.inlier_ratio_pct.toFixed(1)}%` : '--%';

  const kpiConf = document.getElementById('kpi-confidence');
  if (kpiConf) {
    const conf = m.confidence_level || 'LOW';
    kpiConf.textContent = conf;
    kpiConf.className = `confidence-badge ${conf}`;
  }

  const kpiRmse = document.getElementById('kpi-rmse');
  if (kpiRmse) {
    const rmse = m.reprojection_rmse_px != null ? m.reprojection_rmse_px.toFixed(3) : '--';
    kpiRmse.textContent = `${rmse} px`;
  }

  const kpiSubpixel = document.getElementById('kpi-subpixel-tag');
  if (kpiSubpixel && m.reprojection_rmse_px != null) {
    kpiSubpixel.textContent = m.reprojection_rmse_px < 1.0 ? '✓ Sub-pixel precision achieved' : 'Pixel-level convergence';
    kpiSubpixel.style.color = m.reprojection_rmse_px < 1.0 ? '#10b981' : 'var(--text-muted)';
  }

  const kpiRuntime = document.getElementById('kpi-runtime');
  if (kpiRuntime) kpiRuntime.textContent = m.runtime_ms != null ? `${m.runtime_ms.toFixed(1)} ms` : '-- ms';

  // 3. Estimated Geometry Readouts
  const geomRot = document.getElementById('geom-rotation');
  if (geomRot) {
    const rot = m.estimated_rotation_deg != null ? m.estimated_rotation_deg : 0.0;
    geomRot.textContent = `${rot > 0 ? '+' : ''}${rot.toFixed(3)}°`;
  }

  const geomScale = document.getElementById('geom-scale');
  if (geomScale && m.estimated_scale) {
    geomScale.textContent = `sx: ${m.estimated_scale.sx.toFixed(4)}, sy: ${m.estimated_scale.sy.toFixed(4)}`;
  }

  const geomTrans = document.getElementById('geom-translation');
  if (geomTrans && m.estimated_translation_px) {
    geomTrans.textContent = `Δx: ${m.estimated_translation_px.dx.toFixed(2)}px, Δy: ${m.estimated_translation_px.dy.toFixed(2)}px`;
  }

  // 4. Matrix Display Table
  const matrixContainer = document.getElementById('matrix-display');
  const matrixTypeTag = document.getElementById('matrix-type-tag');
  if (matrixTypeTag) matrixTypeTag.textContent = `${data.transform_type.toUpperCase()}`;

  if (matrixContainer && data.transformation_matrix) {
    const M = data.transformation_matrix;
    let tableHtml = '<table class="matrix-table">';
    for (let r = 0; r < M.length; r++) {
      tableHtml += '<tr>';
      for (let c = 0; c < M[r].length; c++) {
        const val = M[r][c];
        const formatted = Math.abs(val) < 0.0001 && val !== 0 ? val.toExponential(3) : val.toFixed(4);
        tableHtml += `<td>${formatted}</td>`;
      }
      tableHtml += '</tr>';
    }
    tableHtml += '</table>';
    matrixContainer.innerHTML = tableHtml;
  }

  // 5. Download / Export Buttons
  const btnExportWarped = document.getElementById('btn-export-warped');
  if (btnExportWarped && artifacts.warped_url) {
    btnExportWarped.href = artifacts.warped_url;
  }
  const btnExportMatches = document.getElementById('btn-export-matches');
  if (btnExportMatches && artifacts.matches_url) {
    btnExportMatches.href = artifacts.matches_url;
  }

  // 6. Update Active Stage View
  updateStageView();
}

// Switch Stage Viewport Tab (Matches, Checkerboard, Warped, Dual, Swipe)
function updateStageView() {
  const job = poc3State.currentJob;
  if (!job) return;

  const viewTab = poc3State.activeViewTab;
  const viewSingle = document.getElementById('reg-view-single');
  const viewDual = document.getElementById('reg-view-dual');
  const viewSwipe = document.getElementById('reg-view-swipe');
  const artImg = document.getElementById('reg-artifact-img');

  // Reset zoom & pan on tab change
  poc3ResetZoom();

  if (viewTab === 'matches' || viewTab === 'checkerboard' || viewTab === 'warped') {
    if (viewSingle) viewSingle.style.display = 'flex';
    if (viewDual) viewDual.style.display = 'none';
    if (viewSwipe) viewSwipe.style.display = 'none';

    let targetUrl = '';
    if (viewTab === 'matches') targetUrl = job.artifacts?.matches_url || job.artifacts?.warped_url;
    else if (viewTab === 'checkerboard') targetUrl = job.artifacts?.checkerboard_url;
    else if (viewTab === 'warped') targetUrl = job.artifacts?.warped_url;

    if (artImg && targetUrl) {
      // Add timestamp to prevent browser cache
      artImg.src = `${targetUrl}?t=${Date.now()}`;
    }
  } else if (viewTab === 'sidebyside') {
    if (viewSingle) viewSingle.style.display = 'none';
    if (viewDual) viewDual.style.display = 'grid';
    if (viewSwipe) viewSwipe.style.display = 'none';

    const dualSrcImg = document.getElementById('dual-src-img');
    const dualRefImg = document.getElementById('dual-ref-img');
    const dualSrcSub = document.getElementById('dual-src-sub');
    const dualRefSub = document.getElementById('dual-ref-sub');

    const srcObs = state.observations.find(o => o.product_id === (document.getElementById('reg-select-source')?.value || poc3State.selectedSourceId));
    const refObs = state.observations.find(o => o.product_id === (document.getElementById('reg-select-reference')?.value || poc3State.selectedRefId));

    if (dualSrcSub && srcObs) dualSrcSub.textContent = `${srcObs.product_id} (${srcObs.spatial_resolution_m}m)`;
    if (dualRefSub && refObs) dualRefSub.textContent = `${refObs.product_id} (${refObs.spatial_resolution_m}m)`;

    if (dualSrcImg && srcObs) {
      dualSrcImg.src = `/api/v1/observations/${srcObs.product_id}/preview`;
    }
    if (dualRefImg && refObs) {
      dualRefImg.src = `/api/v1/observations/${refObs.product_id}/preview`;
    }
  } else if (viewTab === 'swipe') {
    if (viewSingle) viewSingle.style.display = 'none';
    if (viewDual) viewDual.style.display = 'none';
    if (viewSwipe) viewSwipe.style.display = 'flex';

    const swipeBottom = document.getElementById('swipe-img-bottom');
    const swipeTop = document.getElementById('swipe-img-top');
    const srcObs = state.observations.find(o => o.product_id === (document.getElementById('reg-select-source')?.value || poc3State.selectedSourceId));

    if (swipeTop && srcObs) {
      swipeTop.src = `/api/v1/observations/${srcObs.product_id}/preview`;
    }
    if (swipeBottom && job.artifacts?.warped_url) {
      swipeBottom.src = `${job.artifacts.warped_url}?t=${Date.now()}`;
    }

    setSwipePosition(50);
  }
}

// Swipe Comparator Slider Positioning
function setSwipePosition(percent) {
  const clamped = Math.max(0, Math.min(100, percent));
  poc3State.swipePercent = clamped;

  const overlay = document.getElementById('swipe-overlay');
  const handle = document.getElementById('swipe-handle');
  if (overlay) overlay.style.width = `${clamped}%`;
  if (handle) handle.style.left = `${clamped}%`;
}

// Viewport Zoom & Pan Helpers
function poc3ApplyTransform() {
  const img = document.getElementById('reg-artifact-img');
  const badge = document.getElementById('reg-zoom-badge');
  if (img) {
    img.style.transform = `translate(${poc3State.panX}px, ${poc3State.panY}px) scale(${poc3State.zoom})`;
  }
  if (badge) {
    badge.textContent = `${Math.round(poc3State.zoom * 100)}%`;
  }
}

function poc3ResetZoom() {
  poc3State.zoom = 1.0;
  poc3State.panX = 0;
  poc3State.panY = 0;
  poc3ApplyTransform();
}

function poc3Zoom(delta) {
  poc3State.zoom = Math.max(0.2, Math.min(5.0, poc3State.zoom + delta));
  poc3ApplyTransform();
}

// Initialize POC 3 Event Listeners and Interactive Bindings
function initPOC3() {
  // Source & Reference Selection Change Listeners
  const selSrc = document.getElementById('reg-select-source');
  const selRef = document.getElementById('reg-select-reference');
  selSrc?.addEventListener('change', (e) => {
    poc3State.selectedSourceId = e.target.value;
    updateRegistrationPairDisplay();
  });
  selRef?.addEventListener('change', (e) => {
    poc3State.selectedRefId = e.target.value;
    updateRegistrationPairDisplay();
  });

  // Top Navigation Buttons
  document.getElementById('btn-nav-layer1')?.addEventListener('click', () => switchModule('layer1'));
  document.getElementById('btn-nav-poc3')?.addEventListener('click', () => switchModule('poc3'));

  // Inspector Quick Launch Button
  document.getElementById('btn-inspect-register-poc3')?.addEventListener('click', () => {
    if (state.selectedObservation) {
      switchModule('poc3');
      poc3SetSelectedPair(state.selectedObservation.product_id, null);
    }
  });

  // Benchmark Preset Buttons
  const loadPreset = () => {
    poc3SetDefaultBoguslawskyPair();
  };
  document.getElementById('btn-load-boguslawsky-pair')?.addEventListener('click', loadPreset);
  document.getElementById('btn-preset-boguslawsky')?.addEventListener('click', loadPreset);
  document.getElementById('btn-empty-quickrun')?.addEventListener('click', () => {
    loadPreset();
    executeRegistration();
  });

  // Algorithm Pills
  const algoPills = document.querySelectorAll('#reg-algo-pills .algo-pill');
  algoPills.forEach(pill => {
    pill.addEventListener('click', () => {
      algoPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const method = pill.dataset.method;
      poc3State.selectedMethod = method;

      const doc = ALGORITHM_DOCS[method];
      if (doc) {
        const titleEl = document.getElementById('algo-info-name');
        const descEl = document.getElementById('algo-info-desc');
        if (titleEl) titleEl.textContent = doc.name;
        if (descEl) descEl.textContent = doc.desc;
      }
    });
  });

  // Transformation Model Pills
  const transPills = document.querySelectorAll('#reg-transform-pills .toggle-pill');
  transPills.forEach(pill => {
    pill.addEventListener('click', () => {
      transPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      poc3State.selectedTransform = pill.dataset.transform;
    });
  });

  // Slider Ratio Thresh
  const sliderRatio = document.getElementById('slider-ratio-thresh');
  const valRatio = document.getElementById('val-ratio-thresh');
  sliderRatio?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    poc3State.ratioThresh = val;
    if (valRatio) valRatio.textContent = val.toFixed(2);
  });

  // Slider RANSAC Thresh
  const sliderRansac = document.getElementById('slider-ransac-thresh');
  const valRansac = document.getElementById('val-ransac-thresh');
  sliderRansac?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    poc3State.ransacThresh = val;
    if (valRansac) valRansac.textContent = `${val.toFixed(1)} px`;
  });

  // Execute Registration Button
  document.getElementById('btn-execute-reg')?.addEventListener('click', executeRegistration);

  // Stage View Tabs
  const stageTabs = document.querySelectorAll('#reg-view-tabs .stage-tab');
  stageTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      stageTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      poc3State.activeViewTab = tab.dataset.view;
      updateStageView();
    });
  });

  // Viewport Zoom & HUD Controls
  document.getElementById('btn-reg-zoom-in')?.addEventListener('click', () => poc3Zoom(0.25));
  document.getElementById('btn-reg-zoom-out')?.addEventListener('click', () => poc3Zoom(-0.25));
  document.getElementById('btn-reg-zoom-reset')?.addEventListener('click', poc3ResetZoom);
  document.getElementById('btn-reg-zoom-fit')?.addEventListener('click', poc3ResetZoom);

  // Canvas Pan & Drag Controls
  const canvasWrapper = document.getElementById('reg-canvas-wrapper');
  if (canvasWrapper) {
    canvasWrapper.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      poc3Zoom(delta);
    }, { passive: false });

    canvasWrapper.addEventListener('mousedown', (e) => {
      poc3State.isDraggingCanvas = true;
      poc3State.dragStartX = e.clientX - poc3State.panX;
      poc3State.dragStartY = e.clientY - poc3State.panY;
    });

    window.addEventListener('mousemove', (e) => {
      if (poc3State.isDraggingCanvas) {
        poc3State.panX = e.clientX - poc3State.dragStartX;
        poc3State.panY = e.clientY - poc3State.dragStartY;
        poc3ApplyTransform();
      }
    });

    window.addEventListener('mouseup', () => {
      poc3State.isDraggingCanvas = false;
    });
  }

  // Swipe Comparator Drag Handle
  const swipeContainer = document.getElementById('swipe-container');
  const swipeHandle = document.getElementById('swipe-handle');
  if (swipeHandle && swipeContainer) {
    const handleSwipeMove = (clientX) => {
      const rect = swipeContainer.getBoundingClientRect();
      const offsetX = clientX - rect.left;
      const pct = (offsetX / rect.width) * 100;
      setSwipePosition(pct);
    };

    swipeHandle.addEventListener('mousedown', (e) => {
      poc3State.isSwiping = true;
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (poc3State.isSwiping) {
        handleSwipeMove(e.clientX);
      }
    });

    window.addEventListener('mouseup', () => {
      poc3State.isSwiping = false;
    });

    // Touch events for mobile/tablet
    swipeHandle.addEventListener('touchstart', (e) => {
      poc3State.isSwiping = true;
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (poc3State.isSwiping && e.touches.length > 0) {
        handleSwipeMove(e.touches[0].clientX);
      }
    }, { passive: true });

    window.addEventListener('touchend', () => {
      poc3State.isSwiping = false;
    });
  }

  // Export Metrics as JSON
  document.getElementById('btn-export-json')?.addEventListener('click', () => {
    if (!poc3State.currentJob) {
      alert("No active registration job to export.");
      return;
    }
    const jsonStr = JSON.stringify(poc3State.currentJob, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nexus_lunar_registration_${poc3State.currentJob.job_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}

// Start Application on Load
document.addEventListener('DOMContentLoaded', () => {
  initData();
  initPOC3();
});

