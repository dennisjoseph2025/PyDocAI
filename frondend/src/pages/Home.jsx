import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import CodeBlock from '../components/CodeBlock'
import { IconBolt, IconBrain, IconTable, IconLink, IconRocket, IconArchive, IconCode, IconDatabase } from '../components/Icons'

const pipelineSteps = [
  { step: '01', command: 'Paste code | Upload project', title: 'ADD_YOUR_CODE', desc: 'Paste code from any language, upload a .zip, or connect a GitHub repo — everything works after a quick sign-up.' },
  { step: '02', command: 'AI analyzes instantly', title: 'GET_SMART_DOCS', desc: 'Python/Django projects get deep AST analysis (models, views, serializers, endpoints). Other languages use Groq AI to generate intelligent, contextual documentation.' },
  { step: '03', command: 'Publish | Share | Export', title: 'PUBLISH_AND_SHARE', desc: 'Publish your docs with a public slug link, share privately with teammates, export as Markdown, add comments, and manage everything from your dashboard.' },
]

const modules = [
  { icon: IconBolt, title: 'UNIVERSAL_DOCS', desc: 'Paste code from any language — JavaScript, Rust, Go, Java, Python, C++, or anything else — and get AI-generated documentation instantly. No framework required.' },
  { icon: IconBrain, title: 'DJANGO_DEEP_DOCS', desc: 'For Django/DRF projects, the engine parses models, views, serializers, and URLs via AST to produce structured, comprehensive docs with field constraints and relationships.' },
  { icon: IconLink, title: 'PUBLIC_SHARING', desc: 'Generate a unique public link for any project. Share your documentation with teammates, clients, or the world — no login required to view.' },
  { icon: IconRocket, title: 'MARKDOWN_EXPORT', desc: 'Download your documentation as clean, formatted Markdown. Renders perfectly in GitHub, GitLab, VS Code, and any Markdown viewer.' },
  { icon: IconArchive, title: 'DASHBOARD', desc: 'All your documentation projects in one place. Create, view, edit, and manage docs from a central dashboard with full history.' },
  { icon: IconTable, title: 'COMMENTS & NOTIFICATIONS', desc: 'Add comments to documentation for team feedback. Get notified when docs are updated or when someone replies to your comments.' },
]

const sampleInput = `from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='articles'
    )
    status = models.CharField(
        max_length=10,
        choices=[('draft', 'Draft'), ('published', 'Published')],
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']`

const sampleFields = [
  { name: 'title', type: 'CharField', const: 'max_length=200', desc: 'Article headline string' },
  { name: 'slug', type: 'SlugField', const: 'unique=True', desc: 'URL-friendly identifier' },
  { name: 'content', type: 'TextField', const: '—', desc: 'Full HTML/Markdown body' },
  { name: 'author', type: 'ForeignKey', const: 'User (CASCADE)', desc: 'Author relational mapping' },
  { name: 'status', type: 'CharField', const: 'default=draft', desc: 'Publication state enum' },
  { name: 'created_at', type: 'DateTimeField', const: 'auto_now_add', desc: 'Initial creation timestamp' },
]

const techBadges = ['Django', 'DRF', 'Python 3.x', 'Universal Mode', 'Any Language', 'No Install', 'Groq AI', 'Markdown']

const siteUrl = 'https://pydocai.vercel.app'

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'PyDocAI',
  applicationCategory: 'DeveloperApplication',
  operatingSystem: 'Web',
  description: 'AI-powered documentation generator for Python, Django, and any programming language. Upload code or connect a Git repo to generate comprehensive documentation automatically.',
  url: siteUrl,
  author: { '@type': 'Person', name: 'Denjo (Dennis Joseph)', url: 'https://dennis-r.vercel.app/' },
  offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
}

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return null

  return (
    <div className="relative z-10 flex flex-col bg-bg-primary">
      <Helmet>
        <title>PyDocAI by Denjo — AI-Powered Documentation Generator for Any Language</title>
        <meta name="description" content="Upload your Django project or paste code from any language — AI generates beautiful, comprehensive docs. Created by Denjo (Dennis Joseph). Free universal documentation generator." />
        <link rel="canonical" href={siteUrl} />
        <meta property="og:title" content="PyDocAI by Denjo — AI-Powered Documentation Generator for Any Language" />
        <meta property="og:description" content="Upload your Django project or paste code from any language — AI generates beautiful, comprehensive docs." />
        <meta property="og:url" content={siteUrl} />
        <meta name="twitter:title" content="PyDocAI by Denjo — AI-Powered Documentation Generator for Any Language" />
        <meta name="twitter:description" content="Upload your Django project or paste code from any language — AI generates beautiful, comprehensive docs." />
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>
      <Navbar />

      {/* --- HERO SECTION --- */}
      <section id="hero" className="min-h-[90vh] sm:min-h-screen flex items-center justify-center relative overflow-hidden bg-bg-primary border-b border-border">
        <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
        <div className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M60 0v60H0' fill='none' stroke='%233776AB' stroke-width='1'/%3E%3C/svg%3E")`,
            backgroundSize: '60px 60px'
          }}
        />

        <div className="relative z-10 text-center px-4 sm:px-6 max-w-5xl mx-auto">
          <h1 className="font-display font-extrabold text-4xl sm:text-5xl md:text-7xl lg:text-8xl leading-none tracking-tight text-ink-primary animate-slide-up">
            <span className="text-accent-blue">Python</span> Docs,<br />
            <span className="text-accent">generated</span>.
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-ink-secondary text-center max-w-2xl mx-auto mt-4 sm:mt-6 animate-slide-up px-2" style={{ animationDelay: '100ms' }}>
            Upload your Django project <span className="text-ink-primary font-semibold">or</span> paste code from any language — AI generates beautiful, comprehensive docs in seconds.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center mt-8 sm:mt-10 animate-slide-up px-4 sm:px-0" style={{ animationDelay: '200ms' }}>
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn-accent text-sm sm:text-base text-center">Go to Dashboard →</Link>
            ) : (
              <Link to="/register" className="btn-accent text-sm sm:text-base text-center">Start for Free →</Link>
            )}
            <a href="#pipeline" className="btn-ghost text-sm sm:text-base text-center">See How It Works</a>
          </div>
          <div className="flex gap-2 sm:gap-3 mt-6 sm:mt-8 justify-center flex-wrap animate-slide-up px-2" style={{ animationDelay: '300ms' }}>
            {techBadges.map((badge) => (
              <span key={badge} className="text-[10px] sm:text-xs font-mono text-ink-secondary border border-border rounded-full px-2 sm:px-3 py-1 bg-bg-surface shadow-sm">
                {badge}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* --- PIPELINE SECTION --- */}
      <section id="pipeline" className="py-16 sm:py-20 md:py-24 bg-[#080e17] border-b border-border/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-3 mb-6 sm:mb-8">
            <IconDatabase className="w-4 sm:w-5 h-4 sm:h-5 text-accent-blue shrink-0" />
            <h2 className="font-mono text-[11px] sm:text-sm text-ink-muted uppercase tracking-widest">Execution_Pipeline</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 border border-border rounded-md overflow-hidden bg-bg-surface">
            {pipelineSteps.map((item, idx) => (
              <div key={item.step} className={`p-5 sm:p-6 md:p-8 relative ${idx !== pipelineSteps.length - 1 ? 'border-b md:border-b-0 md:border-r border-border' : ''}`}>
                <div className="font-mono text-[9px] sm:text-[10px] text-accent-blue mb-3 sm:mb-4 break-all">
                  <span className="text-ink-muted mr-2">$</span>{item.command}
                </div>
                <h3 className="font-display font-bold text-base sm:text-lg text-ink-primary mb-2 sm:mb-3">
                  <span className="text-accent mr-2">{item.step}.</span>{item.title}
                </h3>
                <p className="text-ink-secondary text-xs sm:text-sm leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- I/O PREVIEW SECTION --- */}
      <section className="py-16 sm:py-20 md:py-24 bg-bg-primary">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-3 mb-6 sm:mb-8">
            <IconCode className="w-4 sm:w-5 h-4 sm:h-5 text-accent shrink-0" />
            <h2 className="font-mono text-[11px] sm:text-sm text-ink-muted uppercase tracking-widest">I/O_Compilation_Preview</h2>
          </div>

          <div className="border border-border rounded-md bg-[#0b1320] shadow-2xl overflow-hidden flex flex-col lg:flex-row">

            {/* Left Pane - Input Code */}
            <div className="w-full lg:w-[45%] flex flex-col border-b lg:border-b-0 lg:border-r border-border">
              <div className="bg-[#080e17] px-3 sm:px-4 py-2 border-b border-border flex items-center gap-3">
                <div className="flex gap-1.5 opacity-50 hover:opacity-100 transition-opacity">
                  <div className="w-2.5 sm:w-3 h-2.5 sm:h-3 rounded-full bg-danger"></div>
                  <div className="w-2.5 sm:w-3 h-2.5 sm:h-3 rounded-full bg-warning"></div>
                  <div className="w-2.5 sm:w-3 h-2.5 sm:h-3 rounded-full bg-success"></div>
                </div>
                <span className="text-[10px] sm:text-[11px] font-mono text-ink-muted ml-2">app/models.py</span>
              </div>
              <div className="flex-1 bg-[#080e17] max-h-[300px] sm:max-h-none overflow-auto">
                <CodeBlock code={sampleInput} filename="" language="python" />
              </div>
            </div>

            {/* Right Pane - Rendered Output */}
            <div className="w-full lg:w-[55%] flex flex-col bg-[#0b1320]">
              <div className="bg-[#080e17] px-3 sm:px-4 py-2 border-b border-border flex items-center">
                <span className="text-[10px] sm:text-[11px] font-mono text-accent-blue border-b border-accent-blue pb-[9px] -mb-[9px]">
                  models.md
                </span>
                <span className="text-[10px] sm:text-[11px] font-mono text-ink-muted ml-4 sm:ml-6 cursor-not-allowed">
                  endpoints.md
                </span>
              </div>
              <div className="p-4 sm:p-6 md:p-8 flex-1 overflow-x-auto">
                <div className="border-l-4 border-accent-blue pl-3 sm:pl-4 mb-4 sm:mb-6">
                  <h3 className="font-display font-bold text-lg sm:text-xl md:text-2xl text-ink-primary mb-1">Article <span className="text-xs sm:text-sm font-mono text-ink-muted font-normal">Model</span></h3>
                  <p className="text-ink-secondary text-xs sm:text-sm">
                    Represents a blog article with draft/published workflow. Ordered by creation date descending.
                  </p>
                </div>

                <div className="border border-border rounded overflow-hidden min-w-[500px] sm:min-w-0">
                  <table className="w-full text-left font-mono text-[10px] sm:text-xs">
                    <thead className="bg-[#080e17] border-b border-border text-ink-muted">
                      <tr>
                        <th className="px-2 sm:px-4 py-1.5 sm:py-2 font-normal">Field</th>
                        <th className="px-2 sm:px-4 py-1.5 sm:py-2 font-normal">Type</th>
                        <th className="px-2 sm:px-4 py-1.5 sm:py-2 font-normal hidden sm:table-cell">Constraints</th>
                        <th className="px-2 sm:px-4 py-1.5 sm:py-2 font-normal">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border text-ink-secondary">
                      {sampleFields.map((f) => (
                        <tr key={f.name} className="hover:bg-bg-surface/50">
                          <td className="px-2 sm:px-4 py-2 sm:py-3 text-accent font-bold whitespace-nowrap">{f.name}</td>
                          <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">{f.type}</td>
                          <td className="px-2 sm:px-4 py-2 sm:py-3 text-ink-muted hidden sm:table-cell whitespace-nowrap">{f.const}</td>
                          <td className="px-2 sm:px-4 py-2 sm:py-3 text-[10px] sm:text-xs">{f.desc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* --- CORE MODULES SECTION --- */}
      <section className="py-16 sm:py-20 md:py-24 bg-[#080e17] border-t border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-3 mb-6 sm:mb-8">
            <IconArchive className="w-4 sm:w-5 h-4 sm:h-5 text-accent shrink-0" />
            <h2 className="font-mono text-[11px] sm:text-sm text-ink-muted uppercase tracking-widest">System_Capabilities</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-border border border-border rounded-md overflow-hidden">
            {modules.map((m) => (
              <div key={m.title} className="bg-bg-surface p-5 sm:p-6 md:p-8 flex items-start gap-4 sm:gap-5 hover:bg-[#16273d] transition-colors group">
                <div className="mt-1 text-accent border border-accent/20 bg-accent/5 p-1.5 sm:p-2 rounded group-hover:bg-accent/10 transition-colors shrink-0">
                  <m.icon className="w-4 sm:w-5 h-4 sm:h-5" />
                </div>
                <div className="min-w-0">
                  <h4 className="font-mono text-xs sm:text-sm font-bold text-ink-primary tracking-wide mb-1.5 sm:mb-2 break-words">{m.title}</h4>
                  <p className="text-ink-secondary text-xs sm:text-sm leading-relaxed">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
