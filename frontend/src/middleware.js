import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware((context, next) => {
  const url = new URL(context.url);
  const pathParts = url.pathname.split('/').filter(Boolean);

  const validLocales = ['zh', 'en'];
  const hasLocale = pathParts.length > 0 && validLocales.includes(pathParts[0]);

  if (!hasLocale && url.pathname !== '/' && !url.pathname.startsWith('/api/') && !url.pathname.startsWith('/admin') && !url.pathname.startsWith('/uploads') && !url.pathname.startsWith('/static') && !url.pathname.startsWith('/health')) {
    return new Response(null, {
      status: 302,
      headers: { 'Location': `/zh${url.pathname}${url.search}` },
    });
  }

  if (url.pathname === '/') {
    const langCookie = context.cookies.get('lang');
    const redirectLocale = ['zh', 'en'].includes(langCookie?.value || '') ? langCookie.value : 'zh';
    return new Response(null, {
      status: 302,
      headers: { 'Location': `/${redirectLocale}/` },
    });
  }

  return next();
});
