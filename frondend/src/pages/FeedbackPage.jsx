import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import FeedbackModal from '../components/FeedbackModal';
import MyFeedbackView from './MyFeedback'; // Refactored from your file

export default function FeedbackPage() {
  const [activeTab, setActiveTab] = useState('give'); // 'give' or 'history'

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Helmet>
        <title>Feedback — PyDocAI</title>
        <meta name="description" content="Submit feedback about PyDocAI's documentation quality, UI/UX, performance, or request new features." />
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <Navbar />
      
      <header className="bg-bg-primary/80 backdrop-blur-xl border-b border-border/40 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/dashboard" className="text-ink-secondary hover:text-ink-primary text-sm font-medium transition-colors">
            ← Back to Dashboard
          </Link>
          <h1 className="text-2xl font-display font-bold text-ink-primary">Feedback Hub</h1>
        </div>
      </header>

      <main className="flex-1 max-w-4xl w-full mx-auto py-8 px-6 flex flex-col">
        {/* Toggle Switch Tabs */}
        <div className="flex gap-6 border-b border-border/60 mb-8 text-sm font-mono">
          <button
            onClick={() => setActiveTab('give')}
            className={`pb-3 font-bold transition-all relative ${
              activeTab === 'give' ? 'text-accent' : 'text-ink-muted hover:text-ink-secondary'
            }`}
          >
            Give Feedback
            {activeTab === 'give' && <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-accent" />}
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`pb-3 font-bold transition-all relative ${
              activeTab === 'history' ? 'text-accent' : 'text-ink-muted hover:text-ink-secondary'
            }`}
          >
            My Feedback History
          </button>
        </div>

        {/* Dynamic Display Rendering */}
        <div className="flex-1">
          {activeTab === 'give' ? (
            <div className="max-w-xl mx-auto w-full">
              {/* Removed internal onClose redirect since it lives directly on-page now */}
              <FeedbackModal onClose={() => setActiveTab('history')} />
            </div>
          ) : (
            <MyFeedbackView />
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}