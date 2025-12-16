import React from "react";
import { Activity } from "lucide-react";

export const Sidebar = ({ userId }) => {
  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      <div className="p-6 border-b border-gray-700 flex items-center gap-3">
        <Activity className="text-blue-500 w-6 h-6" />
        <h1 className="text-xl font-bold tracking-tight">TestFlow AI</h1>
      </div>
      <div className="p-4 flex-1">
        <div className="flex items-center gap-2 text-sm text-green-400 bg-green-400/10 px-3 py-2 rounded-md border border-green-400/20">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          System Connected
        </div>
        <div className="mt-4 text-xs text-gray-500">
          Session ID: <span className="font-mono text-gray-400">{userId}</span>
        </div>
      </div>
      <div className="p-4 text-xs text-gray-500 text-center">v0.1.0 Alpha</div>
    </aside>
  );
};
