import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default function handler(req, res) {
  const cwd = process.cwd()
  const candidates = [
    path.join(cwd, 'dist', 'sitemap.xml'),
    path.join(cwd, 'public', 'sitemap.xml'),
    path.join(__dirname, '..', 'dist', 'sitemap.xml'),
    path.join(__dirname, '..', 'public', 'sitemap.xml'),
    path.join(__dirname, '..', '..', 'dist', 'sitemap.xml'),
    path.join(__dirname, '..', '..', 'public', 'sitemap.xml'),
  ]

  for (const filePath of candidates) {
    try {
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf-8')
        res.setHeader('Content-Type', 'text/html')
        res.setHeader('Cache-Control', 'public, max-age=3600')
        return res.status(200).send(content)
      }
    } catch {}
  }

  res.status(404).json({
    error: 'Sitemap not found',
    cwd,
    candidates: candidates.map(p => ({ path: p, exists: fs.existsSync(p) })),
  })
}
