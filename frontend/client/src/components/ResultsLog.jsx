import React from "react";
import { Clock, List } from "lucide-react";
import { ResultItem } from "./ResultItem";
import { GlassCard } from "./ui/GlassCard";
import { motion, AnimatePresence } from "framer-motion";

export const ResultsLog = ({ testHistory, isRunningTest }) => {
  return (
    <GlassCard
      className="w-full h-full p-0 flex flex-col overflow-hidden"
      delay={0.4}
    >
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
                <ResultItem run={run} />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </GlassCard>
  );
};
