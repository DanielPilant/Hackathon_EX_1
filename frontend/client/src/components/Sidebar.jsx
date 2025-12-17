import React from "react";
import PropTypes from "prop-types";
import {
  Activity,
  Cpu,
  Shield,
  Zap,
  Terminal,
  Database,
  Globe,
} from "lucide-react";
import { GlassCard } from "./ui/GlassCard";

export const Sidebar = ({ userId }) => {
  return (
    <GlassCard
      className="w-72 flex flex-col h-full border-r-0 rounded-3xl"
      delay={0.1}
    >
      {/* Header */}
      <div className="p-6 border-b border-white/10 flex items-center gap-4">
        <div className="relative p-2 bg-blue-500/10 rounded-xl border border-blue-500/20">
          <Activity className="text-blue-400 w-6 h-6" />
          <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full opacity-50" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            TestFlow
          </h1>
          <p className="text-[10px] text-blue-400 font-medium tracking-[0.2em] uppercase">
            AI Command Center
          </p>
        </div>
      </div>

      {/* Status Indicator */}
      <div className="p-6 pb-2">
        <div className="flex items-center gap-3 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-4 py-3 rounded-xl border border-emerald-500/20 shadow-[0_0_15px_-3px_rgba(16,185,129,0.2)]">
          <div className="relative w-2 h-2">
            <div className="absolute inset-0 rounded-full bg-emerald-500 animate-ping opacity-75" />
            <div className="relative w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <span className="tracking-wide">SYSTEM ONLINE</span>
        </div>
      </div>

      {/* Navigation Modules */}
      <div className="p-4 flex-1 flex flex-col gap-1">
        <div className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          Core Modules
        </div>

        {[
          { icon: Cpu, label: "Neural Engine", active: true },
          { icon: Globe, label: "Browser Link", active: false },
          { icon: Terminal, label: "Live Console", active: false },
          { icon: Database, label: "Test Data", active: false },
          { icon: Shield, label: "Security Audit", active: false },
        ].map((item, i) => (
          <div
            key={i}
            className={`group flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-300 cursor-pointer ${
              item.active
                ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
            }`}
          >
            <item.icon
              className={`w-4 h-4 transition-transform duration-300 group-hover:scale-110 ${
                item.active
                  ? "text-blue-400"
                  : "text-slate-500 group-hover:text-slate-300"
              }`}
            />
            <span>{item.label}</span>
            {item.active && (
              <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400 shadow-[0_0_10px_rgba(96,165,250,0.5)]" />
            )}
          </div>
        ))}
      </div>

      {/* Session Info */}
      <div className="p-6 mt-auto border-t border-white/5">
        <div className="px-1 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">
          Active Session
        </div>
        <div className="px-4 py-3 bg-black/40 rounded-xl border border-white/5 font-mono text-[10px] text-slate-400 break-all shadow-inner">
          <span className="text-blue-500 mr-2">$</span>
          {userId || "Initializing..."}
        </div>
        <div className="mt-4 text-[10px] text-slate-600 text-center font-mono">
          v2.0.0-beta • build.8942
        </div>
      </div>
    </GlassCard>
  );
};

Sidebar.propTypes = {
  userId: PropTypes.string,
};
