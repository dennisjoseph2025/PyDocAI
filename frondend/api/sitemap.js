import fs from 'fs'
import path from 'path'

export default function handler(req, res) {
  const paths = [
    path.join(process.cwd(), 'dist', 'sitemap.xml'),
    path.join(process.cwd(), 'public', 'sitemap.xml'),
  ]

  for (const filePath of paths) {
    try {
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf-8')
        res.setHeader('Content-Type', 'application/xml')
        res.setHeader('Cache-Control', 'public, max-age=3600')
        return res.status(200).send(content)
      }
    } catch {}
  }

  res.status(404).send('Sitemap not found')
}
