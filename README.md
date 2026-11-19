# Portfolio site

A small static website, in Hebrew (`/`) and English (`/en/`). No framework: one Python script turns
the content files into HTML pages.

## Change the text

| What | File |
|---|---|
| Name, contact details, all page text (both languages) | `content/site.json` |
| Projects: featured pages and the "more" cards | `content/projects.json` |
| The troubleshooting write-up | `content/notes.json` |
| Colours, fonts, layout | `assets/style.css` |
| Screenshots | `assets/media/<project-slug>/` |

Each text has a Hebrew (`he`) and an English (`en`) version side by side.

**Before publishing**, fill in `contact` in `content/site.json` (at least `email` or `whatsapp`).
Until then every page shows a red "Draft" bar.

### Adding screenshots to a project

1. Put the image in `assets/media/<slug>/` (for example `assets/media/click-to-read/reader.png`).
   About 540 px wide for a phone screenshot, 1200 px for a wide one. Check it shows no names,
   emails, phone numbers or messages.
2. Add it to that project's `"media"` list in `content/projects.json`:
   `{ "file": "click-to-read/reader.png", "alt": { "he": "...", "en": "..." }, "phone": true }`
   Use `"wide": true` instead of `"phone": true` for a landscape image; the first wide image
   also becomes the project's card picture on the home page.

## Build and preview

```powershell
python build.py
python -m http.server 8787 --directory dist
```

Then open http://127.0.0.1:8787.

## The Lesson Journal demo

`demo/lesson-journal/app-source.html` is a copy of the real app's `src/Index.html`.
`fake-backend.js` replaces Google with made-up students, so it runs in any browser and
saves nothing. After changing the real app, copy its `src/Index.html` here again and rebuild.
`#lesson` and `#student` at the end of the demo address open those screens directly
(used for screenshots).

## Publishing on Cloudflare

The site is a Cloudflare Worker with static assets (`wrangler.jsonc`), live at
https://aviyah-apps.taviyah.workers.dev. To publish a change:

```powershell
python build.py
npx wrangler@4 deploy
```

The first run asks you to sign in to Cloudflare in the browser. A custom domain can be added in
the Cloudflare dashboard under the Worker's Settings → Domains & Routes; then put it in
`"domain"` in `content/site.json` so search engines get the right links between languages.

`_headers` sets basic security headers.
