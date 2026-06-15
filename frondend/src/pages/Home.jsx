import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import CodeBlock from '../components/CodeBlock'
import { IconBolt, IconBrain, IconTable, IconLink, IconRocket, IconArchive, IconCode, IconDatabase } from '../components/Icons'

const pipelineSteps = [
  { step: '01', command: 'git clone <repo>', title: 'INGEST_SOURCE', desc: 'Connect a Git repository, upload a local codebase archive, or input raw Python files directly.' },
  { step: '02', command: 'pydocai analyze ./', title: 'PARSE_AST_TREE', desc: 'The engine parses models, views, serializers, and URLs to build a relational map of your Django architecture.' },
  { step: '03', command: 'pydocai compile --md', title: 'GENERATE_MARKDOWN', desc: 'Receive standard Markdown files featuring field constraints, foreign key mappings, and endpoint specs.' },
]

const modules = [
  { icon: IconBolt, title: 'ASYNC_COMPILATION', desc: 'Upload your codebase and retrieve complete documentation payloads in seconds via optimized AST parsing.' },
  { icon: IconBrain, title: 'AI_PATTERN_RECOGNITION', desc: 'Deep contextual understanding of complex Django patterns, DRF views, and nested serializers.' },
  { icon: IconTable, title: 'SCHEMA_GENERATION', desc: 'Auto-compiled Markdown tables detailing database models, field types, constraints, and relationships.' },
  { icon: IconLink, title: 'ENDPOINT_MAPPING', desc: 'Automated REST API documentation including allowed HTTP methods, path parameters, and JSON response bodies.' },
  { icon: IconRocket, title: 'VS_CODE_COMPATIBLE', desc: 'Generated markdown is strictly formatted to render perfectly in GitHub, GitLab, and VS Code preview modes.' },
  { icon: IconArchive, title: 'MULTI_SOURCE_INGESTION', desc: 'Supports direct .zip uploads, single .py files, and public/private GitHub repository linking.' },
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

const techBadges = ['Django', 'DRF', 'Python 3.x', 'REST APIs', 'Models', 'Serializers', 'Views', 'URLs']

const siteUrl = 'https://pydocai.vercel.app'

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'PyDocAI',
  applicationCategory: 'DeveloperApplication',
  operatingSystem: 'Web',
  description: 'AI-powered documentation generator for Python and Django projects. Upload code or connect a Git repo to generate beautiful, comprehensive documentation automatically.',
  url: siteUrl,
  author: { '@type': 'Organization', name: 'PyDocAI' },
  offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
}

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return null

  return (
    <div className="relative z-10 flex flex-col bg-bg-primary">
      <Helmet>
        <title>PyDocAI — AI-Powered Python Documentation Generator</title>
        <meta name="description" content="Upload your Django project and let AI produce beautiful, comprehensive docs — models, views, endpoints, and more. Free AI documentation generator for Python." />
        <link rel="canonical" href={siteUrl} />
        <meta property="og:title" content="PyDocAI — AI-Powered Python Documentation Generator" />
        <meta property="og:description" content="Upload your Django project and let AI produce beautiful, comprehensive docs — models, views, endpoints, and more." />
        <meta property="og:url" content={siteUrl} />
        <meta name="twitter:title" content="PyDocAI — AI-Powered Python Documentation Generator" />
        <meta name="twitter:description" content="Upload your Django project and let AI produce beautiful, comprehensive docs — models, views, endpoints, and more." />
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>
      <Navbar />

      {/* --- HERO SECTION (Original Soft/Rounded Design) --- */}
      <section id="hero" className="min-h-screen flex items-center justify-center relative overflow-hidden bg-bg-primary border-b border-border">
        <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
        <div className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M60 0v60H0' fill='none' stroke='%233776AB' stroke-width='1'/%3E%3C/svg%3E")`,
            backgroundSize: '60px 60px'
          }}
        />

        <div className="relative z-10 text-center px-6 max-w-5xl mx-auto">
          <h1 className="font-display font-extrabold text-5xl sm:text-6xl md:text-7xl lg:text-8xl leading-none tracking-tight text-ink-primary animate-slide-up">
            <span className="text-accent-blue">Python</span> Docs,<br />
            <span className="text-accent">generated</span>.
          </h1>
          <p className="text-lg md:text-xl text-ink-secondary text-center max-w-2xl mx-auto mt-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
            Upload your Django project and let AI produce beautiful, comprehensive docs — models, views, endpoints, and more.
          </p>
          <div className="flex gap-4 justify-center mt-10 animate-slide-up" style={{ animationDelay: '200ms' }}>
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn-accent text-base">Go to Dashboard →</Link>
            ) : (
              <Link to="/register" className="btn-accent text-base">Start for Free →</Link>
            )}
            <a href="#pipeline" className="btn-ghost text-base">See How It Works</a>
          </div>
          <div className="flex gap-3 mt-8 justify-center flex-wrap animate-slide-up" style={{ animationDelay: '300ms' }}>
            {techBadges.map((badge) => (
              <span key={badge} className="text-xs font-mono text-ink-secondary border border-border rounded-full px-3 py-1 bg-bg-surface shadow-sm">
                {badge}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* --- PIPELINE SECTION (New Technical IDE Design) --- */}
      <section id="pipeline" className="py-24 bg-[#080e17] border-b border-border/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center gap-3 mb-8">
            <IconDatabase className="w-5 h-5 text-accent-blue" />
            <h2 className="font-mono text-sm text-ink-muted uppercase tracking-widest">Execution_Pipeline</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 border border-border rounded-md overflow-hidden bg-bg-surface">
            {pipelineSteps.map((item, idx) => (
              <div key={item.step} className={`p-8 relative ${idx !== pipelineSteps.length - 1 ? 'border-b md:border-b-0 md:border-r border-border' : ''}`}>
                <div className="font-mono text-[10px] text-accent-blue mb-4">
                  <span className="text-ink-muted mr-2">$</span>{item.command}
                </div>
                <h3 className="font-display font-bold text-lg text-ink-primary mb-3">
                  <span className="text-accent mr-2">{item.step}.</span>{item.title}
                </h3>
                <p className="text-ink-secondary text-sm leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- I/O PREVIEW SECTION (New Technical IDE Design) --- */}
      <section className="py-24 bg-bg-primary">
        <div className="max-w-[1400px] mx-auto px-6">
          <div className="flex items-center gap-3 mb-8">
            <IconCode className="w-5 h-5 text-accent" />
            <h2 className="font-mono text-sm text-ink-muted uppercase tracking-widest">I/O_Compilation_Preview</h2>
          </div>

          <div className="border border-border rounded-md bg-[#0b1320] shadow-2xl overflow-hidden flex flex-col lg:flex-row">
            
            {/* Left Pane - Input Code */}
            <div className="w-full lg:w-[45%] flex flex-col border-b lg:border-b-0 lg:border-r border-border">
              <div className="bg-[#080e17] px-4 py-2 border-b border-border flex items-center gap-3">
                <div className="flex gap-1.5 opacity-50 hover:opacity-100 transition-opacity">
                  <div className="w-3 h-3 rounded-full bg-danger"></div>
                  <div className="w-3 h-3 rounded-full bg-warning"></div>
                  <div className="w-3 h-3 rounded-full bg-success"></div>
                </div>
                <span className="text-[11px] font-mono text-ink-muted ml-2">app/models.py</span>
              </div>
              <div className="flex-1 bg-[#080e17]">
                <CodeBlock code={sampleInput} filename="" language="python" />
              </div>
            </div>

            {/* Right Pane - Rendered Output */}
            <div className="w-full lg:w-[55%] flex flex-col bg-[#0b1320]">
              <div className="bg-[#080e17] px-4 py-2 border-b border-border flex items-center">
                <span className="text-[11px] font-mono text-accent-blue border-b border-accent-blue pb-[9px] -mb-[9px]">
                  models.md
                </span>
                <span className="text-[11px] font-mono text-ink-muted ml-6 cursor-not-allowed">
                  endpoints.md
                </span>
              </div>
              <div className="p-8 flex-1 overflow-x-auto">
                <div className="border-l-4 border-accent-blue pl-4 mb-6">
                  <h3 className="font-display font-bold text-2xl text-ink-primary mb-1">Article <span className="text-sm font-mono text-ink-muted font-normal">Model</span></h3>
                  <p className="text-ink-secondary text-sm">
                    Represents a blog article with draft/published workflow. Ordered by creation date descending.
                  </p>
                </div>
                
                <div className="border border-border rounded overflow-hidden">
                  <table className="w-full text-left font-mono text-xs">
                    <thead className="bg-[#080e17] border-b border-border text-ink-muted">
                      <tr>
                        <th className="px-4 py-2 font-normal">Field</th>
                        <th className="px-4 py-2 font-normal">Type</th>
                        <th className="px-4 py-2 font-normal hidden sm:table-cell">Constraints</th>
                        <th className="px-4 py-2 font-normal">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border text-ink-secondary">
                      {sampleFields.map((f) => (
                        <tr key={f.name} className="hover:bg-bg-surface/50">
                          <td className="px-4 py-3 text-accent font-bold">{f.name}</td>
                          <td className="px-4 py-3">{f.type}</td>
                          <td className="px-4 py-3 text-ink-muted hidden sm:table-cell">{f.const}</td>
                          <td className="px-4 py-3">{f.desc}</td>
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

      {/* --- CORE MODULES SECTION (New Technical IDE Design) --- */}
      <section className="py-24 bg-[#080e17] border-t border-border">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center gap-3 mb-8">
            <IconArchive className="w-5 h-5 text-accent" />
            <h2 className="font-mono text-sm text-ink-muted uppercase tracking-widest">System_Capabilities</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-border border border-border rounded-md overflow-hidden">
            {modules.map((m) => (
              <div key={m.title} className="bg-bg-surface p-8 flex items-start gap-5 hover:bg-[#16273d] transition-colors group">
                <div className="mt-1 text-accent border border-accent/20 bg-accent/5 p-2 rounded group-hover:bg-accent/10 transition-colors">
                  <m.icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-mono text-sm font-bold text-ink-primary tracking-wide mb-2">{m.title}</h4>
                  <p className="text-ink-secondary text-sm leading-relaxed">{m.desc}</p>
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