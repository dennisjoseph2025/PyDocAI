import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = path.resolve(__dirname, '..', 'public')
const SITEMAP_PATH = path.join(PUBLIC_DIR, 'sitemap.xml')

const SITE_URL = 'https://pydocai.vercel.app'
const TODAY = new Date().toISOString().split('T')[0]

async function fetchAPI(endpoint) {
  const urls = [
    process.env.SITEMAP_API_URL,
    `${SITE_URL}/api/public/projects/?limit=1000`,
    'http://34.226.86.46:8000/api/public/projects/?limit=1000',
  ]
  for (const base of urls) {
    if (!base) continue
    try {
      const url = base.includes('/api/') ? base : `${base.replace(/\/+$/, '')}/api/public/projects/?limit=1000`
      const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
      if (res.ok) return await res.json()
    } catch {}
  }
  return null
}

async function generate() {
  const urls = [
    {
      loc: `${SITE_URL}/`,
      lastmod: TODAY,
      changefreq: 'weekly',
      priority: '1.0',
    },
    {
      loc: `${SITE_URL}/published`,
      lastmod: TODAY,
      changefreq: 'daily',
      priority: '0.9',
    },
  ]

  try {
    const data = await fetchAPI()
    if (data) {
      const projects = data.results || data || []
      for (const p of projects) {
        if (p.public_slug) {
          urls.push({
            loc: `${SITE_URL}/public/${p.public_slug}`,
            lastmod: p.updated_at ? p.updated_at.split('T')[0] : TODAY,
            changefreq: 'weekly',
            priority: '0.8',
          })
        }
      }
      console.log(`Fetched ${projects.length} published projects from API`)
    }
  } catch (e) {
    console.warn('Could not fetch published projects, using static URLs only')
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(u => `  <url>
    <loc>${u.loc}</loc>
    <lastmod>${u.lastmod}</lastmod>
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`).join('\n')}
</urlset>
`

  fs.writeFileSync(SITEMAP_PATH, xml, 'utf-8')
  console.log(`Sitemap generated: ${urls.length} URLs → ${SITEMAP_PATH}`)
}

generate()
