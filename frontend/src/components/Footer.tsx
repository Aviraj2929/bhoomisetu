import React from 'react';

export const Footer: React.FC = () => (
  <footer className="mt-auto">
    <div className="flex h-1.5" aria-hidden="true">
      <div className="flex-1 bg-saffron" />
      <div className="flex-1 bg-white" />
      <div className="flex-1 bg-india-green" />
    </div>
    <div className="bg-navy-dark text-white text-sm">
      <div className="max-w-7xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-3">
        <ul className="flex flex-wrap gap-x-5 gap-y-1">
          <li><a href="#main-content" className="hover:underline">Help</a></li>
          <li><a href="#main-content" className="hover:underline">Contact Us</a></li>
          <li><a href="#main-content" className="hover:underline">Terms &amp; Conditions</a></li>
          <li><a href="#main-content" className="hover:underline">Privacy Policy</a></li>
        </ul>
        <p className="text-white/80">
          Last updated: {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
        </p>
      </div>
      <div className="border-t border-white/20 text-center text-xs text-white/70 py-2 px-4">
        BhoomiSetu – Land Records Digitization and Validation Portal. Content is owned and maintained by the project team.
      </div>
    </div>
  </footer>
);
