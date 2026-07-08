const CATEGORY_INFO = {
  camping: {
    title: "Camping & Outdoor",
    description: "Outdoor essentials, tents, hiking and adventure gear."
  },
  home: {
    title: "Home",
    description: "Functional home essentials, organizers, and everyday helpers."
  },
  kitchen: {
    title: "Kitchen",
    description: "Useful kitchen tools, smart accessories, and cooking inspiration."
  },
  tech: {
    title: "Tech",
    description: "Gadgets, accessories, and simple technology for daily life."
  },
  beauty: {
    title: "Beauty",
    description: "Beauty finds, self-care ideas, and practical lifestyle products."
  },
  outdoor: {
    title: "Outdoor",
    description: "Camping, travel, garden, and outdoor product ideas."
  },
  pets: {
    title: "Pets",
    description: "Helpful product inspiration for pets and pet owners."
  },
  gifts: {
    title: "Gifts",
    description: "Seasonal gift guides and simple ideas for different occasions."
  }
};

function getCategorySlug() {
  const params = new URLSearchParams(window.location.search);
  return (params.get("category") || "camping").toLowerCase();
}

function productMatchesCategory(product, slug) {
  const text = [
    product.category,
    product.title,
    product.short_description,
    product.long_description,
    product.seo_title,
    product.seo_description
  ].join(" ").toLowerCase();

  if (slug === "camping" || slug === "outdoor") {
    return text.includes("camping") || text.includes("outdoor") || text.includes("zelt") || text.includes("wander");
  }

  return text.includes(slug);
}

async function loadCategoryPage() {
  const slug = getCategorySlug();
  const info = CATEGORY_INFO[slug] || CATEGORY_INFO.camping;

  document.title = `${info.title} | Daily Deal Finder`;
  document.getElementById("category-title").textContent = info.title;
  document.getElementById("category-description").textContent = info.description;

  const grid = document.getElementById("product-grid");

  try {
    const response = await fetch("/data/products.json?v=3");
    const data = await response.json();
    const products = data.products || data;

    const filtered = products.filter(product => productMatchesCategory(product, slug));

    if (!filtered.length) {
      grid.innerHTML = `
        <div class="empty-state">
          <h2>More ${info.title} ideas are coming soon.</h2>
          <p>We are expanding this category with carefully selected product inspiration.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = filtered.map(product => `
      <article class="product-card">
        <a href="/product.html?id=${encodeURIComponent(product.id)}">
          <img src="/${product.image || "assets/placeholder.svg"}" alt="${product.title}">
          <div class="product-card-body">
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
