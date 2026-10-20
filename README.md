# Robert Kimball – portfolio site

A static website built from one content file by one small Python script. No frameworks and no npm.

```
portfolio/
  src/content.json        ← all site text, projects, images, videos (edit this)
  src/assets/style.css    ← design
  src/assets/script.js    ← mobile menu, image lightbox, copy-email button
  src/favicon.svg         ← "RK" monogram
  assets/img/<project>/   ← full-size source images
  assets/video/           ← project videos (MP4)
  assets/Robert_Kimball_Resume.pdf
  build.py                ← generates site/
  site/                   ← the finished website (generated; upload this)
  TODO.md                 ← facts and pictures still missing from the projects
```

## 1. Edit content

Open `src/content.json` in any text editor (VS Code shows JSON errors as you type).

- `profile`: name, pitch, email, phone, LinkedIn, citizenship, headshot, About text, hobby photos.
- `highlights`: the skill/honor chips under the hero.
- `education`, `skills`, `experience`: newest job first. Keep the wording in line with the resume.
- `projects`: one entry per project page, in display order (strongest first).
  - `slug`: the page file name (`projects/<slug>.html`). Don't change it once the site is shared.
  - `home`: `"featured"` (card on the home page), `"other"` ("Other builds" list) or `"education"` (linked from the Education box).
  - `card_image`: set to `false` to show the `stat` text on the home-page card instead of the first image.
  - `card`: the one-line result on the home-page card. `stat`: big text on the card when the project has no images.
  - `summary`: the bar at the top of the page. Any key/value pair works (`"Problem"`, `"My role"`, `"Tools"`, `"Result"`, `"Duration"`, ...). Leave out what you don't know.
  - `sections`: `{"heading": "...", "items": [...]}`. An item is a string, or `{"text": "...", "items": [...]}` for sub-bullets.
  - `images`: `{"src": "assets/img/<slug>/photo.jpg", "alt": "what the image shows", "caption": "..."}`. The first image is the card image. Use full-size originals; the build makes the web sizes.
  - `videos`: `{"src": "assets/video/name.mp4", "poster": "assets/img/<slug>/poster.jpg", "title": "..."}`.
  - `video_position` (optional): how many images to show before the videos (default 0, videos first).
  - `intro` (optional): a highlighted note above the images.
- `cad_gallery`: the "More CAD & 3D-printed builds" grid on the home page. Each item has `title`, `image` (`src`, `alt`), `size`, `notes`, `purpose` (leave `""` to hide it) and an optional `link` (a project slug).
- `site.base_url`: the final web address (used for the sitemap and link previews). **Set this before you publish.**

To update the resume, replace `assets/Robert_Kimball_Resume.pdf` (keep the name) and rebuild.

## 2. Build

Needs Python 3.9+ and Pillow (one-time install):

```
python -m pip install pillow
python build.py
```

The build writes `site/`: `index.html`, one page per project in `projects/`, `404.html`, `sitemap.xml`, `robots.txt`, the favicon, and resized images (600 px and 1600 px, JPEG + WebP). EXIF data, including phone GPS locations, is removed from every image. Unchanged images are skipped, so rebuilds are fast.

## 3. Preview locally

```
python -m http.server 8000 --directory site
```

Open http://localhost:8000 and press Ctrl+C in the terminal to stop.

## 4. Publish for free

### How this site is published now

The source lives at https://github.com/rkimball2021-hue/portfolio. Every push to `main` runs `.github/workflows/deploy.yml`, which runs `build.py` and uploads `site/` to Cloudflare Pages (robertlkimball.com). Watch it under the repo's **Actions** tab or with `gh run watch`.

```
git add -A
git commit -m "Describe the change"
git push
```

The workflow needs the repo secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` and the repo variable `CLOUDFLARE_PROJECT` (the Cloudflare Pages project name), under **Settings → Secrets and variables → Actions**.

The options below are the original manual alternatives.

### Option A: GitHub Pages

1. Create a free GitHub account, then a **public** repository named `<your-username>.github.io`.
2. Easiest: on the repository page click **Add file → Upload files**, drag in everything *inside* `site/` (not the folder itself), and commit.
3. Go to **Settings → Pages**, set *Source* to "Deploy from a branch", branch `main`, folder `/ (root)`. After a minute the site is live at `https://<your-username>.github.io`.
4. To update: rebuild, then upload the changed files again.

Automatic option: put this whole `portfolio/` folder in the repository instead and set *Settings → Pages → Source* to **GitHub Actions**. The included `.github/workflows/pages.yml` runs `build.py` and publishes `site/` on every push.

Note: use a user site (`<username>.github.io`) or a custom domain. On a project sub-path (`<username>.github.io/portfolio/`) everything works except the links on the 404 page.

### Option B: Netlify drag and drop

1. Sign up at https://app.netlify.com (free).
2. **Sites → Add new site → Deploy manually**, then drag the `site/` folder onto the page.
3. You get a `*.netlify.app` address. Rename it under **Site configuration → Change site name**. To update, drag the new `site/` folder onto **Deploys**.

## 5. Custom domain (about $12–20/year)

1. Buy a domain (e.g. Cloudflare Registrar, Namecheap, Porkbun).
2. **GitHub Pages:** *Settings → Pages → Custom domain* → enter `www.yourname.com` and save. At your registrar, add DNS records:
   - `CNAME` `www` → `<your-username>.github.io`
   - for the bare domain, four `A` records `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`

   When the check passes, tick **Enforce HTTPS**. (GitHub's current list of IPs is in its "Managing a custom domain" docs.)
3. **Netlify:** *Domain management → Add a domain* and follow the DNS steps it shows (HTTPS is automatic).
4. Set `site.base_url` in `src/content.json` to the new address, rebuild, and publish again.
5. Update the "Portfolio" link on your resume and LinkedIn.
