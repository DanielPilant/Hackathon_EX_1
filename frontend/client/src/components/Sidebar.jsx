import React from "react";
import { Activity, Cpu, Shield, Zap } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";

export const Sidebar = ({ userId }) => {
  return (
    <GlassCard className="w-72 flex flex-col h-full border-r-0" delay={0.1}>
      <div className="p-6 border-b border-gray-200 dark:border-white/10 flex items-center gap-3 bg-gray-50/50 dark:bg-white/5 transition-colors duration-300">
        <div className="p-2 bg-blue-500/10 dark:bg-blue-500/20 rounded-lg border border-blue-500/20 dark:border-blue-500/30">
          <Activity className="text-blue-600 dark:text-blue-400 w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-white transition-colors duration-300">
            TestFlow AI
          </h1>
          <p className="text-xs text-blue-600/70 dark:text-blue-300/70 font-mono transition-colors duration-300">
            AUTONOMOUS AGENT
          </p>
        </div>
      </div>

      <div className="p-6 flex-1 flex flex-col gap-6">
        <div className="flex items-center gap-3 text-sm text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-4 py-3 rounded-xl border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)] transition-colors duration-300">
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-ping absolute inset-0" />
            <div className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 relative z-10" />
          </div>
          <span className="font-medium tracking-wide">SYSTEM ONLINE</span>
        </div>

        <div className="space-y-4">
          <div className="text-xs font-bold text-gray-500 dark:text-gray-500 uppercase tracking-widest">
            Modules
          </div>
          <div className="flex items-center gap-3 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors cursor-pointer group">
            <Cpu className="w-5 h-5 text-blue-600 dark:text-blue-500 group-hover:text-blue-500 dark:group-hover:text-blue-400" />
            <span>Core Engine</span>
          </div>
          <div className="flex items-center gap-3 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors cursor-pointer group">
            <Shield className="w-5 h-5 text-purple-600 dark:text-purple-500 group-hover:text-purple-500 dark:group-hover:text-purple-400" />
            <span>Security Protocol</span>
          </div>
          <div className="flex items-center gap-3 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors cursor-pointer group">
            <Zap className="w-5 h-5 text-yellow-600 dark:text-yellow-500 group-hover:text-yellow-500 dark:group-hover:text-yellow-400" />
            <span>Performance Metrics</span>
          </div>
        </div>

        <div className="mt-auto">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">
            Session Context
          </div>
          <div className="p-3 bg-black/40 rounded-lg border border-white/5 font-mono text-xs text-gray-400 break-all">
            {userId || "Initializing..."}
          </div>
        </div>
      </div>

      <div className="p-4 text-[10px] text-gray-600 text-center border-t border-white/5 uppercase tracking-widest">
        v0.1.0 Alpha Build
      </div>
    </GlassCard>
  );
};
