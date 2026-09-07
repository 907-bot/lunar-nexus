/**
 * NEXUS-LUNAR: Client-Side Application Logic
 * Integrates Leaflet GIS, Overlap Engine, and Interactive Patch Studio
 */

// Global State
const state = {
  catalog: [],
  pairs: [],
  activePair: null,
  activeManifest: null,
  activePatch: null,
  map: null,
  footprintsLayer: null,
  blinkInterval: null,
};

// Sensor styling definitions
const SENSOR_COLORS = {
  OHRC: { color: '#00f2fe', fillColor: '#00f2fe', name: 'Chandrayaan-2 OHRC' },
  LRO_NAC: { color: '#ff7675', fillColor: '#ff7675', name: 'NASA LRO NAC' },
  TMC2: { color: '#55efc4', fillColor: '#55efc4', name: 'Chandrayaan-2 TMC-2' },
  IIRS: { color: '#a29bfe', fillColor: '#a29bfe', name: 'Chandrayaan-2 IIRS' },
  DEFAULT: { color: '#58a6ff', fillColor: '#58a6ff', name: 'Lunar Payload' },
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  initTabs();
  initMap();
  initSplitSlider();
  initModal();
  initLightbox();
  initPOC4Studio();
  initPOC5Studio();
  await loadCatalogAndPairs();
});

// ==========================================================================
// Navigation Tabs
// ==========================================================================
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');

      if (targetId === 'tab-map' && state.map) {
        setTimeout(() => state.map.invalidateSize(), 150);
      }
    });
  });

  // Check URL hash for direct tab linking (e.g. #poc4, #patches, #catalog, #map)
  if (window.location.hash) {
    const hash = window.location.hash.replace('#', '').toLowerCase();
    const matchingTab = document.querySelector(`.nav-tab[data-tab="tab-${hash}"]`);
    if (matchingTab) {
      matchingTab.click();
    }
  }

  document.getElementById('btnRefreshCatalog').addEventListener('click', loadCatalogAndPairs);
}

// ==========================================================================
// Lunar Leaflet GIS Map
// ==========================================================================
function initMap() {
  // Center near Boguslawsky South Pole Crater (-73.25, 26.0)
  state.map = L.map('lunarMap', {
    center: [-73.25, 26.0],
    zoom: 6,
    minZoom: 1,
    maxZoom: 14,
    attributionControl: false,
  });

  // Basemap: USGS Lunar Reconnaissance Orbiter (LRO) WAC Global Mosaic (via USGS Astropedia / NASA JPL WMTS)
  // Fallback to NASA Moon imagery or OpenPlanetary tiles
  const lunarTiles = L.tileLayer('https://cartocdn-gusc.global.ssl.fastly.net/opmbuilder/api/v1/map/named/opm-moon-basemap-v0-1/all/{z}/{x}/{y}.png', {
    maxNativeZoom: 9,
    maxZoom: 14,
    attribution: 'NASA / USGS / LRO WAC Global Morphologic Mosaic / OpenPlanetary',
    errorTileUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" style="background:%23050811"><text x="128" y="128" fill="%23223049" font-family="sans-serif" font-size="12" text-anchor="middle">Lunar Tile</text></svg>'
  });
  lunarTiles.addTo(state.map);

  state.footprintsLayer = L.layerGroup().addTo(state.map);

  // Jump buttons
  document.querySelectorAll('.btn-jump').forEach(btn => {
    btn.addEventListener('click', () => {
      const lat = parseFloat(btn.getAttribute('data-lat'));
      const lon = parseFloat(btn.getAttribute('data-lon'));
      const zoom = parseInt(btn.getAttribute('data-zoom'));
      state.map.flyTo([lat, lon], zoom, { duration: 1.2 });
    });
  });

  // Sensor checkbox filters
  document.querySelectorAll('.sensor-filter').forEach(checkbox => {
    checkbox.addEventListener('change', renderFootprints);
  });
}

// ==========================================================================
// Data Ingestion & API Calls
// ==========================================================================
async function loadCatalogAndPairs() {
  try {
    document.getElementById('statusText').innerText = 'Syncing...';

    // 1. Fetch Catalog
    const catRes = await fetch('/api/catalog');
    state.catalog = await catRes.json();

    // 2. Fetch Overlapping Pairs
    const pairsRes = await fetch('/api/pairs');
    state.pairs = await pairsRes.json();

    document.getElementById('statusText').innerText = `${state.catalog.length} Products Online`;
    document.getElementById('pairCountBadge').innerText = state.pairs.length;

    renderFootprints();
    renderPairsList();
    renderCatalogTable();

    // Auto-select first pair if exists
    if (state.pairs.length > 0) {
      selectPair(state.pairs[0]);
    }
  } catch (err) {
    console.error('Error loading data:', err);
    document.getElementById('statusText').innerText = 'Offline / Standalone';
  }
}

// ==========================================================================
// Footprints Renderer
// ==========================================================================
function renderFootprints() {
  if (!state.footprintsLayer) return;
  state.footprintsLayer.clearLayers();

  const enabledSensors = Array.from(document.querySelectorAll('.sensor-filter:checked')).map(cb => cb.value);
  let visibleCount = 0;

  state.catalog.forEach(obs => {
    if (!enabledSensors.includes(obs.sensor)) return;
    visibleCount++;

    const sensorDef = SENSOR_COLORS[obs.sensor] || SENSOR_COLORS.DEFAULT;
    const bounds = [
      [obs.bbox.min_lat, obs.bbox.min_lon],
      [obs.bbox.max_lat, obs.bbox.max_lon]
    ];

    const rect = L.rectangle(bounds, {
      color: sensorDef.color,
      weight: 2,
      fillColor: sensorDef.fillColor,
      fillOpacity: 0.15,
      dashArray: obs.sensor === 'OHRC' ? '4, 4' : null,
    });

    rect.bindPopup(`
      <div style="font-family: 'Outfit', sans-serif; color: #111; padding: 4px;">
        <strong style="color: #0072ff;">${obs.product_id}</strong><br/>
        <span style="font-size: 0.8rem; color: #555;">${sensorDef.name} (${obs.resolution_m}m)</span><br/>
        <div style="margin-top: 6px; font-size: 0.75rem;">
          <strong>Lat:</strong> [${obs.bbox.min_lat.toFixed(2)}, ${obs.bbox.max_lat.toFixed(2)}]<br/>
          <strong>Lon:</strong> [${obs.bbox.min_lon.toFixed(2)}, ${obs.bbox.max_lon.toFixed(2)}]<br/>
          <strong>Incidence:</strong> ${obs.incidence_angle ? obs.incidence_angle.toFixed(1) + '°' : 'N/A'}
        </div>
      </div>
    `);

    rect.on('click', () => {
      displayObservationCard(obs);
    });

    rect.addTo(state.footprintsLayer);
  });

  document.getElementById('visibleFootprintsCount').innerText = `${visibleCount} visible`;
}

function displayObservationCard(obs) {
  const card = document.getElementById('selectedObservationCard');
  const sensorDef = SENSOR_COLORS[obs.sensor] || SENSOR_COLORS.DEFAULT;

  card.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 8px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <span class="tag-pill" style="background: rgba(0, 242, 254, 0.2); color: ${sensorDef.color}">${obs.sensor}</span>
        <span style="font-size: 0.75rem; color: var(--text-secondary);">${obs.resolution_m}m GSD</span>
      </div>
      <div style="font-size: 0.85rem; font-weight: 700; color: #fff; word-break: break-all;">${obs.product_id}</div>
      <div style="font-size: 0.75rem; color: var(--text-secondary);">
        <strong>Bounds:</strong> Lat [${obs.bbox.min_lat.toFixed(2)}°, ${obs.bbox.max_lat.toFixed(2)}°]<br/>
        Lon [${obs.bbox.min_lon.toFixed(2)}°, ${obs.bbox.max_lon.toFixed(2)}°]<br/>
        <strong>Incidence:</strong> ${obs.incidence_angle ? obs.incidence_angle.toFixed(1) + '°' : 'N/A'}
      </div>
      <button class="btn-primary" style="padding: 6px 12px; font-size: 0.78rem; margin-top: 4px;" onclick="switchToPairForProduct('${obs.product_id}')">
        Open in Patch Studio
      </button>
    </div>
  `;
}

window.switchToPairForProduct = function(productId) {
  const pair = state.pairs.find(p => p.source_product_id === productId || p.reference_product_id === productId);
  if (pair) {
    document.getElementById('tabBtnPatches').click();
    selectPair(pair);
  } else {
    alert(`No candidate overlap pairs currently discovered for ${productId}`);
  }
};

// ==========================================================================
// POC 2: Overlapping Pairs Sidebar & Patch Studio
// ==========================================================================
function renderPairsList() {
  const container = document.getElementById('pairsContainer');
  container.innerHTML = '';

  if (state.pairs.length === 0) {
    container.innerHTML = `
      <div class="card-empty-state">
        <span>No overlapping pairs found with current thresholds.</span>
      </div>
    `;
    return;
  }

  state.pairs.forEach((pair, idx) => {
    const card = document.createElement('div');
    card.className = `pair-card ${state.activePair === pair ? 'active' : ''}`;
    card.innerHTML = `
      <div class="pair-badge-row">
        <span class="badge-overlap">${pair.overlap_percent_of_source}% Overlap</span>
        <span style="font-size: 0.7rem; color: var(--text-dim);">${pair.overlap_area_km2 || 'N/A'} km²</span>
      </div>
      <div class="pair-names">
        <span>${pair.source_sensor}</span> ${pair.source_product_id.split('_').slice(0, 3).join('_')}
        <br/>
        <span style="color: var(--sensor-lro);">${pair.reference_sensor}</span> ${pair.reference_product_id}
      </div>
      <div class="pair-stats">
        <span>Res: ${pair.source_resolution_m}m vs ${pair.reference_resolution_m}m</span>
        <span>Δ Sun: ${pair.solar_incidence_diff_deg?.toFixed(1) || 0}°</span>
      </div>
    `;

    card.addEventListener('click', () => {
      document.querySelectorAll('.pair-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      selectPair(pair);
    });

    container.appendChild(card);
  });
}

async function selectPair(pair) {
  state.activePair = pair;
  document.getElementById('btnOpenExtractModal').disabled = false;
  const btnViewMap = document.getElementById('btnViewPairOnMap');
  if (btnViewMap) {
    btnViewMap.disabled = false;
    btnViewMap.onclick = () => {
      document.getElementById('tabBtnMap').click();
      highlightIntersectionOnMap(pair);
    };
  }

  document.getElementById('bannerPairTitle').innerHTML = `
    <span>${pair.source_sensor}</span> vs <span>${pair.reference_sensor}</span>: Boguslawsky Overlap Region
  `;
  document.getElementById('bannerPairMeta').innerText = `
    Overlap: ${pair.overlap_percent_of_source}% • Area: ${pair.overlap_area_km2 || 'N/A'} km² • Source Res: ${pair.source_resolution_m}m • Ref Res: ${pair.reference_resolution_m}m
  `;

  document.getElementById('lblSrcTag').innerText = `Source (${pair.source_sensor})`;
  document.getElementById('lblRefTag').innerText = `Reference (${pair.reference_sensor})`;

  // Fetch patch manifest for this pair if exists
  await loadManifestForPair(pair);
}

function highlightIntersectionOnMap(pair) {
  if (!state.map || !pair.intersection_bbox) return;
  if (state.overlapHighlightLayer) {
    state.map.removeLayer(state.overlapHighlightLayer);
  }
  const ibox = pair.intersection_bbox;
  const bounds = [
    [ibox.min_lat, ibox.min_lon],
    [ibox.max_lat, ibox.max_lon]
  ];
  state.overlapHighlightLayer = L.rectangle(bounds, {
    color: '#ffd32a',
    weight: 3,
    fillColor: '#ffd32a',
    fillOpacity: 0.35,
    dashArray: '5, 5'
  }).addTo(state.map);

  state.overlapHighlightLayer.bindPopup(`
    <div style="font-family: 'Outfit', sans-serif; color: #111;">
      <strong style="color: #d63031;">Active Overlap Intersection Zone</strong><br/>
      <span style="font-size: 0.8rem; color: #333;">${pair.source_sensor} <-> ${pair.reference_sensor}</span><br/>
      <strong>Overlap:</strong> ${pair.overlap_percent_of_source}% (${pair.overlap_area_km2 || 'N/A'} km²)
    </div>
  `).openPopup();

  state.map.flyToBounds(bounds, { padding: [50, 50], duration: 1.2 });
}


async function loadManifestForPair(pair) {
  const pairKey = `${pair.source_product_id}___${pair.reference_product_id}`;
  try {
    const res = await fetch(`/api/manifest?pair_id=${encodeURIComponent(pairKey)}`);
    if (res.ok) {
      const manifest = await res.json();
      if (manifest && manifest.total_patches > 0) {
        state.activeManifest = manifest;
        renderPatchesGrid(manifest);
      } else {
        state.activeManifest = null;
        renderEmptyPatchesGrid(pair);
      }
    } else {
      state.activeManifest = null;
      renderEmptyPatchesGrid(pair);
    }
  } catch (e) {
    console.error('Error fetching manifest:', e);
    renderEmptyPatchesGrid(pair);
  }
}

function renderEmptyPatchesGrid(pair) {
  const container = document.getElementById('patchesGridView');
  container.innerHTML = `
    <div class="card-empty-state" style="grid-column: 1 / -1; padding: 40px 0;">
      <p style="font-size: 0.95rem; color: var(--text-main);">No patches extracted yet for this pair.</p>
      <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
        Click <strong>"Configure & Extract Patches"</strong> above to extract resolution-harmonized co-registered patches.
      </p>
    </div>
  `;
  document.getElementById('patchStatsPills').innerHTML = '';
}

function renderPatchesGrid(manifest) {
  const container = document.getElementById('patchesGridView');
  container.innerHTML = '';

  const pills = document.getElementById('patchStatsPills');
  pills.innerHTML = `
    <span class="tag-pill">${manifest.total_patches} Patches Generated</span>
    <span class="tag-pill" style="background: rgba(46, 213, 115, 0.15); color: #2ed573;">GSD: ${manifest.patches[0]?.effective_resolution_m || 'N/A'}m</span>
  `;

  manifest.patches.forEach((patch, idx) => {
    const tile = document.createElement('div');
    tile.className = `patch-tile-card ${idx === 0 ? 'selected' : ''}`;
    
    // Normalize image paths for web browser
    const srcImgUrl = `/data/processed/patches/${manifest.source_product_id}___${manifest.reference_product_id}/${patch.source_patch_path.split('\\').pop().split('/').pop()}`;
    const refImgUrl = `/data/processed/patches/${manifest.source_product_id}___${manifest.reference_product_id}/${patch.reference_patch_path.split('\\').pop().split('/').pop()}`;

    tile.innerHTML = `
      <div class="patch-tile-header">
        <span class="patch-tile-id">Patch #${patch.patch_index.toString().padStart(4, '0')}</span>
        <span class="patch-tile-score">Score: ${(patch.quality_score * 100).toFixed(0)}%</span>
      </div>
      <div class="patch-dual-thumbnails">
        <div class="thumb-item">
          <img src="${srcImgUrl}" alt="Source Patch" loading="lazy">
          <span class="thumb-label">Source</span>
        </div>
        <div class="thumb-item">
          <img src="${refImgUrl}" alt="Reference Patch" loading="lazy">
          <span class="thumb-label">Reference</span>
        </div>
      </div>
      <div class="patch-tile-footer">
        <span>Lat: [${patch.ground_bbox.min_lat.toFixed(2)}°, ${patch.ground_bbox.max_lat.toFixed(2)}°]</span>
        <span>Lon: [${patch.ground_bbox.min_lon.toFixed(2)}°, ${patch.ground_bbox.max_lon.toFixed(2)}°]</span>
      </div>
    `;

    tile.addEventListener('click', () => {
      document.querySelectorAll('.patch-tile-card').forEach(t => t.classList.remove('selected'));
      tile.classList.add('selected');
      loadPatchIntoViewer(patch, srcImgUrl, refImgUrl);
    });

    container.appendChild(tile);
  });

  // Load first patch into split viewer
  if (manifest.patches.length > 0) {
    const first = manifest.patches[0];
    const srcImgUrl = `/data/processed/patches/${manifest.source_product_id}___${manifest.reference_product_id}/${first.source_patch_path.split('\\').pop().split('/').pop()}`;
    const refImgUrl = `/data/processed/patches/${manifest.source_product_id}___${manifest.reference_product_id}/${first.reference_patch_path.split('\\').pop().split('/').pop()}`;
    loadPatchIntoViewer(first, srcImgUrl, refImgUrl);
  }
}

function loadPatchIntoViewer(patch, srcImgUrl, refImgUrl) {
  state.activePatch = patch;
  document.getElementById('currentPatchLabel').innerText = `Patch #${patch.patch_index.toString().padStart(4, '0')}`;
  
  const imgRef = document.getElementById('imgRefView');
  const imgSrc = document.getElementById('imgSrcView');
  
  imgRef.src = refImgUrl;
  imgSrc.src = srcImgUrl;
}

// ==========================================================================
// Split Screen Comparison Slider & Blinking
// ==========================================================================
function initSplitSlider() {
  const slider = document.getElementById('compareSlider');
  const layerSrc = document.getElementById('layerSrc');
  const dividerLine = document.getElementById('dividerLine');

  slider.addEventListener('input', (e) => {
    const val = e.target.value;
    layerSrc.style.width = `${val}%`;
    dividerLine.style.left = `${val}%`;
  });

  // Toggle Blink Mode (alternates opacity rapidly to spot subtle ground disparities)
  const btnBlink = document.getElementById('btnToggleMode');
  btnBlink.addEventListener('click', () => {
    if (state.blinkInterval) {
      clearInterval(state.blinkInterval);
      state.blinkInterval = null;
      btnBlink.innerText = 'Toggle Blink';
      layerSrc.style.opacity = '1';
      layerSrc.style.width = `${slider.value}%`;
      dividerLine.style.display = 'block';
    } else {
      btnBlink.innerText = 'Stop Blink';
      layerSrc.style.width = '100%';
      dividerLine.style.display = 'none';
      let toggle = false;
      state.blinkInterval = setInterval(() => {
        layerSrc.style.opacity = toggle ? '1' : '0';
        toggle = !toggle;
      }, 500);
    }
  });
}

// ==========================================================================
// Patch Extraction Modal
// ==========================================================================
function initModal() {
  const modal = document.getElementById('extractModal');
  const btnOpen = document.getElementById('btnOpenExtractModal');
  const btnClose = document.getElementById('btnCloseExtractModal');
  const btnCancel = document.getElementById('btnCancelModal');
  const btnRun = document.getElementById('btnRunExtraction');

  btnOpen.addEventListener('click', () => {
    if (!state.activePair) return;
    document.getElementById('modalSourceId').value = state.activePair.source_product_id;
    document.getElementById('modalRefId').value = state.activePair.reference_product_id;
    modal.classList.add('show');
  });

  const closeModal = () => modal.classList.remove('show');
  btnClose.addEventListener('click', closeModal);
  btnCancel.addEventListener('click', closeModal);

  btnRun.addEventListener('click', async () => {
    const patchSize = parseInt(document.getElementById('modalPatchSize').value);
    const stride = parseInt(document.getElementById('modalStride').value);
    const strategy = document.getElementById('modalStrategy').value;

    btnRun.innerText = 'Extracting Patches...';
    btnRun.disabled = true;

    try {
      const res = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_product_id: state.activePair.source_product_id,
          reference_product_id: state.activePair.reference_product_id,
          patch_size: patchSize,
          stride: stride,
          strategy: strategy,
        })
      });

      if (res.ok) {
        const manifest = await res.json();
        closeModal();
        state.activeManifest = manifest;
        renderPatchesGrid(manifest);
        alert(`Successfully extracted ${manifest.total_patches} patch pairs!`);
      } else {
        const err = await res.text();
        alert(`Extraction failed: ${err}`);
      }
    } catch (err) {
      alert(`Error during extraction: ${err}`);
    } finally {
      btnRun.innerText = 'Run Patch Extraction Engine';
      btnRun.disabled = false;
    }
  });
}

// ==========================================================================
// Catalog Table View
// ==========================================================================
function renderCatalogTable() {
  const tbody = document.getElementById('catalogTableBody');
  tbody.innerHTML = '';

  const searchInput = document.getElementById('catalogSearchInput');
  const query = searchInput.value.toLowerCase();

  const filtered = state.catalog.filter(obs => {
    return obs.product_id.toLowerCase().includes(query) ||
           obs.sensor.toLowerCase().includes(query) ||
           obs.mission.toLowerCase().includes(query);
  });

  filtered.forEach(obs => {
    const tr = document.createElement('tr');
    
    // Resolve thumbnail path
    let thumbUrl = '/data/raw/ohrc/placeholder.png';
    if (obs.primary_image) {
      thumbUrl = '/' + obs.primary_image.replace(/\\/g, '/');
    } else if (obs.preview_image) {
      thumbUrl = '/' + obs.preview_image.replace(/\\/g, '/');
    }

    tr.innerHTML = `
      <td>
        <img src="${thumbUrl}" class="cell-thumb" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'44\\' height=\\'44\\' style=\\'background:%23111\\'><text x=\\'22\\' y=\\'26\\' fill=\\'%23666\\' font-size=\\'9\\' text-anchor=\\'middle\\'>NO IMG</text></svg>'"/>
      </td>
      <td class="cell-id">${obs.product_id}</td>
      <td>${obs.mission}</td>
      <td><span class="badge-sensor badge-sensor-${obs.sensor}">${obs.sensor}</span></td>
      <td>${obs.resolution_m ? obs.resolution_m + 'm' : 'N/A'}</td>
      <td>[${obs.bbox.min_lat.toFixed(2)}°, ${obs.bbox.max_lat.toFixed(2)}°]</td>
      <td>[${obs.bbox.min_lon.toFixed(2)}°, ${obs.bbox.max_lon.toFixed(2)}°]</td>
      <td>${obs.incidence_angle ? obs.incidence_angle.toFixed(1) + '°' : 'N/A'}</td>
      <td>
        <button class="btn-primary" style="padding: 4px 8px; font-size: 0.72rem;" onclick="jumpToObservation('${obs.product_id}')">
          Locate Map
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  searchInput.oninput = renderCatalogTable;
}

window.jumpToObservation = function(productId) {
  const obs = state.catalog.find(o => o.product_id === productId);
  if (!obs) return;

  document.getElementById('tabBtnMap').click();
  state.map.flyTo(obs.center, 7, { duration: 1.0 });
  displayObservationCard(obs);
};

// ==========================================================================
// POC 4: Illumination & Scale Robustness Studio
// ==========================================================================
function initLightbox() {
  const modal = document.getElementById('imagePreviewModal');
  const modalImg = document.getElementById('previewModalImg');
  const modalTitle = document.getElementById('previewModalTitle');
  const btnClose = document.getElementById('btnClosePreviewModal');

  if (!modal) return;

  document.querySelectorAll('.img-preview-trigger').forEach(img => {
    img.addEventListener('click', () => {
      const src = img.getAttribute('src');
      const title = img.getAttribute('data-title') || 'Figure Preview';
      modalImg.src = src;
      modalTitle.innerText = title;
      modal.classList.add('show');
      modal.style.display = 'flex';
    });
  });

  const closeModal = () => {
    modal.classList.remove('show');
    modal.style.display = 'none';
  };

  if (btnClose) btnClose.addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });
}

// ==========================================================================
// POC 4: Illumination + Scale Robustness Studio Engine
// ==========================================================================
let currentPOC4Data = null;
let currentPOC4Seed = 42;

function showPOC4Toast(msg) {
  let toast = document.getElementById('poc4Toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'poc4Toast';
    toast.className = 'nexus-toast';
    document.body.appendChild(toast);
  }
  toast.innerText = msg;
  toast.classList.add('visible');
  setTimeout(() => {
    toast.classList.remove('visible');
  }, 3800);
}

function initPOC4Studio() {
  const btnRun = document.getElementById('btnRunPOC4Experiment');
  const btnReroll = document.getElementById('btnRerollPOC4');
  const selectCond = document.getElementById('poc4ConditionSelect');
  const selectScale = document.getElementById('poc4ScaleSelect');

  if (btnRun) {
    btnRun.addEventListener('click', () => runPOC4FullPipeline(42));
  }
  if (btnReroll) {
    btnReroll.addEventListener('click', () => {
      const randomSeed = Math.floor(Math.random() * 90000 + 10000);
      runPOC4FullPipeline(randomSeed);
    });
  }

  if (selectCond) {
    selectCond.addEventListener('change', () => {
      if (currentPOC4Data) renderPOC4DynamicView(currentPOC4Data);
    });
  }
  if (selectScale) {
    selectScale.addEventListener('change', () => {
      if (currentPOC4Data) renderPOC4DynamicView(currentPOC4Data);
    });
  }

  // Load existing results if available
  loadPOC4Results();
}

async function loadPOC4Results() {
  try {
    const res = await fetch('/api/poc4/results');
    if (res.ok) {
      const data = await res.json();
      currentPOC4Data = data;
      renderPOC4DynamicView(data);
    }
  } catch (e) {
    console.log('POC-4 cached results not available yet.');
  }
}

async function runPOC4FullPipeline(seed = 42) {
  const btnRun = document.getElementById('btnRunPOC4Experiment');
  const btnReroll = document.getElementById('btnRerollPOC4');
  const progressCard = document.getElementById('poc4ProgressCard');
  const progressBar = document.getElementById('poc4ProgressBar');
  const stepLabel = document.getElementById('poc4CurrentStep');
  const stepBadges = document.querySelectorAll('#poc4StepsFlow .step-badge');

  if (btnRun) btnRun.disabled = true;
  if (btnReroll) btnReroll.disabled = true;

  if (btnRun) {
    btnRun.innerHTML = `
      <span class="spinner" style="width: 14px; height: 14px; border-width: 2px; display: inline-block;"></span>
      Executing Matrix (Seed ${seed})...
    `;
  }
  if (progressCard) progressCard.style.display = 'flex';

  const steps = [
    { name: '1. Ingesting Real Geographic Base Patch...', percent: 12, index: 0 },
    { name: '2. Applying 8 Illumination Transformations...', percent: 25, index: 1 },
    { name: '3. Computing Shadow Morphological Masks...', percent: 38, index: 2 },
    { name: '4. Generating 4-Octave Multi-Scale Pyramids...', percent: 50, index: 3 },
    { name: '5. Extracting Spatial Gradient Features...', percent: 62, index: 4 },
    { name: '6. Nearest-Neighbor Lowe Ratio Matching...', percent: 74, index: 5 },
    { name: '7. Executing RANSAC Geometric Verification...', percent: 85, index: 6 },
    { name: '8. Computing Ground Truth Recall@K & Inlier Metrics...', percent: 93, index: 7 },
    { name: '9. Generating Publication-Quality Figures & CSV...', percent: 100, index: 8 }
  ];

  let currentStepIdx = 0;
  const progressTimer = setInterval(() => {
    if (currentStepIdx < steps.length) {
      const s = steps[currentStepIdx];
      if (stepLabel) stepLabel.innerText = s.name;
      if (progressBar) progressBar.style.width = `${s.percent}%`;
      
      stepBadges.forEach((b, idx) => {
        if (idx < currentStepIdx) {
          b.className = 'step-badge completed';
        } else if (idx === currentStepIdx) {
          b.className = 'step-badge active';
        } else {
          b.className = 'step-badge';
        }
      });
      currentStepIdx++;
    }
  }, 450);

  const startTime = Date.now();

  try {
    const res = await fetch('/api/poc4/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_product_id: 'ch2_ohr_ncp_20260103t1005176450_d_img_d18',
        reference_product_id: 'SYNTHETIC_LROC_CANDIDATE_P850S0250',
        seed: seed
      })
    });

    clearInterval(progressTimer);

    if (res.ok) {
      const data = await res.json();
      currentPOC4Data = data;
      currentPOC4Seed = seed;
      const elapsedSec = ((Date.now() - startTime) / 1000).toFixed(2);

      if (progressBar) progressBar.style.width = '100%';
      if (stepLabel) stepLabel.innerText = `Experiment Completed in ${elapsedSec}s!`;
      stepBadges.forEach(b => b.className = 'step-badge completed');
      
      setTimeout(() => {
        renderPOC4DynamicView(data);
        refreshFigureImages();
        if (progressCard) progressCard.style.display = 'none';
        showPOC4Toast(`✓ POC-4 Experiment Run Complete (Seed ${seed}, ${elapsedSec}s) — All figures and tables refreshed!`);
      }, 700);
    } else {
      const err = await res.text();
      alert('POC-4 Experiment run error: ' + err);
    }
  } catch (err) {
    clearInterval(progressTimer);
    console.error('POC-4 execution failure:', err);
    alert('Failed to connect to POC-4 experiment service: ' + err);
  } finally {
    if (btnRun) {
      btnRun.disabled = false;
      btnRun.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        RUN EXPERIMENT (SEED 42)
      `;
    }
    if (btnReroll) btnReroll.disabled = false;
  }
}

function refreshFigureImages() {
  const t = Date.now();
  document.querySelectorAll('.gallery-img-box img').forEach(img => {
    const base = img.src.split('?')[0];
    img.src = `${base}?t=${t}`;
  });
}

function renderPOC4DynamicView(data) {
  if (!data) return;

  const selectCond = document.getElementById('poc4ConditionSelect');
  const selectScale = document.getElementById('poc4ScaleSelect');
  const activeCond = selectCond ? selectCond.value : 'ALL';
  const activeScale = selectScale ? selectScale.value : 'ALL';

  // Update Provenance
  const provLabel = document.getElementById('poc4ProvenanceLabel');
  if (provLabel) {
    provLabel.innerText = data.metadata?.data_provenance || 'REAL-GEOGRAPHY / SYNTHETIC-ILLUMINATION EXPERIMENT';
  }

  // Update Run Status Banner
  const statusText = document.getElementById('poc4RunStatusText');
  const now = new Date();
  const timeStr = now.toLocaleTimeString();
  if (statusText) {
    statusText.innerHTML = `<strong>Live Run Active</strong> (Seed: <code>${currentPOC4Seed}</code>) • Filter: <strong>${activeCond}</strong> | Scale: <strong>${activeScale}</strong> • Updated ${timeStr}`;
  }

  // 1. Calculate representation metrics from matrix_results or summary
  const matrix = data.matrix_results || [];
  const repNames = ["RAW", "NORMALIZED", "GRADIENT", "MULTI-SCALE", "MULTI-SCALE + ILLUMINATION-AWARE"];
  const repMetrics = {};

  repNames.forEach(rName => {
    let rows = matrix.filter(r => r.representation.toUpperCase() === rName.toUpperCase());
    if (activeCond !== 'ALL') {
      rows = rows.filter(r => r.illumination_condition.toUpperCase() === activeCond.toUpperCase());
    }
    if (activeScale !== 'ALL') {
      const sVal = parseFloat(activeScale);
      rows = rows.filter(r => Math.abs(r.scale_factor - sVal) < 1e-3);
    }

    if (rows.length > 0) {
      const succ = rows.filter(r => r.alignment_success).length / rows.length;
      const inlier = rows.reduce((acc, r) => acc + (r.inlier_ratio || 0), 0) / rows.length;
      const validRmse = rows.map(r => r.rmse).filter(val => isFinite(val) && val < 50);
      const rmse = validRmse.length > 0 ? (validRmse.reduce((a, b) => a + b, 0) / validRmse.length) : 999.0;
      const validR1 = rows.map(r => r.recall_at_1).filter(val => val !== null && val !== undefined);
      const r1 = validR1.length > 0 ? (validR1.reduce((a, b) => a + b, 0) / validR1.length) : 0.0;
      repMetrics[rName] = {
        success_rate: succ,
        mean_inlier_ratio: inlier,
        mean_rmse: rmse,
        mean_recall_1: r1,
        evaluated_conditions: rows.length
      };
    } else {
      const fallback = (data.summary && data.summary.representation_metrics) ? data.summary.representation_metrics[rName] : null;
      if (fallback) {
        repMetrics[rName] = fallback;
      }
    }
  });

  // 2. Determine best representation for current filter view
  let bestRep = "MULTI-SCALE + ILLUMINATION-AWARE";
  let bestScore = -1;
  for (const [rName, m] of Object.entries(repMetrics)) {
    const score = (m.success_rate * 50) + (m.mean_inlier_ratio * 30) + Math.max(0, 20 - Math.min(20, m.mean_rmse));
    if (score > bestScore) {
      bestScore = score;
      bestRep = rName;
    }
  }

  // 3. Update Scorecards with values & Flash animation
  const elBestRep = document.getElementById('poc4BestRep');
  if (elBestRep) elBestRep.innerText = bestRep;

  const targetBest = repMetrics[bestRep] || repMetrics["MULTI-SCALE + ILLUMINATION-AWARE"] || repMetrics["MULTI-SCALE"];
  if (targetBest) {
    const elSuccess = document.getElementById('poc4SuccessRate');
    const elInlier = document.getElementById('poc4InlierRatio');
    const elRecall1 = document.getElementById('poc4Recall1');
    const elRmse = document.getElementById('poc4Rmse');

    if (elSuccess) elSuccess.innerText = `${(targetBest.success_rate * 100).toFixed(1)}%`;
    if (elInlier) elInlier.innerText = `${(targetBest.mean_inlier_ratio * 100).toFixed(1)}%`;
    if (elRecall1) elRecall1.innerText = `${(targetBest.mean_recall_1 * 100).toFixed(1)}%`;
    if (elRmse) elRmse.innerText = `${targetBest.mean_rmse < 900 ? targetBest.mean_rmse.toFixed(2) + ' px' : '999.00 px'}`;
  }

  // Flash scorecard for feedback
  document.querySelectorAll('.score-card').forEach(card => {
    card.classList.remove('card-flash');
    void card.offsetWidth;
    card.classList.add('card-flash');
  });

  // 4. Populate Baseline Comparison Table
  const tbody = document.getElementById('poc4ComparisonTableBody');
  if (tbody) {
    tbody.innerHTML = '';
    for (const [repName, m] of Object.entries(repMetrics)) {
      const tr = document.createElement('tr');
      const isWinner = repName === bestRep;
      if (isWinner) tr.className = 'highlight-row';

      let pillClass = 'pill-fail';
      let pillText = 'Baseline';
      if (m.success_rate >= 0.7) {
        pillClass = isWinner ? 'pill-winner' : 'pill-pass';
        pillText = isWinner ? '★ BEST PERFORMER' : 'High Robustness';
      } else if (m.success_rate >= 0.5) {
        pillClass = 'pill-pass';
        pillText = 'Scale Invariant';
      } else if (m.success_rate >= 0.2) {
        pillClass = 'pill-neutral';
        pillText = 'Partial';
      }

      tr.innerHTML = `
        <td><strong>${repName}</strong></td>
        <td>${(m.success_rate * 100).toFixed(1)}%</td>
        <td>${(m.mean_inlier_ratio * 100).toFixed(1)}%</td>
        <td>${(m.mean_recall_1 * 100).toFixed(1)}%</td>
        <td>${m.mean_rmse < 900 ? m.mean_rmse.toFixed(2) + ' px' : '999.00 px'}</td>
        <td><span class="${pillClass}">${pillText}</span></td>
      `;
      tbody.appendChild(tr);
    }
  }

  // 5. Populate Ablation Table
  const ablBody = document.getElementById('poc4AblationTableBody');
  const ablationList = data.ablation_results || data.ablation || [];
  if (ablBody && ablationList.length > 0) {
    ablBody.innerHTML = '';
    ablationList.forEach(row => {
      const tr = document.createElement('tr');
      const cfg = row.configuration || row.config_name || '';
      const isPass = row.alignment_success !== undefined ? row.alignment_success : row.success;
      const isBest = cfg.includes('ILLUMINATION-AWARE') && row.scale_harmonized;
      if (isBest) tr.className = 'highlight-row';

      tr.innerHTML = `
        <td>${cfg}</td>
        <td>${row.scale_harmonized ? 'Yes' : 'No'}</td>
        <td>${((row.inlier_ratio || 0) * 100).toFixed(1)}%</td>
        <td>${(row.rmse < 900 ? (row.rmse || 0).toFixed(2) + ' px' : '999.00 px')}</td>
        <td><span class="${isBest ? 'pill-winner' : (isPass ? 'pill-pass' : 'pill-fail')}">${isPass ? 'PASS' : 'FAIL'}</span></td>
      `;
      ablBody.appendChild(tr);
    });
  }
}

// ==========================================================================
// POC-5 Multimodal AI Correspondence Studio
// ==========================================================================
let poc5Data = null;

function initPOC5Studio() {
  const btnRun = document.getElementById('btnRunPOC5');
  const selectQuery = document.getElementById('poc5QuerySelect');

  if (btnRun) {
    btnRun.addEventListener('click', async () => {
      btnRun.disabled = true;
      btnRun.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Retraining & Retrieving...`;
      showPOC4Toast('Running Two-Tower AI Retrieval Pipeline (12 Epochs)...');
      try {
        const resp = await fetch('/api/poc5/run', { method: 'POST' });
        if (resp.ok) {
          showPOC4Toast('POC-5 Pipeline executed successfully!');
          await loadPOC5Data();
        } else {
          showPOC4Toast('Failed to run POC-5 pipeline: ' + resp.statusText);
        }
      } catch (err) {
        showPOC4Toast('Network error triggering POC-5: ' + err.message);
      } finally {
        btnRun.disabled = false;
        btnRun.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Run POC-5 Retrieval Pipeline`;
      }
    });
  }

  if (selectQuery) {
    selectQuery.addEventListener('change', () => {
      renderPOC5QueryRetrieval(selectQuery.value);
    });
  }

  // Initial load
  loadPOC5Data();
}

async function loadPOC5Data() {
  try {
    const res = await fetch('/api/poc5/results');
    if (!res.ok) return;
    poc5Data = await res.json();
    populatePOC5Metrics(poc5Data);
    populatePOC5QueryDropdown(poc5Data);
    populatePOC5Figures(poc5Data);
  } catch (e) {
    console.warn('Could not load POC 5 data:', e);
  }
}

function populatePOC5Metrics(data) {
  const s = data.summary || {};
  const r1El = document.getElementById('poc5Recall1Val');
  const r5El = document.getElementById('poc5Recall5Val');
  const r10El = document.getElementById('poc5Recall10Val');
  const mrrEl = document.getElementById('poc5MRRVal');

  if (r1El && s.recall_at_1 !== undefined) r1El.innerText = `${(s.recall_at_1 * 100).toFixed(1)}%`;
  if (r5El && s.recall_at_5 !== undefined) r5El.innerText = `${(s.recall_at_5 * 100).toFixed(1)}%`;
  if (r10El && s.recall_at_10 !== undefined) r10El.innerText = `${(s.recall_at_10 * 100).toFixed(1)}%`;
  if (mrrEl && s.mean_reciprocal_rank !== undefined) mrrEl.innerText = s.mean_reciprocal_rank.toFixed(3);
}

function populatePOC5QueryDropdown(data) {
  const selectQuery = document.getElementById('poc5QuerySelect');
  if (!selectQuery || !data.queries) return;

  selectQuery.innerHTML = '';
  data.queries.forEach((q, idx) => {
    const opt = document.createElement('option');
    opt.value = q.query_patch_id;
    opt.innerText = `${q.query_sensor || 'OHRC'} Query #${idx + 1} (${q.query_patch_id}) - True Rank: #${q.true_match_rank || 'N/A'}`;
    selectQuery.appendChild(opt);
  });

  if (data.queries.length > 0) {
    renderPOC5QueryRetrieval(data.queries[0].query_patch_id);
  }
}

function renderPOC5QueryRetrieval(queryId) {
  const container = document.getElementById('poc5RetrievalGrid');
  if (!container || !poc5Data || !poc5Data.queries) return;

  const qData = poc5Data.queries.find(q => q.query_patch_id === queryId);
  if (!qData) return;

  container.innerHTML = '';

  // 1. Query Card
  const qCard = document.createElement('div');
  qCard.className = 'glassmorphism';
  qCard.style.cssText = 'min-width: 220px; max-width: 220px; border: 2px solid #1a73e8; border-radius: 8px; padding: 0.8rem; background: rgba(26, 115, 232, 0.08);';
  qCard.innerHTML = `
    <div style="font-size: 0.75rem; font-weight: bold; color: #58a6ff; margin-bottom: 0.4rem; text-transform: uppercase;">
      ★ QUERY FOOTPRINT
    </div>
    <div style="font-weight: bold; font-size: 0.9rem; margin-bottom: 0.2rem;">${qData.query_patch_id}</div>
    <div style="font-size: 0.75rem; color: #8b949e; margin-bottom: 0.5rem;">Sensor: ${qData.query_sensor} | GSD: ${qData.query_gsd_m}m</div>
    <div style="background: #000; border-radius: 4px; height: 140px; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid #30363d;">
      <span style="font-size: 0.8rem; color: #8b949e;">Query Patch [${qData.query_sensor}]</span>
    </div>
    <div style="margin-top: 0.6rem; font-size: 0.75rem; color: #c9d1d9;">
      True Match Rank: <span class="pill-${qData.true_match_rank <= 5 ? 'pass' : 'neutral'}">#${qData.true_match_rank || 'N/A'}</span>
    </div>
  `;
  container.appendChild(qCard);

  // 2. Candidate Cards
  const candidates = qData.candidates || [];
  candidates.slice(0, 5).forEach(cand => {
    const isHit = cand.is_ground_truth;
    const borderCol = isHit ? '#2ea043' : '#30363d';
    const bgCol = isHit ? 'rgba(46, 160, 67, 0.12)' : 'rgba(255, 255, 255, 0.02)';
    
    const cCard = document.createElement('div');
    cCard.className = 'glassmorphism';
    cCard.style.cssText = `min-width: 220px; max-width: 220px; border: 2px solid ${borderCol}; border-radius: 8px; padding: 0.8rem; background: ${bgCol};`;
    cCard.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
        <span style="font-size: 0.8rem; font-weight: bold; color: ${isHit ? '#3fb950' : '#8b949e'};">Rank #${cand.rank}</span>
        <span class="pill-${isHit ? 'winner' : 'neutral'}" style="font-size: 0.65rem;">${isHit ? 'TRUE MATCH' : 'DISTRACTOR'}</span>
      </div>
      <div style="font-weight: 500; font-size: 0.85rem; margin-bottom: 0.2rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${cand.candidate_patch_id}</div>
      <div style="font-size: 0.75rem; color: #8b949e; margin-bottom: 0.5rem;">Dist: ${cand.ground_distance_m}m</div>
      <div style="background: #000; border-radius: 4px; height: 140px; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid #30363d;">
        <span style="font-size: 0.75rem; color: #8b949e;">Candidate [${cand.sensor}]</span>
      </div>
      <div style="margin-top: 0.6rem; font-size: 0.75rem; display: flex; justify-content: space-between;">
        <span style="color: #8b949e;">Cosine Sim:</span>
        <strong style="color: ${isHit ? '#3fb950' : '#c9d1d9'};">${cand.cosine_similarity.toFixed(4)}</strong>
      </div>
    `;
    container.appendChild(cCard);
  });
}

function populatePOC5Figures(data) {
  const figs = data.figures || {};
  const map = {
    poc5FigArch: figs.two_tower_architecture,
    poc5FigGrid: figs.retrieval_ranking_grid,
    poc5FigClusters: figs.embedding_clusters,
    poc5FigRecall: figs.recall_at_k_curve,
    poc5FigDist: figs.similarity_distribution,
  };

  const t = Date.now();
  for (const [id, src] of Object.entries(map)) {
    const el = document.getElementById(id);
    if (el && src) {
      el.src = `${src}?t=${t}`;
    }
  }
}


