import React from "react";
import { Monitor, Play } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";

export const VideoPlayer = () => {
  return (
    <GlassCard
      className="w-full h-full p-0 flex flex-col overflow-hidden"
      delay={0.3}
    >
      <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center gap-2">
        <Monitor className="w-4 h-4 text-gray-500" />
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
          Live Preview
        </h2>
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gray-300 dark:bg-gray-600" />
          <span className="text-xs text-gray-500 font-medium">Offline</span>
        </div>
      </div>

      <div className="flex-1 bg-gray-100 dark:bg-zinc-950 flex items-center justify-center relative">
        <div className="text-center">
          <div className="w-12 h-12 bg-white dark:bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-3 border border-gray-200 dark:border-gray-700 shadow-sm">
            <Play className="w-5 h-5 text-gray-400 dark:text-gray-500 ml-0.5" />
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
            No active session
          </p>
        </div>
      </div>
    </GlassCard>
  );
};
