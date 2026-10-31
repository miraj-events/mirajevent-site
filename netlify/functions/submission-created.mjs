/*
  ChatGPT ads (OpenAI Ads): a server-side copy of every inquiry, sent to the OpenAI Conversions API as "lead_created".
  Netlify runs this automatically for each verified (non-spam) form submission, because of the file name
  ("submission-created" is Netlify's form event; the name must stay exactly this). Added Oct 28, 2026.

  Why: the browser pixel on /thank-you can be blocked or skipped (ad blockers, privacy settings, the visitor closing
  the tab first). This sends the same lead from Netlify's server, so OpenAI still counts it and Ads Manager no longer
  warns "No recent server-to-server events".

  How it stays accurate
  - Only the two forms that count as leads (the ones that reach /thank-you): "inquiry" and "quick-inquiry".
    The step-1 "Unfinished" save and services-guide requests are ignored.
  - Event id = the inquiry's Lead ID (hidden field "lead_id", e.g. ME-261028-K3F9). The thank-you pixel sends the
    same ID as its event_id, so OpenAI keeps one copy of each lead. A submission without a Lead ID is not sent
    (the pixel still counts it), so nothing is ever counted twice.
  - The ad credit travels with the server copy too, so it doesn't matter which copy reaches OpenAI first:
      oppref  the ChatGPT ad click id, saved by assets/site.js and posted in the "click_id" field
      obref   the pixel's browser id (__obref cookie), added to "click_id" by site.js for ChatGPT-ad visitors
      user    SHA-256 hashes of email, phone and first/last name (the raw details never leave Netlify), plus the
              visitor's IP address and browser, which Netlify records with every submission
  - Inquiries from a device marked internal (?internal=1; Source starts "Internal device"), from outside the US/Canada
    (Source starts "Out of area"; see netlify/edge-functions/geo.js), names starting with
    "TEST", and forms sent from a Netlify preview address instead of mirajevent.com are sent with validate_only:
    OpenAI checks the format and records nothing.

  Setup: Netlify > Site configuration > Environment variables > OPENAI_ADS_API_KEY (scope: Functions), the key from
  OpenAI Ads Manager > Conversions > Conversion keys. Redeploy after adding it. Without the key this logs one line and stops.
  It never throws: Netlify has already saved and emailed the inquiry, whatever happens here.
  Logs: Netlify > Logs > Functions > submission-created (one line per lead with OpenAI's HTTP status).
  Spec: https://developers.openai.com/ads/conversions-api
*/
import { createHash } from 'node:crypto';

const PIXEL_ID = 'DQ1HpbhhjYa76ncDFrtMaF';            // public pixel id, same as OAI_PIXEL in tools/build.py
const ENDPOINT = 'https://bzr.openai.com/v1/events';
const LEAD_FORMS = new Set(['inquiry', 'quick-inquiry']);
const SITE = 'https://www.mirajevent.com';

const sha256 = (s) => createHash('sha256').update(s, 'utf8').digest('hex');
const normEmail = (v) => String(v || '').trim().toLowerCase();
/* OpenAI phone rule: keep the country code, digits only, no leading "+" or zeros, 8-15 digits.
   US numbers typed without the country code (10 digits) get the leading 1. */
function normPhone(v) {
  let d = String(v || '').replace(/\D/g, '');
  if (d.length === 10) d = '1' + d;
  d = d.replace(/^0+/, '');
  return d.length >= 8 && d.length <= 15 ? d : '';
}
/* OpenAI name rule: lowercase, remove all whitespace and ASCII punctuation, keep accents. */
const normName = (v) => String(v || '').toLowerCase().replace(/[\s!-/:-@[-`{-~]/g, '');
const field = (s, key) => (String(s || '').match(new RegExp('(?:^|\\s)' + key + ':(\\S+)')) || [])[1] || '';

export function leadId(d) {
  const v = String((d && d.lead_id) || '').trim();
  return /^[A-Za-z0-9_-]{4,64}$/.test(v) ? v : '';
}

/* A form sent from anywhere but the live site (a Netlify preview or branch address) counts as a test, the same rule
   the site's own tags follow. Netlify records the page address as "referrer"; if it is missing, the lead is treated as live. */
export function fromLiveSite(d) {
  let host = '';
  try { host = new URL(String((d && d.referrer) || '')).hostname; } catch { host = ''; }
  return !host || /(^|\.)mirajevent\.com$/i.test(host);
}

export function isTest(d) {
  return /^test\b/i.test(String((d && d.name) || '').trim())
    || /^internal device/i.test(String((d && d.source) || '').trim())
    || /^out of area/i.test(String((d && d.source) || '').trim())
    || !fromLiveSite(d);
}

export function buildEvent(p) {
  const d = (p && p.data) || {};
  const page = String(d.form_page || '/');
  const user = {};
  const e = normEmail(d.email); if (e) user.emails_sha256 = [sha256(e)];
  const ph = normPhone(d.phone); if (ph) user.phone_numbers_sha256 = [sha256(ph)];
  const parts = String(d.name || '').trim().split(/\s+/).filter(Boolean);
  const first = normName(parts[0]); if (first) user.first_names_sha256 = [sha256(first)];
  const last = parts.length > 1 ? normName(parts[parts.length - 1]) : ''; if (last) user.last_names_sha256 = [sha256(last)];
  if (d.ip) user.ip_address = String(d.ip);
  if (d.user_agent) user.user_agent = String(d.user_agent);
  const obref = field(d.click_id, 'obref'); if (obref) user.obref = obref;

  const ts = Date.parse((p && p.created_at) || '');
  const ev = {
    id: leadId(d),
    type: 'lead_created',
    timestamp_ms: Number.isFinite(ts) ? Math.min(ts, Date.now()) : Date.now(),
    action_source: 'web',
    source_url: SITE + (page.startsWith('/') ? page.slice(0, 300) : '/'),
    data: { type: 'customer_action' },
  };
  const oppref = field(d.click_id, 'oppref'); if (oppref) ev.oppref = oppref;
  if (Object.keys(user).length) ev.user = user;
  return ev;
}

async function send(body, key) {
  let last = { status: 0, text: '' };
  for (let attempt = 1; attempt <= 2; attempt++) {   // one retry with the same event id (OpenAI keeps one copy)
    try {
      const res = await fetch(`${ENDPOINT}?pid=${encodeURIComponent(PIXEL_ID)}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(4000),
      });
      last = { status: res.status, text: (await res.text()).replace(/\s+/g, ' ').slice(0, 300) };
      if (res.status < 500) return last;
    } catch (err) {
      last = { status: 0, text: String((err && err.message) || err) };
    }
    if (attempt === 1) await new Promise((r) => setTimeout(r, 500));
  }
  return last;
}

export default async (req) => {
  try {
    const body = (await req.json()) || {};
    const payload = body.payload || body;   // Netlify sends { payload: <submission>, site }; a bare submission works too
    const d = payload.data || {};
    const form = payload.form_name || d['form-name'] || '';
    if (!LEAD_FORMS.has(form)) {
      console.log(`ChatGPT ads server event skipped: "${String(form).slice(0, 40)}" is not a lead form`
        + ` (event keys: ${Object.keys(body).slice(0, 8).join(', ') || 'none'})`);
      return new Response('skipped: not a lead form');
    }
    if (!leadId(d)) {
      console.log(`ChatGPT ads server event skipped: no Lead ID on this ${form} submission (the thank-you pixel still counts it)`);
      return new Response('skipped: no lead id');
    }
    const key = process.env.OPENAI_ADS_API_KEY;
    if (!key) {
      console.log('ChatGPT ads server event skipped: OPENAI_ADS_API_KEY is not set in Netlify');
      return new Response('skipped: no key');
    }
    const event = buildEvent(payload);
    const test = isTest(d);
    const request = { integration_source: 'miraj-netlify-forms', validate_only: test, events: [event] };
    const r = await send(request, key);
    const ok = r.status >= 200 && r.status < 300;
    console.log(`ChatGPT ads lead_created ${event.id}${test ? ' (test, validate only)' : ''}`
      + `${event.oppref ? ' [ChatGPT ad click]' : ''}: ${ok ? 'OK' : 'FAILED'} HTTP ${r.status} ${r.text}`);
    return new Response(ok ? 'sent' : 'failed (logged)');
  } catch (err) {
    console.log('ChatGPT ads server event error:', (err && err.message) || err);
    return new Response('error (logged)');
  }
};
