import React from "react";
import PropTypes from "prop-types";
import { Activity, Cpu, Shield, Zap } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";

export const Sidebar = ({ userId }) => {
  return (
    <GlassCard
      className="w-full flex flex-col h-full border-r-0 rounded-lg"
      delay={0.1}
    >
      <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3">
        <div className="p-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-md border border-gray-200 dark:border-gray-700">
          <Activity className="text-zinc-900 dark:text-white w-5 h-5" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-gray-900 dark:text-white">
            TestFlow
          </h1>
          <p className="text-[10px] text-gray-500 font-medium tracking-wide">
            AI AGENT
          </p>
        </div>
      </div>

      <div className="p-4 flex-1 flex flex-col gap-2">
        <div className="flex items-center gap-3 text-xs font-medium text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-3 py-2 rounded-md border border-green-200 dark:border-green-900/30 mb-4">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          <span className="tracking-wide">SYSTEM ONLINE</span>
        </div>

        <div className="space-y-1">
          <div className="px-2 py-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            Modules
          </div>
          <div className="flex items-center gap-3 px-2 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-md transition-colors cursor-pointer">
            <Cpu className="w-4 h-4" />
            <span>Core Engine</span>
          </div>
          <div className="flex items-center gap-3 px-2 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-md transition-colors cursor-pointer">
            <Shield className="w-4 h-4" />
            <span>Security</span>
          </div>
          <div className="flex items-center gap-3 px-2 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-md transition-colors cursor-pointer">
            <Zap className="w-4 h-4" />
            <span>Performance</span>
          </div>
        </div>

        <div className="mt-auto">
          <div className="px-2 py-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
            Session
          </div>
          <div className="px-3 py-2 bg-gray-50 dark:bg-zinc-800/50 rounded-md border border-gray-200 dark:border-gray-800 font-mono text-[10px] text-gray-500 break-all">
            {userId || "Initializing..."}
          </div>
        </div>
      </div>

      <div className="p-4 text-[10px] text-gray-400 text-center border-t border-gray-200 dark:border-gray-800">
        v0.1.0 Alpha
      </div>
    </GlassCard>
  );
};

Sidebar.propTypes = {
  userId: PropTypes.string,
};
