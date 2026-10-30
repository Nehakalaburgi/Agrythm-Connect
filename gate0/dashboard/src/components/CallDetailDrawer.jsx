import React, { useState, useEffect } from 'react';
import { 
  X, 
  Play, 
  Pause, 
  Volume2, 
  CloudRain, 
  Thermometer, 
  Wind, 
  Droplets, 
  Phone, 
  MapPin, 
  MessageSquare
} from 'lucide-react';

import { maskPhoneNumber } from '../utils';

export const CallDetailDrawer = ({ call, onClose }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackTime, setPlaybackTime] = useState(0);
  const [activeCallId, setActiveCallId] = useState(call?.call_id);

  // Sync internal state when a different call is selected
  if (call && call.call_id !== activeCallId) {
    setActiveCallId(call.call_id);
    setIsPlaying(false);
    setPlaybackTime(0);
  }

  // Audio timer simulation
  useEffect(() => {
    let interval = null;
    const dur = parseInt(call?.duration_sec, 10) || 60;
    if (isPlaying) {
      interval = setInterval(() => {
        setPlaybackTime((prev) => {
          if (prev >= dur) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, call]);

  if (!call) return null;

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const durationSec = parseInt(call.duration_sec, 10) || 60;
  const progressPercent = Math.min(100, Math.round((playbackTime / durationSec) * 100));

  const rawTranscript = call.transcript_preview || call.transcript || '';

  return (
    <>
      {/* Backdrop */}
      <div 
        onClick={onClose}
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 transition-opacity"
      />

      {/* Drawer Container */}
      <aside className="fixed top-0 right-0 bottom-0 z-50 w-full max-w-2xl bg-white shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-sm text-slate-900">
                {call.call_id}
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                {call.displayDateTime || call.call_timestamp || 'Active Call'}
              </span>
            </div>
            <p className="text-[11px] font-bold tracking-wider text-slate-500 uppercase mt-0.5">
              Call Inspection & Post-Call Telemetry
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5 md:p-6 space-y-6">
          {/* Farmer Profile Card */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
              Farmer Profile
            </span>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-2">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-trust-navy text-white flex items-center justify-center font-bold text-base shadow-xs">
                  {(call.farmer_name || 'F').charAt(0)}
                </div>
                <div>
                  <h4 className="text-base font-bold text-slate-900">
                    {call.farmer_name || 'Unassigned'}
                  </h4>
                  <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                    <span className="flex items-center gap-1">
                      <Phone className="w-3 h-3 text-slate-400" />
                      <span className="font-mono">{maskPhoneNumber(call?.phone_number || call?.phone)}</span>
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-400" />
                      {call.village || 'N/A'}, {call.district || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`px-2.5 py-1 rounded-xl text-xs font-bold border ${
                    call.primary_language === 'English'
                      ? 'bg-blue-50 text-blue-700 border-blue-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}
                >
                  {call.primary_language === 'English' ? 'English' : 'Hindi'}
                </span>
                <span className="px-2.5 py-1 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-trust-green">
                  {call.farmer_id || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Interactive Audio Player & Simulated Waveform */}
          <div className="p-5 rounded-2xl bg-trust-navy text-white space-y-3 shadow-md">
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span className="text-[10px] font-bold tracking-wider uppercase text-slate-300">
                Voice Call Recording & Synthesis Stream
              </span>
              <span className="font-mono text-xs text-emerald-400 font-bold">
                {formatTimer(playbackTime)} / {formatTimer(durationSec)}
              </span>
            </div>

            {/* Audio Waveform Bars */}
            <div className="flex items-center gap-1 h-10 py-1">
              {[40, 65, 80, 50, 95, 70, 30, 85, 100, 60, 45, 90, 75, 40, 85, 95, 60, 70, 90, 50, 40, 65, 80, 50, 95, 70, 30, 85, 100, 60].map((h, i) => {
                const isActive = (i / 30) * 100 <= progressPercent;
                return (
                  <div
                    key={i}
                    className={`flex-1 rounded-full transition-all duration-150 ${
                      isActive ? 'bg-emerald-400' : 'bg-slate-600/60'
                    }`}
                    style={{
                      height: isPlaying ? `${Math.max(20, (h * (Math.sin(playbackTime + i) * 0.3 + 0.8)))}%` : `${h}%`,
                    }}
                  />
                );
              })}
            </div>

            {/* Playback Controls */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="w-10 h-10 rounded-full bg-emerald-500 hover:bg-emerald-400 text-trust-navy flex items-center justify-center font-bold transition-transform active:scale-95 shadow-md cursor-pointer"
                >
                  {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
                </button>
                <div className="text-xs">
                  <div className="font-semibold text-white">Post-Call Audio Stream</div>
                  <div className="text-[10px] text-slate-300">Duration: {durationSec} seconds</div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-300">
                <Volume2 className="w-4 h-4" />
                <span className="font-mono text-[11px] bg-white/10 px-2 py-0.5 rounded">1.0x</span>
              </div>
            </div>
          </div>

          {/* Weather Advisory Delivered */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                Weather Advisory Grounding
              </span>
              {call.call_status === 'skipped' ? (
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                  <CloudRain className="w-3.5 h-3.5 text-slate-400" />
                  Skipped
                </span>
              ) : (
                <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  <CloudRain className="w-3.5 h-3.5 text-emerald-600" />
                  Live Grounded ({call.weather_source || 'Open-Meteo'})
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  <Thermometer className="w-3 h-3 text-amber-500" />
                  Temperature
                </span>
                <div className="font-bold text-slate-900 mt-1">{call.temperature || 'N/A'}</div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  <CloudRain className="w-3 h-3 text-blue-500" />
                  Rain Chance
                </span>
                <div className="font-bold text-slate-900 mt-1">{call.rainfall_chance || 'N/A'}</div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  <Droplets className="w-3 h-3 text-cyan-500" />
                  Humidity
                </span>
                <div className="font-bold text-slate-900 mt-1">{call.humidity || 'N/A'}</div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  <Wind className="w-3 h-3 text-slate-500" />
                  Wind Speed
                </span>
                <div className="font-bold text-slate-900 mt-1">{call.wind || 'N/A'}</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-blue-50/60 border border-blue-100 text-xs text-slate-700 leading-relaxed">
              <strong className="text-trust-navy block mb-1">Forecast: {call.weather_forecast || 'General Weather'}</strong>
              {call?.message_text || call?.advisory_summary || 'No spoken message recorded'}
            </div>
          </div>

          {/* Dialog Transcript from Sheet */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                Dialog Transcript ({call.primary_language === 'English' ? 'English' : 'Hindi'})
              </span>
            </div>

            {rawTranscript ? (
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans">
                {rawTranscript}
              </div>
            ) : (
              <div className="p-6 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-slate-400 text-xs">
                <MessageSquare className="w-5 h-5 mx-auto mb-1.5 text-slate-400" />
                No transcript preview provided in the database for this call.
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
