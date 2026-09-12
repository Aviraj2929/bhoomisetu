import React from 'react';
import { LayoutDashboard, FileText, CheckSquare, ShieldCheck, Database } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <nav className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="bg-emerald-600 p-2 rounded-lg text-white font-bold">BS</div>
        <div>
          <h1 className="font-bold text-lg text-slate-100 tracking-wide">BhoomiSetu</h1>
          <p className="text-xs text-slate-400">Intelligent Land Record Digitization Portal</p>
        </div>
      </div>

      <div className="flex space-x-2 bg-slate-800 p-1 rounded-lg border border-slate-700">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md text-xs font-semibold transition ${
            activeTab === 'dashboard' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <LayoutDashboard size={16} />
          <span>Dashboard</span>
        </button>

        <button
          onClick={() => setActiveTab('verification')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md text-xs font-semibold transition ${
            activeTab === 'verification' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <CheckSquare size={16} />
          <span>Verification Workspace</span>
        </button>

        <button
          onClick={() => setActiveTab('records')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md text-xs font-semibold transition ${
            activeTab === 'records' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Database size={16} />
          <span>Digitized Records</span>
        </button>
      </div>

      <div className="flex items-center space-x-3 text-xs text-slate-400">
        <span className="bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700">
          User: <strong className="text-slate-200">R. Sharma (Verifier)</strong>
        </span>
      </div>
    </nav>
  );
};
