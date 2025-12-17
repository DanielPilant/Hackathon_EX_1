import React from "react";
import { Clock, List, AlertTriangle, Lightbulb, Terminal } from "lucide-react";
import { ResultItem } from "./ResultItem";
import { GlassCard } from "./ui/GlassCard";
import { AnimatePresence, motion } from "framer-motion";

const FailureCard = ({ run }) => (
  <div className="relative overflow-hidden rounded-xl border border-red-500/30 bg-red-500/5 shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:shadow-[0_0_25px_rgba(239,68,68,0.2)] transition-all duration-300 group">
    {/* Left Accent Border with Glow */}
    <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-500 shadow-[0_0_10px_#ef4444]" />

    <div className="p-4 pl-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="p-1.5 bg-red-500/10 rounded-lg border border-red-500/20">
          <AlertTriangle className="w-4 h-4 text-red-400" />
        </div>
        <h3 className="text-sm font-bold text-red-100 uppercase tracking-wider font-mono">
          {run.title}
        </h3>
        <span className="ml-auto text-[10px] font-mono text-red-400/50 border border-red-500/10 px-2 py-1 rounded">
          {run.timestamp}
        </span>
      </div>

      {/* Body: Summary & Reason */}
      <div className="space-y-3 mb-4">
        <p className="text-sm text-slate-300 leading-relaxed font-light">
          {run.summary}
        </p>
        {run.reason && (
          <div className="relative">
            <div className="absolute inset-0 bg-red-500/5 blur-sm rounded-lg" />
            <p className="relative text-xs text-red-200/80 font-mono bg-black/40 p-3 rounded-lg border border-red-500/10">
              <span className="text-red-500 mr-2">::</span>
              {run.reason}
            </p>
          </div>
        )}
      </div>

      {/* Footer: The Fix */}
      {run.fix && (
        <div className="mt-3 pt-3 border-t border-red-500/10">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 p-1 bg-amber-500/10 rounded-full">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-amber-500/80 uppercase tracking-widest block mb-1.5">
                Recommended Protocol
              </span>
              <p className="text-sm text-slate-300 leading-relaxed">
                {run.fix}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  </div>
);

export const ResultsLog = ({ testHistory, isRunningTest }) => {
  console.log("🎨 Rendering Log List. Items count:", testHistory.length); // <--- Junction C: Render Log

  return (
    <GlassCard className="h-1/2 p-0 flex flex-col overflow-hidden" delay={0.4}>
      <div className="p-4 border-b border-white/5 flex items-center gap-3 bg-white/5 backdrop-blur-md">
        <Terminal className="w-4 h-4 text-blue-400" />
        <h2 className="text-sm font-bold text-white tracking-wide uppercase">
          Execution Log
        </h2>
        <span className="ml-auto text-[10px] font-mono text-blue-300/70 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full">
          {testHistory.length} ENTRIES
        </span>
      </div>

      {testHistory.length === 0 && !isRunningTest ? (
        <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-white/5">
            <Clock className="w-8 h-8 opacity-50" />
          </div>
          <p className="text-sm font-medium text-slate-400">System Idle</p>
          <p className="text-xs text-slate-600 mt-1 font-mono">
            Waiting for test execution...
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          <AnimatePresence mode="popLayout">
            {testHistory.map((run) => (
              <motion.div
                key={run.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                {run.type === "failure_card" ? (
                  <FailureCard run={run} />
                ) : (
                  <ResultItem run={run} />
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </GlassCard>
  );
};
