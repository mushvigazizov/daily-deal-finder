from pathlib import Path

CATEGORY_JS = r"""const CATEGORY_META = {
  camping: { icon: '🏕️', title: 'Camping & Outdoor', description: 'Outdoor essentials, tents, hiking and adventure gear.' },
  home: { icon: '🏠', title: 'Home', description: 'Functional home essentials, organizers, and everyday helpers.' },
  kitchen: { icon: '🍳', title: 'Kitchen', description: 'Useful kitchen tools, smart accessories, and cooking inspiration.' },
  tech: { icon: '💻', title: 'Tech', description: 'Gadgets, accessories, and simple technology for daily life.' },
  beauty: { icon: '💄', title: 'Beauty', description: 'Beauty finds, self-care ideas, and practical lifestyle products.' },
  outdoor: { icon: '🌿', title: 'Outdoor', description: 'Camping, travel, garden, and outdoor product ideas.' },
  pets: { icon: '🐶', title: 'Pets', description: 'Helpful product inspiration for pets and pet owners.' },
  gifts: { icon: '🎁', title: 'Gifts', description: 'Seasonal gift guides and simple ideas for different occasions.' }
};

function renderCategoryProductCard(product) {
  const imageHtml = product.image
    ? `<img src="/${product.image}" alt="${product.title}" loading="lazy">`
    : `<div class="product-placeholder" aria-label="${product.title}">${product.title}</div>`;

  return `
    <article class="product-card">
      <a href="/product.html?id=${product.id}">${imageHtml}</a>
      <div class="info">
        <span class="category-tag">${product.category || ''}</span>
        <h3><a href="/product.html?id=${product.id}">${product.title}</a></h3>
        <p>${product.short_description || ''}</p>
        <a href="${buildAmazonUrl(product.amazon_asin)}" target="_blank" rel="nofollow sponsored noopener" class="button">${product.button_text || 'Auf Amazon ansehen'}</a>
        <span class="ad-badge">#Anzeige</span>
      </div>
    </article>
  `;
}

async function initCategoryPage() {
  await loadConfig();
  const products = await loadProducts();

  const params = new URLSearchParams(window.location.search);
  const categoryKey = (params.get('category') || 'camping').toLowerCase();
  const meta = CATEGORY_META[categoryKey] || CATEGORY_META.camping;

  const heading = document.getElementById('category-heading');
  const subtitle = document.getElementById('category-subtitle');
  const grid = document.getElementById('category-grid');

  const filtered = products.filter(product =>
    product.active !== false &&
    (product.category || '').toLowerCase() === categoryKey
  );

  if (heading) heading.textContent = `${meta.icon} ${meta.title}`;
  if (subtitle) subtitle.textContent = meta.description;
  document.title = `${meta.title} – Daily Deal Finder`;

  if (!grid) return;

  if (!filtered.length) {
    grid.innerHTML = `
      <div class="empty category-empty">
        <h2>${meta.icon} ${meta.title}</h2>
        <p>Products are being added to this category.</p>
        <p>New recommendations will appear here soon.</p>
        <a class="button cta" href="/">Back to homepage</a>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(renderCategoryProductCard).join('');
}
"""

def main():
    Path("js").mkdir(exist_ok=True)
    Path("js/category.js").write_text(CATEGORY_JS, encoding="utf-8")
    print("Generated js/category.js")

if __name__ == "__main__":
    main()
