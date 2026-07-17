function getCategorySlug() {
  const params = new URLSearchParams(window.location.search);

  return (
    params.get("category") ||
    "camping"
  ).toLowerCase();
}


function productMatchesCategory(product, slug) {
  return (
    product.category || ""
  ).toLowerCase() === slug;
}


function getCategoryInfo(slug) {
  return {
    title: translateUi(
      `categories.${slug}.title`,
      translateUi(
        "category.default_title",
        "Category"
      )
    ),
    description: translateUi(
      `categories.${slug}.description`,
      translateUi(
        "category.default_description",
        "Explore practical product ideas selected for everyday use."
      )
    ),
  };
}


function renderCategoryProducts(products, grid) {
  // CATEGORY_VERIFIED_AMAZON_V4
  grid.innerHTML = products.map(product => {
    const amazonUrl = getVerifiedAmazonUrl(product);

    return `
      <article class="product-card">
        <a
          class="product-card-media-link"
          href="${buildProductUrl(product.id)}"
        >
          <div class="product-image-wrap">
            <img
              src="/${product.image || "assets/placeholder.svg"}"
              alt="${product.alt_text || product.title}"
              loading="lazy"
            >
            <span class="ai-visual-badge">${translateUi(
              "common.ai_visual",
              "AI Visual"
            )}</span>
          </div>
        </a>

        <div class="product-card-body">
          <span class="category-tag">${product.category || ""}</span>

          <h3>
            <a href="${buildProductUrl(product.id)}">${product.title}</a>
          </h3>

          <p>${product.short_description || ""}</p>

          <div class="product-card-actions">
            ${renderAmazonButton(
              product,
              "button category-amazon-button"
            )}
            <span class="ad-badge">${translateUi(
              "common.advertisement",
              "#Ad"
            )}</span>
          </div>
        </div>
      </article>
    `;
  }).join("");
}

async function loadCategoryPage() {
  const slug = getCategorySlug();
  const grid = document.getElementById("product-grid");

  try {
    await Promise.all([
      loadConfig(),
      loadUiTranslations(),
    ]);

    const info = getCategoryInfo(slug);

    document.title =
      `${info.title} | Daily Deal Finder`;

    const metaDescription = document.querySelector(
      'meta[name="description"]'
    );

    if (metaDescription) {
      metaDescription.content = info.description;
    }

    const titleElement = document.getElementById(
      "category-title"
    );

    const descriptionElement = document.getElementById(
      "category-description"
    );

    if (titleElement) {
      titleElement.textContent = info.title;
    }

    if (descriptionElement) {
      descriptionElement.textContent = info.description;
    }

    const products = await loadProducts();

    const filtered = products.filter(product =>
      product.active !== false &&
      Boolean(getVerifiedAmazonUrl(product)) &&
      productMatchesCategory(product, slug)
    );

    if (!filtered.length) {
      grid.innerHTML = `
        <div class="empty-state">
          <h2>${translateUi(
            "category.coming_soon_title",
            "Recommendations for this category are coming soon."
          )}</h2>

          <p>${translateUi(
            "category.coming_soon_description",
            "We are preparing carefully selected product ideas for this category."
          )}</p>
        </div>
      `;

      return;
    }

    renderCategoryProducts(filtered, grid);
  } catch (error) {
    console.error("Category page load failed", error);

    grid.innerHTML = `
      <div class="empty-state">
        <h2>${translateUi(
          "category.load_error_title",
          "Products could not be loaded."
        )}</h2>

        <p>${translateUi(
          "category.load_error_description",
          "Please try again later."
        )}</p>
      </div>
    `;
  }
}


loadCategoryPage();
