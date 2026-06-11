const API_BASE = import.meta.env.BUILD_API || 'http://localhost:8000';

export async function fetchProducts() {
  try {
    const res = await fetch(`${API_BASE}/api/products`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchProductById(id) {
  try {
    const res = await fetch(`${API_BASE}/api/products/${id}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchProductBySlug(slug) {
  try {
    const products = await fetchProducts();
    return products.find(p => p.slug === slug) || null;
  } catch {
    return null;
  }
}

export async function fetchNews() {
  try {
    const res = await fetch(`${API_BASE}/api/news`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchNewsById(id) {
  try {
    const res = await fetch(`${API_BASE}/api/news/${id}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchNewsBySlug(slug) {
  try {
    const news = await fetchNews();
    return news.find(n => n.slug === slug) || null;
  } catch {
    return null;
  }
}

export async function fetchSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchSiteConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/site-config`);
    if (!res.ok) return {};
    return await res.json();
  } catch {
    return {};
  }
}

export async function fetchAbout() {
  try {
    const res = await fetch(`${API_BASE}/api/about`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchContact() {
  try {
    const res = await fetch(`${API_BASE}/api/contact`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function submitContact(data) {
  try {
    const res = await fetch(`${API_BASE}/api/submissions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return { ok: res.ok, data: res.ok ? await res.json() : null };
  } catch {
    return { ok: false, data: null };
  }
}

export async function trackPageview(page, source, ua) {
  try {
    await fetch(`${API_BASE}/api/analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page, source, user_agent: ua }),
    });
  } catch {
    // silent fail
  }
}

export function getSettingValue(settings, key, defaultValue) {
  const setting = settings?.find(s => s.key === key);
  return setting?.value ?? defaultValue;
}
