import React from "react";
import { Activity, Play } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";

export const VideoPlayer = () => {
  return (
    <GlassCard className="h-1/2 p-6 flex flex-col" delay={0.3}>
      <h2 className="text-sm font-bold text-blue-600 dark:text-blue-300 uppercase tracking-wider mb-4 flex items-center gap-2 transition-colors duration-300">
        <Activity className="w-4 h-4" /> Live Execution Feed
      </h2>
      <div className="flex-1 bg-gray-900 dark:bg-black/80 rounded-xl border border-gray-200 dark:border-white/10 flex items-center justify-center relative overflow-hidden group shadow-inner transition-colors duration-300">
        {/* Placeholder for Video Player */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-blue-900/20 to-transparent opacity-50"></div>

        <div className="text-center z-10">
          <div className="w-20 h-20 bg-white/10 dark:bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform border border-white/10 backdrop-blur-sm shadow-[0_0_30px_rgba(59,130,246,0.2)]">
            <Play className="w-8 h-8 text-blue-400 ml-1" />
          </div>
          <p className="text-blue-200/50 font-mono text-sm tracking-widest">
            AWAITING SIGNAL...
          </p>
        </div>

        {/* Decorative Corner Accents */}
        <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-blue-500/30 rounded-tl-lg"></div>
        <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-blue-500/30 rounded-tr-lg"></div>
        <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-blue-500/30 rounded-bl-lg"></div>
        <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-blue-500/30 rounded-br-lg"></div>
      </div>
    </GlassCard>
  );
};
