const CATEGORY_INFO = {
  camping: {
    title: "Camping & Outdoor",
    description: "Outdoor essentials, tents, hiking and adventure gear."
  },
  home: {
    title: "Home & Garden",
    description: "Functional home essentials, organizers, and everyday helpers."
  },
  kitchen: {
    title: "Kitchen & Dining",
    description: "Useful kitchen tools, smart accessories, and cooking inspiration."
  },
  electronics: {
    title: "Electronics & Gadgets",
    description: "Electronics, gadgets, accessories, and useful tech finds."
  },
  fitness: {
    title: "Fitness & Sports",
    description: "Fitness gear, sports accessories, and active lifestyle products."
  },
  travel: {
    title: "Travel Gear",
    description: "Travel gear, packing helpers, and practical trip accessories."
  },
  pets: {
    title: "Pet Supplies",
    description: "Helpful product inspiration for pets and pet owners."
  },
  lifestyle: {
    title: "Lifestyle",
    description: "Lifestyle finds, useful everyday ideas, and smart inspiration."
  }
};

function getCategorySlug() {
  const params = new URLSearchParams(window.location.search);
  return (params.get("category") || "camping").toLowerCase();
}

function productMatchesCategory(product, slug) {
  return (product.category || "").toLowerCase() === slug;
}

async function loadCategoryPage() {
  const slug = getCategorySlug();
  const info = CATEGORY_INFO[slug] || CATEGORY_INFO.camping;

  document.title = `${info.title} | Daily Deal Finder`;

  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) metaDesc.content = info.description;

  const titleEl = document.getElementById("category-title");
  const descEl = document.getElementById("category-description");
  const grid = document.getElementById("product-grid");

  if (titleEl) titleEl.textContent = info.title;
  if (descEl) descEl.textContent = info.description;

  try {
    const response = await fetch("/data/products.json?v=5");
    const data = await response.json();
    const products = data.products || data;

    const filtered = products.filter(product =>
      product.active !== false && productMatchesCategory(product, slug)
    );

    if (!filtered.length) {
      grid.innerHTML = `
        <div class="empty-state">
          <h2>${info.title} recommendations are coming soon.</h2>
          <p>We are preparing carefully selected product ideas for this category. No unrelated products are shown here.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = filtered.map(product => `
      <article class="product-card">
        <a href="/product.html?id=${encodeURIComponent(product.id)}">
          <div class="product-image-wrap">
            <img src="/${product.image || "assets/placeholder.svg"}" alt="${product.title}" loading="lazy">
            <span class="ai-visual-badge">AI Visual</span>
          </div>
          <div class="product-card-body">
            <span class="category-tag">${product.category || ""}</span>
            <h3>${product.title}</h3>
            <p>${product.short_description || ""}</p>
          </div>
        </a>
      </article>
    `).join("");
  } catch (error) {
    grid.innerHTML = `
      <div class="empty-state">
        <h2>Products could not be loaded.</h2>
        <p>Please try again later.</p>
      </div>
    `;
  }
}

loadCategoryPage();
