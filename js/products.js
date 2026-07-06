/**
 * Daily Deal Finder — Products Engine
 * Config & Data loaded via fetch(). Affiliate link auto-generated.
 */

let CONFIG = {};
let PRODUCTS = [];

async function loadConfig() {
  try {
    CONFIG = await fetch('/data/config.json').then(r => r.json());
    document.documentElement.lang = CONFIG.site?.locale || 'de-DE';
  } catch (e) {
    console.warn('Config load failed', e);
  }
}

async function loadProducts() {
  try {
    const data = await fetch('/data/products.json').then(r => r.json());
    PRODUCTS = data.products || [];
    return PRODUCTS;
  } catch (e) {
    console.warn('Products load failed', e);
    return [];
  }
}

function buildAmazonUrl(asin) {
  const tag = CONFIG.affiliate?.amazon_associate_tag || '';
  const domain = CONFIG.site?.amazon_domain || 'amazon.de';
  const base = `https://www.${domain}/dp/${asin}`;
  return tag ? `${base}?tag=${tag}` : base;
}

// ========== ANA SƏHİFƏ ==========

function renderProductGrid(products, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!products.length) {
    container.innerHTML = '<p class="empty">Keine Produkte gefunden. Bald verfügbar!</p>';
    return;
  }

  container.innerHTML = products.map(p => {
    const imgHtml = p.image 
      ? `<img src="/${p.image}" alt="${p.title}" loading="lazy">`
      : `<div class="product-placeholder" aria-label="${p.title}">${p.title}</div>`;
    return `
    <article class="product-card">
      <a href="/product.html?id=${p.id}">
        ${imgHtml}
      </a>
      <div class="info">
        <span class="category-tag">${p.category || ''}</span>
        <h3><a href="/product.html?id=${p.id}">${p.title}</a></h3>
        <p>${p.short_description || ''}</p>
        <a href="${buildAmazonUrl(p.amazon_asin)}" target="_blank" rel="nofollow sponsored noopener" class="button">${p.button_text || 'Auf Amazon ansehen'}</a>
        <span class="ad-badge">#Anzeige</span>
      </div>
    </article>
  `}).join('');
}

async function initHomePage() {
  await loadConfig();
  const products = await loadProducts();
  const active = products.filter(p => p.active !== false && p.featured);
  renderProductGrid(active, 'product-grid');
}

// ========== MƏHSUL SƏHİFƏSİ ==========

function renderProductPage(product) {
  if (!product) {
    document.getElementById('product-page').innerHTML = '<p>Produkt nicht gefunden.</p>';
    return;
  }

  // Meta update
  document.title = product.seo_title || product.title;
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) metaDesc.content = product.seo_description || product.short_description;
  const canonical = document.querySelector('link[rel="canonical"]');
  if (canonical) canonical.href = `https://dailydealfinder.netlify.app/product.html?id=${product.id}`;

  // OG update
  document.querySelector('meta[property="og:title"]')?.setAttribute('content', product.pinterest_title || product.title);
  document.querySelector('meta[property="og:description"]')?.setAttribute('content', product.pinterest_description || product.short_description);
  document.querySelector('meta[property="og:image"]')?.setAttribute('content', product.image ? `https://dailydealfinder.netlify.app/${product.image}` : 'https://dailydealfinder.netlify.app/assets/logo.png');
  document.querySelector('meta[property="og:url"]')?.setAttribute('content', `https://dailydealfinder.netlify.app/product.html?id=${product.id}`);
  document.querySelector('meta[name="twitter:image"]')?.setAttribute('content', product.image ? `https://dailydealfinder.netlify.app/${product.image}` : 'https://dailydealfinder.netlify.app/assets/logo.png');

  // Page render
  document.getElementById('product-page').innerHTML = `
    <div class="product-hero">
      ${product.image ? `<img src="/${product.image}" alt="${product.title}" class="product-main-image">` : `<div class="product-placeholder product-placeholder-large">${product.title}</div>`}
      <div class="product-hero-info">
        <span class="category-tag">${product.category || ''}</span>
        <h1>${product.title}</h1>
        ${product.brand ? `<p class="brand">Marke: ${product.brand}</p>` : ''}
        <div class="product-description">
          <p>${product.long_description || product.short_description}</p>
        </div>
        ${product.features?.length ? `
        <ul class="features">
          ${product.features.map(f => `<li>${f}</li>`).join('')}
        </ul>` : ''}
        <a href="${buildAmazonUrl(product.amazon_asin)}" target="_blank" rel="nofollow sponsored noopener" class="button cta">${product.button_text || 'Auf Amazon ansehen'}</a>
        <p class="price-note">*Preise können variieren. Aktuellen Preis auf Amazon.de prüfen.</p>
        <p class="disclosure">Als Amazon Associate verdienen wir an qualifizierten Käufen.</p>
      </div>
    </div>
  `;
}

async function initProductPage() {
  await loadConfig();
  const products = await loadProducts();
  const id = new URLSearchParams(window.location.search).get('id');
  const product = products.find(p => p.id === id);
  renderProductPage(product);
}
