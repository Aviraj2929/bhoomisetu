import React, { useState } from 'react';
import { LayoutDashboard, CheckSquare, Database } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TABS = [
  { id: 'dashboard', label: 'Dashboard', hi: 'डैशबोर्ड', icon: LayoutDashboard },
  { id: 'verification', label: 'Verification Workspace', hi: 'सत्यापन कक्ष', icon: CheckSquare },
  { id: 'records', label: 'Digitized Records', hi: 'डिजिटल अभिलेख', icon: Database },
];

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const [hindi, setHindi] = useState(false);

  const setTextSize = (px: number) => {
    document.documentElement.style.fontSize = `${px}px`;
  };

  return (
    <header>
      {/* Tricolour strip */}
      <div className="flex h-1.5" aria-hidden="true">
        <div className="flex-1 bg-saffron" />
        <div className="flex-1 bg-white border-y border-line" />
        <div className="flex-1 bg-india-green" />
      </div>

      {/* Accessibility bar */}
      <div className="bg-navy-dark text-white text-xs">
        <div className="max-w-7xl mx-auto px-4 py-1.5 flex flex-wrap items-center justify-between gap-2">
          <a href="#main-content" className="hover:underline">Skip to main content</a>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1" role="group" aria-label="Text size">
              <button onClick={() => setTextSize(14)} className="px-1.5 border border-white/40 hover:bg-white/10" aria-label="Decrease text size">A-</button>
              <button onClick={() => setTextSize(16)} className="px-1.5 border border-white/40 hover:bg-white/10" aria-label="Normal text size">A</button>
              <button onClick={() => setTextSize(18)} className="px-1.5 border border-white/40 hover:bg-white/10" aria-label="Increase text size">A+</button>
            </div>
            <button
              onClick={() => setHindi(h => !h)}
              className="px-2 border border-white/40 hover:bg-white/10"
              aria-pressed={hindi}
            >
              {hindi ? 'English' : 'हिन्दी'}
            </button>
          </div>
        </div>
      </div>

      {/* Title band */}
      <div className="bg-white border-b-2 border-navy">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4">
            {/* Placeholder emblem – replace with your own approved logo */}
            <div className="w-14 h-14 rounded-full border-2 border-navy flex items-center justify-center text-navy font-bold text-lg bg-navy-light" aria-hidden="true">
              भूसे
            </div>
            <div>
              <h1 className="text-2xl font-bold text-navy leading-tight">
                भूमिसेतु <span className="text-ink font-normal">|</span> BhoomiSetu
              </h1>
              <p className="text-sm text-ink">
                {hindi ? 'भूमि अभिलेख डिजिटलीकरण एवं सत्यापन पोर्टल' : 'Land Records Digitization and Validation Portal'}
              </p>
            </div>
          </div>
          <div className="text-sm text-right border-l-4 border-saffron pl-3">
            <p className="text-ink">Logged in as</p>
            <p className="font-semibold text-navy">R. Sharma (Verifier)</p>
          </div>
        </div>
      </div>

      {/* Navigation bar */}
      <nav className="bg-navy" aria-label="Main navigation">
        <ul className="max-w-7xl mx-auto px-4 flex flex-wrap">
          {TABS.map(t => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <li key={t.id}>
                <button
                  onClick={() => setActiveTab(t.id)}
                  aria-current={active ? 'page' : undefined}
                  className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold text-white border-b-4 ${
                    active ? 'border-saffron bg-navy-dark' : 'border-transparent hover:bg-navy-dark'
                  }`}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{hindi ? t.hi : t.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
};
