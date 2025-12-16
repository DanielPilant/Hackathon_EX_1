import React from "react";
import PropTypes from "prop-types";
import { Activity, Cpu, Shield, Zap, LayoutGrid } from "lucide-react";
import { Panel } from "./ui/Panel";

export const Sidebar = ({ userId }) => {
  return (
    <Panel className="w-full flex flex-col h-full border-r-0 rounded-lg">
      <div className="p-4 border-b border-zinc-800 flex items-center gap-3">
        <div className="p-1.5 bg-zinc-900 rounded-md border border-zinc-800">
          <LayoutGrid className="text-zinc-100 w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-zinc-100">
            TestFlow
          </h1>
          <p className="text-[10px] text-zinc-500 font-medium tracking-wide">
            AI AGENT
          </p>
        </div>
      </div>

      <div className="p-2 flex-1 flex flex-col gap-1">
        <div className="flex items-center gap-3 text-xs font-medium text-emerald-500 bg-emerald-500/10 px-3 py-2 rounded-md border border-emerald-500/20 mb-4 mx-2 mt-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="tracking-wide">SYSTEM ONLINE</span>
        </div>

        <div className="space-y-0.5 px-2">
          <div className="px-2 py-2 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">
            Modules
          </div>
          <div className="flex items-center gap-3 px-2 py-2 text-sm text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50 rounded-md transition-colors cursor-pointer">
            <Cpu className="w-4 h-4" />
            <span>Core Engine</span>
          </div>
          <div className="flex items-center gap-3 px-2 py-2 text-sm text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50 rounded-md transition-colors cursor-pointer">
            <Shield className="w-4 h-4" />
            <span>Security</span>
          </div>
          <div className="flex items-center gap-3 px-2 py-2 text-sm text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50 rounded-md transition-colors cursor-pointer">
            <Zap className="w-4 h-4" />
            <span>Performance</span>
          </div>
        </div>

        <div className="mt-auto px-2 pb-2">
          <div className="px-2 py-2 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">
            Session
          </div>
          <div className="px-3 py-2 bg-zinc-900 rounded-md border border-zinc-800 font-mono text-[10px] text-zinc-500 break-all">
            {userId || "Initializing..."}
          </div>
        </div>
      </div>

      <div className="p-3 text-[10px] text-zinc-600 text-center border-t border-zinc-800">
        v0.1.0 Alpha
      </div>
    </Panel>
  );
};

Sidebar.propTypes = {
  userId: PropTypes.string,
};
