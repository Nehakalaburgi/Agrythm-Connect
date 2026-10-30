import React from 'react';
import { Menu, RefreshCw } from 'lucide-react';

export const Header = ({ onToggleSidebar, onRefresh, refreshing, syncStatus, activeTab }) => {
  const getTabTitle = () => {
    switch (activeTab) {
      case 'farmers':
        return 'Farmer Profiles Directory';
      case 'weather':
        return 'District Weather Advisories & Alerts';
      case 'trust_ai':
        return 'Trust AI Verification & Model Integrity';
      case 'sync':
        return 'Google Sheets Sync & Setup';
      case 'overview':
      default:
        return 'Screen C01: Agrythm Connect Call Overview';
    }
  };

  return (
    <header className="w-full bg-white border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 py-3.5 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Left: Mobile Toggle & Active Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            aria-label="Toggle Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold text-slate-900 leading-tight">
                {getTabTitle()}
              </h1>
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold bg-emerald-50 text-trust-green px-2 py-0.5 rounded-full border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-trust-green animate-pulse" />
                Live Sync
              </span>
            </div>
            <p className="text-[11px] font-bold tracking-wider text-slate-500 uppercase">
              Agrythm Connect • Weather Voice Agent System
            </p>
          </div>
        </div>

        {/* Right: Cloud Sync Status & Quick Refresh */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Cloud Sync Status Badge */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200/80 text-xs text-slate-600">
            <span
              className={`w-2 h-2 rounded-full ${syncStatus === 'connected' ? 'bg-trust-green animate-pulse' : 'bg-amber-500'
                }`}
            />
            <span className="font-semibold text-slate-800">
              {syncStatus === 'connected' ? 'Connected (Sheets + SQLite)' : 'Syncing...'}
            </span>
          </div>

          {/* Quick Refresh */}
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors disabled:opacity-50"
            title="Refresh Live Data from Google Sheets"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-trust-navy' : ''}`} />
            <span className="hidden sm:inline">{refreshing ? 'Syncing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
