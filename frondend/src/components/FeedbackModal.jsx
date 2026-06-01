import { useState } from "react";
import api from "../api";

const CATEGORIES = [
  { value: "general",      label: "General" },
  { value: "docs_quality", label: "Docs Quality" },
  { value: "ui_ux",        label: "UI / UX" },
  { value: "performance",  label: "Performance" },
  { value: "bug",          label: "Bug Report" },
  { value: "feature",      label: "Feature Request" },
];

export default function FeedbackModal({ onClose, projectId = null }) {
  const [category, setCategory] = useState("general");
  const [message,  setMessage]  = useState("");
  const [sent,     setSent]     = useState(false);
  const [err,      setErr]      = useState("");

  const submit = async (e) => {
    e.preventDefault();
    if (!message.trim()) { setErr("Please write a message."); return; }
    try {
      await api.post("/feedback/", { category, message, project: projectId });
      setSent(true);
    } catch {
      setErr("Could not submit feedback. Try again.");
    }
  };

  return (
    <div className="glass-card p-8 w-full border-border/80">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-display font-bold text-ink-primary">Share Your Feedback</h3>
      </div>
      
      {sent ? (
        <div className="text-center py-8">
          <div className="text-5xl mb-4">🎉</div>
          <h3 className="text-xl font-bold text-ink-primary mb-2">Thank you for your feedback!</h3>
          <p className="text-ink-secondary mb-6 text-sm">We read every submission and use it to improve PyDocAI.</p>
          <button onClick={() => { setSent(false); setMessage(""); onClose(); }} className="btn-accent text-sm py-2">
            View History Logs
          </button>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-ink-secondary mb-2">Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)}
              className="w-full bg-bg-surface border border-border rounded-xl px-4 py-3 text-sm text-ink-primary focus:outline-none focus:border-accent">
              {CATEGORIES.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-secondary mb-2">Message</label>
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Tell us what you think…"
              rows={5}
              required
              className="w-full bg-bg-surface border border-border rounded-xl px-4 py-3 text-sm text-ink-primary placeholder-ink-muted focus:outline-none focus:border-accent resize-none"
            />
          </div>

          {err && <p className="text-red-400 text-sm font-mono">{err}</p>}
          <button type="submit" className="btn-accent w-full text-sm !py-3">Submit Feedback</button>
        </form>
      )}
    </div>
  );
}