import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import CodeBlock from '../components/CodeBlock'
import { IconBolt, IconBrain, IconTable, IconLink, IconRocket, IconArchive } from '../components/Icons'

const howItWorks = [
  {
    step: '01',
    title: 'Upload Your Code',
    desc: 'Drop your Django project files, paste code snippets, or connect a Git repository. We handle the rest.',
  },
  {
    step: '02',
    title: 'AI Analyzes Everything',
    desc: 'Our engine parses models, views, serializers, URLs, and tests to understand your project architecture.',
  },
  {
    step: '03',
    title: 'Get Documentation',
    desc: 'Receive beautifully structured docs with field tables, endpoint specs, and code examples — ready to share.',
  },
]

const features = [
  { icon: IconBolt, title: 'Instant Generation', desc: 'Upload and get results in seconds, not hours of manual writing.' },
  { icon: IconBrain, title: 'AI-Powered Analysis', desc: 'Deep understanding of Django patterns including models, views, serializers, and URL routing.' },
  { icon: IconTable, title: 'Field Tables', desc: 'Auto-generated tables for model fields with types, constraints, and descriptions.' },
  { icon: IconLink, title: 'API Endpoints', desc: 'Full REST API documentation with methods, parameters, and response examples.' },
  { icon: IconRocket, title: 'Beautiful Output', desc: 'Clean, structured docs with syntax highlighting and a professional layout.' },
  { icon: IconArchive, title: 'Multiple Inputs', desc: 'Upload files, paste code, or connect a Git repository — your workflow, your choice.' },
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
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
        ],
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title`

const sampleFields = [
  { name: 'title', type: 'CharField', constraints: 'max_length=200', desc: 'The article headline' },
  { name: 'slug', type: 'SlugField', constraints: 'unique=True', desc: 'URL-friendly identifier' },
  { name: 'content', type: 'TextField', constraints: '—', desc: 'Full article body' },
  { name: 'author', type: 'ForeignKey → User', constraints: 'CASCADE', desc: 'Article author reference' },
  { name: 'status', type: 'CharField', constraints: 'choices, default=draft', desc: 'Publication status' },
  { name: 'created_at', type: 'DateTimeField', constraints: 'auto_now_add', desc: 'Creation timestamp' },
  { name: 'updated_at', type: 'DateTimeField', constraints: 'auto_now', desc: 'Last update timestamp' },
]

const techBadges = ['Django', 'DRF', 'Python 3.x', 'REST APIs', 'Models', 'Serializers', 'Views', 'URLs']

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()

  // useEffect(() => {
  //   if (!isLoading && isAuthenticated) {
  //     navigate('/input', { replace: true })
  //   }
  // }, [isAuthenticated, isLoading, navigate])

  if (isLoading) return null
  return (
    <div className="relative z-10">
      <Navbar />

      {/* ── Hero Section ────────────────────────────── */}
      <section id="hero" className="min-h-screen flex items-center justify-center relative overflow-hidden bg-bg-primary">
        {/* Radial glow */}
        <div className="absolute inset-0 bg-radial-glow pointer-events-none" />
        {/* Grid lines */}
        <div className="absolute inset-0 opacity-5 pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M60 0v60H0' fill='none' stroke='%237c6af7' stroke-width='0.5'/%3E%3C/svg%3E")`,
            backgroundSize: '60px 60px'
          }}
        />

        <div className="relative z-10 text-center px-6 max-w-5xl mx-auto">
          <h1 className="font-display font-extrabold text-5xl sm:text-6xl md:text-7xl lg:text-8xl leading-none tracking-tight text-ink-primary animate-slide-up">
            Documentation,<br />
            <span className="text-accent">generated</span>.
          </h1>
          <p className="text-lg md:text-xl text-ink-secondary text-center max-w-2xl mx-auto mt-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
            Upload your Django project and let AI produce beautiful, comprehensive docs — models, views, endpoints, and more.
          </p>
          <div className="flex gap-4 justify-center mt-10 animate-slide-up" style={{ animationDelay: '200ms' }}>
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn-accent text-base">
                Go to Dashboard →
              </Link>
            ) : (
              <Link to="/register" className="btn-accent text-base">
                Start for Free →
              </Link>
            )}
            <a href="#how-it-works" className="btn-ghost text-base">
              See How It Works
            </a>
          </div>
          <div className="flex gap-3 mt-8 justify-center flex-wrap animate-slide-up" style={{ animationDelay: '300ms' }}>
            {techBadges.map((badge) => (
              <span key={badge} className="text-xs font-mono text-ink-secondary border border-border rounded-full px-3 py-1 bg-bg-surface">
                {badge}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ────────────────────────────── */}
      <section id="how-it-works" className="py-32 bg-bg-primary">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="section-title text-4xl text-center mb-16">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {howItWorks.map((item) => (
              <div key={item.step} className="glass-card p-8 hover:-translate-y-1 hover:shadow-glow transition-all duration-300 group">
                <span className="font-display font-bold text-6xl text-accent/20 group-hover:text-accent/40 transition-colors">
                  {item.step}
                </span>
                <h3 className="font-display font-bold text-xl mt-4 mb-2 text-ink-primary">{item.title}</h3>
                <p className="text-ink-secondary text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Live Example ────────────────────────────── */}
      <section id="live-example" className="py-32 bg-bg-surface/50">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="section-title text-4xl text-center mb-16">See It in Action</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* Input panel */}
            <div>
              <p className="text-xs font-mono text-ink-muted uppercase tracking-widest mb-3">Input — models.py</p>
              <CodeBlock code={sampleInput} filename="models.py" language="python" />
            </div>
            {/* Output panel */}
            <div>
              <p className="text-xs font-mono text-ink-muted uppercase tracking-widest mb-3">Output — Generated Docs</p>
              <div className="glass-card p-8">
                <h3 className="font-display font-bold text-2xl text-ink-primary mb-1">Article</h3>
                <p className="text-ink-secondary text-sm mb-6">
                  Represents a blog article with draft/published workflow. Ordered by creation date descending.
                </p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-bg-surface">
                      <th className="text-left font-display font-bold text-ink-secondary text-xs uppercase tracking-widest py-2 px-3">Field</th>
                      <th className="text-left font-display font-bold text-ink-secondary text-xs uppercase tracking-widest py-2 px-3">Type</th>
                      <th className="text-left font-display font-bold text-ink-secondary text-xs uppercase tracking-widest py-2 px-3 hidden sm:table-cell">Constraints</th>
                      <th className="text-left font-display font-bold text-ink-secondary text-xs uppercase tracking-widest py-2 px-3">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sampleFields.map((f) => (
                      <tr key={f.name} className="border-t border-border">
                        <td className="py-2 px-3 font-mono text-accent text-xs">{f.name}</td>
                        <td className="py-2 px-3 text-ink-primary">{f.type}</td>
                        <td className="py-2 px-3 text-ink-muted hidden sm:table-cell">{f.constraints}</td>
                        <td className="py-2 px-3 text-ink-secondary">{f.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features Grid ────────────────────────────── */}
      <section id="features" className="py-32 max-w-6xl mx-auto px-6">
        <h2 className="section-title text-4xl text-center mb-16">Why PyDocAI?</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <div key={f.title} className="glass-card p-6 hover:border-accent/50 transition-all duration-200">
              <span className="text-accent mb-3 block">
                <f.icon className="w-7 h-7" />
              </span>
              <h3 className="font-display font-bold text-ink-primary mb-1">{f.title}</h3>
              <p className="text-ink-secondary text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </div>
  )
}
