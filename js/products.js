/**
 * Daily Deal Finder — Products Engine
 * Config & Data loaded via fetch(). Affiliate link auto-generated.
 */

let CONFIG = {};
let PRODUCTS = [];

const SUPPORTED_PRODUCT_LANGUAGES = ["de", "en"];
const DEFAULT_PRODUCT_LANGUAGE = "de";

let UI_TRANSLATIONS = {};


async function loadUiTranslations() {
  const language = getProductLanguage();

  try {
    const response = await fetch(
      `/data/i18n/${language}.json`
    );

    if (!response.ok) {
      throw new Error(
        `UI translation request failed: ${response.status}`
      );
    }

    UI_TRANSLATIONS = await response.json();
  } catch (error) {
    console.warn("UI translations load failed", error);
    UI_TRANSLATIONS = {};
  }

  return UI_TRANSLATIONS;
}


function translateUi(key, fallback = "") {
  const value = key.split(".").reduce(
    (current, part) => {
      if (
        current &&
        Object.prototype.hasOwnProperty.call(current, part)
      ) {
        return current[part];
      }

      return null;
    },
    UI_TRANSLATIONS
  );

  return typeof value === "string" ? value : fallback;
}


function getProductLanguage() {
  const params = new URLSearchParams(window.location.search);
  const urlLanguage = params.get("lang");

  if (SUPPORTED_PRODUCT_LANGUAGES.includes(urlLanguage)) {
    return urlLanguage;
  }

  const savedLanguage = localStorage.getItem("ddf_language");

  if (SUPPORTED_PRODUCT_LANGUAGES.includes(savedLanguage)) {
    return savedLanguage;
  }

  return DEFAULT_PRODUCT_LANGUAGE;
}


function buildLocalizedUrl(path, extraParams = {}) {
  const url = new URL(path, window.location.origin);
  const language = getProductLanguage();

  url.searchParams.set("lang", language);

  Object.entries(extraParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  return `${url.pathname}${url.search}`;
}


function buildProductUrl(productId) {
  return buildLocalizedUrl("/product.html", {
    id: productId,
  });
}


async function loadConfig() {
  try {
    CONFIG = await fetch("/data/config.json").then(response => {
      if (!response.ok) {
        throw new Error(`Config request failed: ${response.status}`);
      }

      return response.json();
    });

    document.documentElement.lang = getProductLanguage();
  } catch (error) {
    console.warn("Config load failed", error);
    document.documentElement.lang = getProductLanguage();
  }
}


async function fetchLocalizedProductContent(productId, language) {
  const response = await fetch(
    `/data/content/${encodeURIComponent(productId)}.${language}.json`
  );

  if (!response.ok) {
    throw new Error(
      `Localized content request failed: ${productId}.${language}`
    );
  }

  return response.json();
}


function mergeProductContent(product, localizedContent) {
  if (!localizedContent || typeof localizedContent !== "object") {
    return product;
  }

  return {
    ...product,
    ...localizedContent,
    id: product.id,
    language: localizedContent.language || getProductLanguage(),
    seo_description:
      localizedContent.meta_description ||
      product.seo_description ||
      product.short_description ||
      "",
  };
}


async function localizeProduct(product, language) {
  const fallbackLanguages = [
    language,
    DEFAULT_PRODUCT_LANGUAGE,
  ].filter(
    (item, index, values) =>
      SUPPORTED_PRODUCT_LANGUAGES.includes(item) &&
      values.indexOf(item) === index
  );

  for (const fallbackLanguage of fallbackLanguages) {
    try {
      const localizedContent =
        await fetchLocalizedProductContent(
          product.id,
          fallbackLanguage
        );

      return mergeProductContent(
        product,
        localizedContent
      );
    } catch (error) {
      console.warn(
        `Content fallback failed for ${product.id}.${fallbackLanguage}`,
        error
      );
    }
  }

  return {
    ...product,
    language: DEFAULT_PRODUCT_LANGUAGE,
  };
}


async function loadProducts() {
  try {
    const response = await fetch("/data/products.json");

    if (!response.ok) {
      throw new Error(
        `Products request failed: ${response.status}`
      );
    }

    const data = await response.json();
    const baseProducts = data.products || [];
    const language = getProductLanguage();

    PRODUCTS = await Promise.all(
      baseProducts.map(product =>
        localizeProduct(product, language)
      )
    );

    localStorage.setItem("ddf_language", language);
    document.documentElement.lang = language;

    return PRODUCTS;
  } catch (error) {
    console.warn("Products load failed", error);
    return [];
  }
}

function buildAmazonUrl(asin) {
  if (!asin) return 'https://www.amazon.de/';
  const tag = CONFIG.affiliate?.amazon_associate_tag || '';
  const domain = CONFIG.site?.amazon_domain || 'amazon.de';
  // Search URL format: "s?k=..."
  if (asin.startsWith('s?k=')) {
    const base = `https://www.${domain}/${asin}`;
    return tag ? `${base}&tag=${tag}` : base;
  }
  // ASIN format: "B0XXXXX"
  const base = `https://www.${domain}/dp/${asin}`;
  return tag ? `${base}?tag=${tag}` : base;
}

// ========== ANA SƏHİFƏ ==========

function renderProductGrid(products, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!products.length) {
    container.innerHTML =
      `<p class="empty">${translateUi(
        "common.products_not_found",
        "Keine Produkte gefunden. Bald verfügbar!"
      )}</p>`;
    return;
  }

  container.innerHTML = products.map(p => {
    const imgHtml = p.image 
      ? `<img src="/${p.image}" alt="${p.alt_text || p.title}" loading="lazy">`
      : `<div class="product-placeholder" aria-label="${p.title}">${p.title}</div>`;
    return `
    <article class="product-card">
      <a href="${buildProductUrl(p.id)}">
        <div class="product-image-wrap">
      ${imgHtml}
      <span class="ai-visual-badge">AI Visual</span>
    </div>
      </a>
      <div class="info">
        <span class="category-tag">${p.category || ''}</span>
        <h3><a href="${buildProductUrl(p.id)}">${p.title}</a></h3>
        <p>${p.short_description || ''}</p>
        <a href="${buildAmazonUrl(p.amazon_asin)}" target="_blank" rel="nofollow sponsored noopener" class="button">${p.button_text || 'Auf Amazon ansehen'}</a>
        <span class="ad-badge">#Anzeige</span>
      </div>
    </article>
  `}).join('');
}

async function initHomePage() {
  await Promise.all([
    loadConfig(),
    loadUiTranslations(),
  ]);

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
  if (canonical) {
    canonical.href =
      `https://daily-deal-finder.com${buildProductUrl(product.id)}`;
  }

  // OG update
  document.querySelector('meta[property="og:title"]')?.setAttribute('content', product.pinterest_title || product.title);
  document.querySelector('meta[property="og:description"]')?.setAttribute('content', product.pinterest_description || product.short_description);
  document.querySelector('meta[property="og:image"]')?.setAttribute('content', product.image ? `https://daily-deal-finder.com/${product.image}` : 'https://daily-deal-finder.com/assets/logo.png');
  document.querySelector('meta[property="og:url"]')?.setAttribute(
    'content',
    `https://daily-deal-finder.com${buildProductUrl(product.id)}`
  );
  document.querySelector('meta[name="twitter:image"]')?.setAttribute('content', product.image ? `https://daily-deal-finder.com/${product.image}` : 'https://daily-deal-finder.com/assets/logo.png');

  // Page render
  document.getElementById('product-page').innerHTML = `
    <div class="product-hero">
      <section class="product-media-panel">
        <div class="product-main-image-wrap">
          ${product.image ? `<img src="/${product.image}" alt="${product.alt_text || product.title}" class="product-main-image">` : `<div class="product-placeholder product-placeholder-large">${product.title}</div>`}
          <span class="ai-visual-badge ai-visual-badge-large">AI Visual</span>
        </div>
      </section>

      <section class="product-info-panel">
        <span class="product-kicker">${product.category || 'Empfohlenes Produkt'}</span>
        <h1>${product.title}</h1>
        ${product.brand ? `<p class="product-brand">Marke: ${product.brand}</p>` : ''}

        <div class="product-description">
          <p>${product.long_description || product.short_description || ''}</p>
        </div>

        ${product.features?.length ? `
        <ul class="features">
          ${product.features.map(f => `<li>${f}</li>`).join('')}
        </ul>` : ''}

        <div class="product-trust-row">
          <div class="product-trust-item">Amazon.de</div>
          <div class="product-trust-item">Camping Auswahl</div>
          <div class="product-trust-item">Affiliate Hinweis</div>
        </div>

        <a href="${buildAmazonUrl(product.amazon_asin)}" target="_blank" rel="nofollow sponsored noopener" class="button cta">${product.button_text || 'Auf Amazon ansehen'}</a>

        <p class="price-note">*Preise und Verfügbarkeit können sich ändern. Aktuellen Preis bitte direkt auf Amazon.de prüfen.</p>
        <p class="disclosure">Als Amazon Associate verdienen wir an qualifizierten Käufen.</p>
      </section>
    </div>
  `;
}

async function initProductPage() {
  await Promise.all([
    loadConfig(),
    loadUiTranslations(),
  ]);

  const products = await loadProducts();
  const id = new URLSearchParams(window.location.search).get('id');
  const product = products.find(p => p.id === id);
  renderProductPage(product);
}
