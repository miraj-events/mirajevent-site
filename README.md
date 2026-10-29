# mirajevent.com

Static website for **Miraj Events, LLC**, hosted on Netlify. Netlify publishes the `site/` folder exactly as committed. There is no build step on Netlify.

## Structure

| Path | What it is |
|---|---|
| `site/` | The live website (generated; don't hand-edit) |
| `tools/build.py` | Generates `site/` from the approved design + data |
| `tools/source/preview-v47.html` | Approved design (preview v47, Oct 24 2026) |
| `tools/data/reviews.json` | Google rating, review count, featured reviews |
| `tools/assets/` | JS, extra CSS, day-of page, privacy page, llms.txt, icons |
| `netlify.toml` | 301 redirects for the old Squarespace URLs + headers |
| `netlify/functions/submission-created.mjs` | Sends each inquiry to ChatGPT ads (OpenAI Conversions API) from the server; see Tracking |

Regenerate after any change:

```bash
python3 tools/build.py
```

## Pages

`/` · `/services` · `/day-of-coordination` · `/about` · `/contact` · `/thank-you` (noindex) · `/privacy` · `404`

## Tracking (do not change IDs without updating Google Ads)

- GA4 `G-PVV95TW26B` and Google Ads `AW-16694224609` load on every page.
- The Google Ads **Form Fill** conversion (`AW-16694224609/zLObCLKztNAZEOHNtpg-`) fires on `/thank-you`, the same page and label as the Squarespace site.
  - It fires once per submission, with a value set by the package chosen and a transaction ID.
  - Enhanced conversions data (email/phone) is sent with it.
- GA4 events: `generate_lead`, `form_start`, `phone_click`, `whatsapp_click`, `email_click`, `view_package`, `guide_request`, `ai_referral`.
- Meta Pixel (`META_PIXEL` in `tools/build.py`; empty = off) loads on every page on the live domain only.
  - `PageView` fires on every page. `Lead` fires on `/thank-you` once per submission, with the same transaction ID as the Google conversion (`eventID`).
  - On `/thank-you` the inquiry's email and phone are passed for advanced matching; the pixel hashes them in the browser. This is disclosed on `/privacy`.
- OpenAI Ads (ChatGPT ads) pixel `DQ1HpbhhjYa76ncDFrtMaF` (`OAI_PIXEL` in `tools/build.py`) loads on every page on the live domain only. `lead_created` fires on `/thank-you` once per submission, with the Lead ID as its `event_id`.
- **ChatGPT ads server copy** (Oct 28): `netlify/functions/submission-created.mjs` runs on every verified `inquiry` / `quick-inquiry` submission and sends the same `lead_created` event to the OpenAI Conversions API, so leads still count when the pixel is blocked.
  - Same Lead ID as the pixel, so OpenAI keeps one copy. A submission without a Lead ID is not sent.
  - Carries `oppref` and `obref` from `click_id`, SHA-256 hashes of email, phone and first/last name, and the IP address and browser Netlify records.
  - Inquiries from internal devices and names starting "TEST" are sent `validate_only` (checked, not recorded).
  - Needs the Netlify environment variable `OPENAI_ADS_API_KEY` (scope Functions), a key from OpenAI Ads Manager → Conversions → Conversion keys. Redeploy after changing it.
  - Logs: Netlify → Logs → Functions → `submission-created`, one line per lead with OpenAI's HTTP status.
- Every form submission carries hidden fields `source` (one readable line: Google Ads · tag, ChatGPT ad, Google search (organic), Google Business Profile, ig / social, Direct…), `click_id` (gclid/gbraid/wbraid/oppref, plus the pixel's `obref` for ChatGPT-ad visitors), `landing_page`, `form_page` and `lead_id` (built in `site.js` `attribution()`; 90-day window).
- Every inquiry has a **Lead ID** (`lead_id`, e.g. `ME-261028-K3F9`). It is in the notification email and Netlify, and it is the same ID sent as the Google Ads `transaction_id`, the OpenAI `event_id` and the Meta `eventID`. The step-1 "Unfinished" email and the finished inquiry from the same form share it.
- **Internal devices:** open any page with `?internal=1` once on an owner/staff device. That device then loads no GA4, Google Ads, OpenAI or Meta tags and fires no conversions. Its inquiries still email, with Source starting "Internal device (test)". `?internal=0` undoes it (stored in localStorage, per browser).

## Forms (Netlify Forms)

| Form | Purpose |
|---|---|
| `inquiry` | Full inquiry (home + contact + day-of) |
| `inquiry-start` | Step 1, sent only if the visitor doesn't finish (tab hidden/closed, or 15 min after Continue), so partial leads are kept |
| `quick-inquiry` | Short "reach out to me" forms |
| `guide-request` | Services-guide email request (not counted as a conversion) |

The form skeletons live in `site/netlify-forms.html` so Netlify registers them. Spam protection is a honeypot field plus Netlify's built-in filter.

## Where to see where leads come from

- **Each lead:** the "Source" line in the inquiry email (also in Netlify → Forms). This is the most reliable per-lead answer.
- **Totals by channel:** GA4 → Reports → Acquisition → Traffic acquisition, with the key events column set to `generate_lead`.
- **Per ad platform:** Google Ads → Goals → Conversions (Form Fill, calls, taps), OpenAI Ads Manager (Lead – website inquiry), Meta Events Manager (Lead). Each platform counts only its own ads, so their totals don't add up to the number of inquiries.

## Updating reviews

Edit `tools/data/reviews.json` (rating, count, reviews), then run the build.

Maintained by Claude for Miraj Events.
