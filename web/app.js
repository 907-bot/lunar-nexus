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

function initPOC4Studio() {
  const btnRun = document.getElementById('btnRunPOC4Experiment');
  if (!btnRun) return;

  btnRun.addEventListener('click', runPOC4FullPipeline);

  // Load existing results if available
  loadPOC4Results();
}

async function loadPOC4Results() {
  try {
    const res = await fetch('/api/poc4/results');
    if (res.ok) {
      const data = await res.json();
      updatePOC4UI(data);
    }
  } catch (e) {
    console.log('POC-4 cached results not available yet.');
  }
}

async function runPOC4FullPipeline() {
  const btnRun = document.getElementById('btnRunPOC4Experiment');
  const progressCard = document.getElementById('poc4ProgressCard');
  const progressBar = document.getElementById('poc4ProgressBar');
  const stepLabel = document.getElementById('poc4CurrentStep');
  const stepBadges = document.querySelectorAll('#poc4StepsFlow .step-badge');

  btnRun.disabled = true;
  btnRun.innerHTML = `
    <span class="spinner" style="width: 14px; height: 14px; border-width: 2px; display: inline-block;"></span>
    Running Experiment Matrix...
  `;
  progressCard.style.display = 'flex';

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
      stepLabel.innerText = s.name;
      progressBar.style.width = `${s.percent}%`;
      
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

  try {
    const res = await fetch('/api/poc4/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_product_id: 'ch2_ohr_ncp_20260103t1005176450_d_img_d18',
        reference_product_id: 'SYNTHETIC_LROC_CANDIDATE_P850S0250',
        fast_mode: false
      })
    });

    clearInterval(progressTimer);

    if (res.ok) {
      const data = await res.json();
      progressBar.style.width = '100%';
      stepLabel.innerText = 'Experiment Completed Successfully!';
      stepBadges.forEach(b => b.className = 'step-badge completed');
      
      setTimeout(() => {
        updatePOC4UI(data);
        refreshFigureImages();
        progressCard.style.display = 'none';
      }, 800);
    } else {
      const err = await res.text();
      alert('POC-4 Experiment run error: ' + err);
    }
  } catch (err) {
    clearInterval(progressTimer);
    console.error('POC-4 execution failure:', err);
    alert('Failed to connect to POC-4 experiment service: ' + err);
  } finally {
    btnRun.disabled = false;
    btnRun.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
      RUN POC-4 EXPERIMENT
    `;
  }
}

function refreshFigureImages() {
  const t = Date.now();
  document.querySelectorAll('.gallery-img-box img').forEach(img => {
    const base = img.src.split('?')[0];
    img.src = `${base}?t=${t}`;
  });
}

function updatePOC4UI(data) {
  if (!data) return;

  // Update Provenance label
  if (data.metadata?.data_provenance) {
    const provLabel = document.getElementById('poc4ProvenanceLabel');
    if (provLabel) provLabel.innerText = data.metadata.data_provenance;
  }

  // Update Scorecards
  if (data.summary) {
    const s = data.summary;
    const bestRep = s.best_representation || 'MULTI-SCALE + ILLUMINATION-AWARE';
    const repData = s.representation_metrics ? s.representation_metrics[bestRep] : null;

    const elBestRep = document.getElementById('poc4BestRep');
    if (elBestRep) elBestRep.innerText = bestRep;

    if (repData) {
      const elSuccess = document.getElementById('poc4SuccessRate');
      if (elSuccess) elSuccess.innerText = `${(repData.success_rate * 100).toFixed(1)}%`;

      const elInlier = document.getElementById('poc4InlierRatio');
      if (elInlier) elInlier.innerText = `${(repData.mean_inlier_ratio * 100).toFixed(1)}%`;

      const elRecall1 = document.getElementById('poc4Recall1');
      if (elRecall1) elRecall1.innerText = `${(repData.mean_recall_1 * 100).toFixed(1)}%`;

      const elRmse = document.getElementById('poc4Rmse');
      if (elRmse) elRmse.innerText = `${repData.mean_rmse.toFixed(2)} px`;
    }
  }

  // Populate Baseline Comparison Table
  if (data.summary?.representation_metrics) {
    const tbody = document.getElementById('poc4ComparisonTableBody');
    if (tbody) {
      tbody.innerHTML = '';
      const reps = data.summary.representation_metrics;
      for (const [repName, m] of Object.entries(reps)) {
        const tr = document.createElement('tr');
        const isBest = repName.includes('MULTI-SCALE') && repName.includes('ILLUMINATION');
        if (isBest) tr.className = 'highlight-row';

        let pillClass = 'pill-fail';
        let pillText = 'Baseline';
        if (m.success_rate >= 0.7) {
          pillClass = isBest ? 'pill-winner' : 'pill-pass';
          pillText = isBest ? '★ BEST PERFORMER' : 'High Robustness';
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
          <td>${m.mean_rmse.toFixed(2)} px</td>
          <td><span class="${pillClass}">${pillText}</span></td>
        `;
        tbody.appendChild(tr);
      }
    }
  }

  // Populate Ablation Table
  if (data.ablation) {
    const tbody = document.getElementById('poc4AblationTableBody');
    if (tbody && Array.isArray(data.ablation)) {
      tbody.innerHTML = '';
      data.ablation.forEach(row => {
        const tr = document.createElement('tr');
        const isPass = row.success;
        const isBest = row.config_name.includes('ILLUMINATION-AWARE') && row.scale_harmonized;
        if (isBest) tr.className = 'highlight-row';

        tr.innerHTML = `
          <td>${row.config_name}</td>
          <td>${row.scale_harmonized ? 'Yes' : 'No'}</td>
          <td>${(row.inlier_ratio * 100).toFixed(1)}%</td>
          <td>${row.rmse < 900 ? row.rmse.toFixed(2) + ' px' : '999.00 px'}</td>
          <td><span class="${isBest ? 'pill-winner' : (isPass ? 'pill-pass' : 'pill-fail')}">${isPass ? 'PASS' : 'FAIL'}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }
  }
}

// ==========================================================================
// POC 5: Multimodal AI Correspondence & Retrieval Studio
// ==========================================================================
function initPOC5Studio() {
  const btnRun = document.getElementById('btnRunPOC5Experiment');
  if (!btnRun) return;

  btnRun.addEventListener('click', runPOC5FullPipeline);

  // Load existing results if available
  loadPOC5Results();
}

async function loadPOC5Results() {
  try {
    const res = await fetch('/api/poc5/demo');
    if (res.ok) {
      const data = await res.json();
      updatePOC5UI(data);
    }
  } catch (e) {
    console.log('POC-5 cached results not available yet.');
  }
}

async function runPOC5FullPipeline() {
  const btnRun = document.getElementById('btnRunPOC5Experiment');
  const progressCard = document.getElementById('poc5ProgressCard');
  const progressBar = document.getElementById('poc5ProgressBar');
  const stepLabel = document.getElementById('poc5CurrentStep');
  const stepBadges = document.querySelectorAll('#poc5StepsFlow .step-badge');

  btnRun.disabled = true;
  btnRun.innerHTML = `
    <span class="spinner" style="width: 14px; height: 14px; border-width: 2px; display: inline-block;"></span>
    Retrieving Cross-Modal Correspondences...
  `;
  progressCard.style.display = 'flex';

  const steps = [
    { name: '1. Ingesting Cross-Sensor Common-Ground Patches...', percent: 16, index: 0 },
    { name: '2. Initializing Multimodal Representation Encoders...', percent: 33, index: 1 },
    { name: '3. Extracting 128-D Dense L2-Normalized Embeddings...', percent: 50, index: 2 },
    { name: '4. Computing Cross-Modal Cosine Similarity Matrix...', percent: 66, index: 3 },
    { name: '5. Ranking Top-K Nearest Neighbor Candidates...', percent: 83, index: 4 },
    { name: '6. Validating Geospatial Relations & Handover to POC-6...', percent: 100, index: 5 }
  ];

  let currentStepIdx = 0;
  const progressTimer = setInterval(() => {
    if (currentStepIdx < steps.length) {
      const s = steps[currentStepIdx];
      stepLabel.innerText = s.name;
      progressBar.style.width = `${s.percent}%`;
      
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
  }, 400);

  try {
    const res = await fetch('/api/poc5/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        num_pairs: 12,
        top_k: 5,
      })
    });

    clearInterval(progressTimer);

    if (res.ok) {
      const data = await res.json();
      progressBar.style.width = '100%';
      stepLabel.innerText = 'Cross-Modal Retrieval Complete!';
      stepBadges.forEach(b => b.className = 'step-badge completed');
      
      setTimeout(() => {
        updatePOC5UI(data);
        refreshPOC5FigureImages();
        progressCard.style.display = 'none';
      }, 700);
    } else {
      const err = await res.text();
      alert('POC-5 Retrieval error: ' + err);
    }
  } catch (err) {
    clearInterval(progressTimer);
    console.error('POC-5 execution failure:', err);
    alert('Failed to execute POC-5 retrieval service: ' + err);
  } finally {
    btnRun.disabled = false;
    btnRun.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
      RUN POC-5 RETRIEVAL
    `;
  }
}

function refreshPOC5FigureImages() {
  const t = Date.now();
  document.querySelectorAll('#tab-poc5 .gallery-img-box img, #poc5QueryImgPreview').forEach(img => {
    const base = img.src.split('?')[0];
    img.src = `${base}?t=${t}`;
  });
}

function updatePOC5UI(data) {
  if (!data) return;

  // Update Provenance label
  const prov = data.metadata?.data_provenance || data.provenance;
  if (prov) {
    const provLabel = document.getElementById('poc5ProvenanceLabel');
    if (provLabel) provLabel.innerText = prov;
  }

  // Update Scorecards
  const sm = data.summary_metrics || data;
  if (sm) {
    const elR1 = document.getElementById('poc5Recall1');
    if (elR1 && sm.recall_at_1 !== undefined) {
      elR1.innerText = typeof sm.recall_at_1 === 'number' ? `${(sm.recall_at_1 * 100).toFixed(1)}%` : sm.recall_at_1;
    }

    const elR3 = document.getElementById('poc5Recall3');
    if (elR3 && sm.recall_at_3 !== undefined) {
      elR3.innerText = typeof sm.recall_at_3 === 'number' ? `${(sm.recall_at_3 * 100).toFixed(1)}%` : sm.recall_at_3;
    }

    const elR5 = document.getElementById('poc5Recall5');
    if (elR5 && sm.recall_at_5 !== undefined) {
      elR5.innerText = typeof sm.recall_at_5 === 'number' ? `${(sm.recall_at_5 * 100).toFixed(1)}%` : sm.recall_at_5;
    }

    const elR10 = document.getElementById('poc5Recall10');
    if (elR10 && sm.recall_at_10 !== undefined) {
      elR10.innerText = typeof sm.recall_at_10 === 'number' ? `${(sm.recall_at_10 * 100).toFixed(1)}%` : sm.recall_at_10;
    }

    const elMrr = document.getElementById('poc5Mrr');
    if (elMrr && sm.mean_reciprocal_rank !== undefined) {
      elMrr.innerText = typeof sm.mean_reciprocal_rank === 'number' ? sm.mean_reciprocal_rank.toFixed(3) : sm.mean_reciprocal_rank;
    }

    const elMeanSim = document.getElementById('poc5MeanSim');
    if (elMeanSim && sm.mean_similarity_score !== undefined) {
      elMeanSim.innerText = sm.mean_similarity_score.toFixed(3);
    }
  }

  // Update Candidate List for first query
  const retrievals = data.retrieval_results;
  if (retrievals && Object.keys(retrievals).length > 0) {
    const firstQ = Object.keys(retrievals)[0];
    const matches = retrievals[firstQ];

    const qLabel = document.getElementById('poc5ActiveQueryId');
    if (qLabel) qLabel.innerText = firstQ;

    const candContainer = document.getElementById('poc5CandidatesList');
    if (candContainer && Array.isArray(matches)) {
      candContainer.innerHTML = '';
      matches.forEach(m => {
        const card = document.createElement('div');
        const isGt = m.is_ground_truth;
        card.className = `candidate-rank-card glassmorphism ${isGt ? 'winner-card' : ''}`;
        
        let pillClass = 'pill-neutral';
        let pillText = m.geographic_relation || 'CANDIDATE';
        if (isGt) {
          pillClass = 'pill-winner';
          pillText = '★ TRUE GEOGRAPHIC MATCH';
        } else if (m.geographic_relation === 'OVERLAPPING') {
          pillClass = 'pill-pass';
        }

        const simPercent = Math.max(0, Math.min(100, m.similarity_score * 100));

        card.innerHTML = `
          <div class="cand-rank-badge">#${m.rank}</div>
          <div class="cand-info-col">
            <div class="cand-title-row">
              <strong class="val-code">${m.candidate_patch_id}</strong>
              <span class="${pillClass}">${pillText}</span>
            </div>
            <div class="cand-meta-row">
              <span>${m.candidate_sensor} (${m.candidate_gsd}m GSD)</span>
              <span>Spatial Rel: <strong>${m.geographic_relation}</strong></span>
            </div>
            <div class="cand-sim-bar-track">
              <div class="cand-sim-bar-fill" style="width: ${simPercent}%; ${isGt ? 'background: linear-gradient(90deg, #a29bfe, #2ed573);' : ''}"></div>
            </div>
          </div>
          <div class="cand-score-col">
            <div class="cand-score-val">${m.similarity_score.toFixed(3)}</div>
            <div class="cand-score-lbl">Cosine Sim</div>
          </div>
        `;
        candContainer.appendChild(card);
      });
    }
  }

  // Update Ablation Table
  if (data.ablation_comparison && Array.isArray(data.ablation_comparison)) {
    const tbody = document.getElementById('poc5AblationTableBody');
    if (tbody) {
      tbody.innerHTML = '';
      data.ablation_comparison.forEach(row => {
        const tr = document.createElement('tr');
        const isAi = row.representation.includes('AI');
        if (isAi) tr.className = 'highlight-row';

        tr.innerHTML = `
          <td><strong>${row.representation}</strong></td>
          <td>${row.embedding_dim}-D</td>
          <td>${typeof row.recall_at_1 === 'number' ? (row.recall_at_1 * 100).toFixed(1) + '%' : row.recall_at_1}</td>
          <td>${typeof row.recall_at_5 === 'number' ? (row.recall_at_5 * 100).toFixed(1) + '%' : row.recall_at_5}</td>
          <td>${typeof row.mrr === 'number' ? row.mrr.toFixed(3) : row.mrr}</td>
          <td><span class="${isAi ? 'pill-winner' : 'pill-neutral'}">${isAi ? '★ SUPERIOR RECALL' : 'Baseline'}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }
  }
}


