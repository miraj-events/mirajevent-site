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
- Every form submission carries hidden fields: `gclid`/`gbraid`/`wbraid`, UTMs, first landing page, first referrer, AI-assistant referrer, and the page submitted from.

## Forms (Netlify Forms)

| Form | Purpose |
|---|---|
| `inquiry` | Full inquiry (home + contact + day-of) |
| `inquiry-start` | Step 1 saved when a visitor clicks Continue, so partial leads are kept |
| `quick-inquiry` | Short "reach out to me" forms |
| `guide-request` | Services-guide email request (not counted as a conversion) |

The form skeletons live in `site/netlify-forms.html` so Netlify registers them. Spam protection is a honeypot field plus Netlify's built-in filter.

## Updating reviews

Edit `tools/data/reviews.json` (rating, count, reviews), then run the build.

Maintained by Claude for Miraj Events.
