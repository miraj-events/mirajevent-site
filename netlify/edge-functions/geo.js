/*
  Out-of-area visitors (Oct 30, 2026): keeps bots and overseas traffic out of the numbers without blocking anyone.

  Netlify runs this before every page (not images, fonts or scripts). It reads the visitor's country from Netlify's
  geolocation and sets a short-lived cookie, miraj_cc=<two-letter code>. The page's head script reads that cookie:
  outside the US and Canada the site works exactly the same, but GA4, Google Ads, the OpenAI pixel and the Meta Pixel
  don't load and no conversion fires. An inquiry from abroad still reaches Netlify and the email, with Source
  starting "Out of area (XX)", and the ChatGPT-ads server copy sends it validate_only (checked, not recorded).

  Why: in the week of Oct 23-29, 69 of 154 GA4 users were in the Netherlands. Search Console (checked Oct 31) shows
  they come from Google searches for "miraj event(s)" and "miraaj events" in Amsterdam, Rotterdam, Eindhoven and
  The Hague: most likely people looking for a different, similarly named business, not clients. Ads target Metro
  Detroit only, so none of this was paid traffic, but it doubled the visitor count and halved every conversion rate.

  Unknown country: no cookie value is set, and the visitor is tracked normally (never drop a real local visitor).
  Testing on a Netlify preview or branch address (never on mirajevent.com): add ?cc=NL to any page to act as that
  country, ?cc=US to undo. The cookie lasts one hour and is refreshed on each page.
*/
export default async (request, context) => {
  const response = await context.next();
  const type = response.headers.get('content-type') || '';
  if (!type.includes('text/html')) return response;

  const url = new URL(request.url);
  let cc = String((context.geo && context.geo.country && context.geo.country.code) || '').toUpperCase();
  const live = /(^|\.)mirajevent\.com$/i.test(url.hostname);
  const test = String(url.searchParams.get('cc') || '').toUpperCase();
  if (!live && /^[A-Z]{2}$/.test(test)) cc = test;
  if (!/^[A-Z]{2}$/.test(cc)) return response;

  const res = new Response(response.body, response);
  res.headers.append('set-cookie', `miraj_cc=${cc}; Path=/; Max-Age=3600; SameSite=Lax; Secure`);
  return res;
};

/* GET only (Oct 31): page loads get the cookie; form submissions (POST to /) never pass through this function,
   so Netlify Forms handles inquiries exactly as it did before the filter. */
export const config = {
  path: '/*',
  excludedPath: ['/assets/*', '/*.ico', '/*.png', '/*.svg', '/*.txt', '/*.xml', '/*.woff2', '/*.webp'],
  method: ['GET'],
};
