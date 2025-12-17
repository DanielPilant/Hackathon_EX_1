import React from "react";
import { Clock, List, AlertTriangle, Lightbulb } from "lucide-react";
import { ResultItem } from "./ResultItem";
import { GlassCard } from "./ui/GlassCard";
import { AnimatePresence, motion } from "framer-motion";

const FailureCard = ({ run }) => (
  <div className="relative overflow-hidden rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/10 shadow-sm hover:shadow-md transition-all duration-300">
    {/* Left Accent Border */}
    <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-red-500" />

    <div className="p-4 pl-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 bg-red-100 dark:bg-red-900/30 rounded-full">
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
        </div>
        <h3 className="text-sm font-bold text-red-700 dark:text-red-400 uppercase tracking-wide">
          {run.title}
        </h3>
        <span className="ml-auto text-[10px] font-mono text-red-400/70">
          {run.timestamp}
        </span>
      </div>

      {/* Body: Summary & Reason */}
      <div className="space-y-2 mb-4">
        <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 leading-relaxed">
          {run.summary}
        </p>
        {run.reason && (
          <p className="text-xs text-gray-500 dark:text-gray-400 font-mono bg-white/50 dark:bg-black/20 p-2 rounded border border-gray-100 dark:border-white/5">
            {run.reason}
          </p>
        )}
      </div>

      {/* Footer: The Fix */}
      {run.fix && (
        <div className="mt-3 pt-3 border-t border-red-100 dark:border-red-900/30">
          <div className="flex items-start gap-2">
            <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
            <div>
              <span className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">
                Suggested Fix
              </span>
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
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
  return (
    <GlassCard className="h-1/2 p-0 flex flex-col overflow-hidden" delay={0.4}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center gap-2">
        <List className="w-4 h-4 text-gray-500" />
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
          Execution Log
        </h2>
        <span className="ml-auto text-xs text-gray-500 font-medium bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full">
          {testHistory.length} Runs
        </span>
      </div>

      {testHistory.length === 0 && !isRunningTest ? (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 dark:text-gray-600">
          <Clock className="w-8 h-8 mb-3 opacity-20" />
          <p className="text-sm font-medium">No test history available</p>
          <p className="text-xs text-gray-400 mt-1">
            Run a test to see results here
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
          <AnimatePresence mode="popLayout">
            {testHistory.map((run) => (
              <motion.div
                key={run.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
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
