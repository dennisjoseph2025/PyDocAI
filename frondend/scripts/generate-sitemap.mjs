import fs from 'fs'
import path from 'path'
import https from 'https'
import http from 'http'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = path.resolve(__dirname, '..', 'public')
const SITEMAP_PATH = path.join(PUBLIC_DIR, 'sitemap.xml')

const SITE_URL = 'https://pydocai.vercel.app'
const TODAY = new Date().toISOString().split('T')[0]

function nodeFetch(url, options = {}) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http
    const agent = url.startsWith('https') ? new https.Agent({ rejectUnauthorized: false }) : undefined
    const req = mod.get(url, { ...options, agent, timeout: 8000 }, (res) => {
      const chunks = []
      res.on('data', (c) => chunks.push(c))
      res.on('end', () => {
        const body = Buffer.concat(chunks).toString()
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          const redirectUrl = new URL(res.headers.location, url).toString()
          nodeFetch(redirectUrl, options).then(resolve).catch(reject)
        } else {
          resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, status: res.statusCode, body, json: () => JSON.parse(body) })
        }
      })
    })
    req.on('error', reject)
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')) })
  })
}

async function fetchAPI() {
  const attempts = [
    process.env.SITEMAP_API_URL && `${process.env.SITEMAP_API_URL.replace(/\/+$/, '')}/api/public/projects/?limit=1000`,
    'https://34.226.86.46:8000/api/public/projects/?limit=1000',
    'http://34.226.86.46:8000/api/public/projects/?limit=1000',
    `${SITE_URL}/api/public/projects/?limit=1000`,
  ].filter(Boolean)

  for (const url of attempts) {
    try {
      const res = await nodeFetch(url)
      if (res.ok) return await res.json()
    } catch {}
  }
  return null
}

async function generate() {
  const urls = [
    { loc: `${SITE_URL}/`, lastmod: TODAY, changefreq: 'weekly', priority: '1.0' },
    { loc: `${SITE_URL}/published`, lastmod: TODAY, changefreq: 'daily', priority: '0.9' },
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
      console.log(`Sitemap: fetched ${projects.length} published projects from API`)
    } else {
      console.log('Sitemap: API unreachable, using static URLs only')
    }
  } catch (e) {
    console.warn('Sitemap: error fetching API, using static URLs only')
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
