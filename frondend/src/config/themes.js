import { IconBook, IconCode } from '../components/Icons'

export const MODES = {
  python: {
    id: 'python',
    label: 'Python Doc',
    tagline: 'Python only',
    desc: 'AST-parsed, full documentation for Python and Django projects.',
    icon: IconCode,
    symbol: '{ }',
    gradient: 'from-blue-950 via-blue-900 to-slate-950',
    bg: 'bg-blue-950',
    bgSurface: 'bg-blue-900/40',
    bgElevated: 'bg-blue-800/30',
    border: 'border-blue-500/40',
    accent: 'text-blue-400',
    accentBg: 'bg-blue-500',
    accentBgHover: 'bg-blue-400',
    accentBgSoft: 'bg-blue-500/10',
    glow: '0 0 30px rgba(59,130,246,0.15)',
    primary: '#3B82F6',
    primaryDim: 'rgba(59,130,246,0.1)',
    tabActive: 'bg-blue-500/10 text-blue-400',
    tabInactive: 'text-blue-300/50',
    btn: 'bg-blue-500 hover:bg-blue-400 text-white',
  },
  universal: {
    id: 'universal',
    label: 'Universal Doc',
    tagline: 'Full detailed',
    desc: 'Comprehensive documentation for any language or framework.',
    icon: IconBook,
    symbol: '\u2200',
    gradient: 'from-emerald-950 via-emerald-900 to-slate-950',
    bg: 'bg-emerald-950',
    bgSurface: 'bg-emerald-900/40',
    bgElevated: 'bg-emerald-800/30',
    border: 'border-emerald-500/40',
    accent: 'text-emerald-400',
    accentBg: 'bg-emerald-500',
    accentBgHover: 'bg-emerald-400',
    accentBgSoft: 'bg-emerald-500/10',
    glow: '0 0 30px rgba(16,185,129,0.15)',
    primary: '#10B981',
    primaryDim: 'rgba(16,185,129,0.1)',
    tabActive: 'bg-emerald-500/10 text-emerald-400',
    tabInactive: 'text-emerald-300/50',
    btn: 'bg-emerald-500 hover:bg-emerald-400 text-white',
  },

}

export function getMode(id) {
  return MODES[id] || MODES.universal
}
