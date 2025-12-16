import React from "react";
import { CheckCircle, Clock, Terminal } from "lucide-react";
import { ResultItem } from "./ResultItem";
import { GlassCard } from "./ui/GlassCard";
import { motion, AnimatePresence } from "framer-motion";

export const ResultsLog = ({ testHistory, isRunningTest }) => {
  return (
    <GlassCard className="h-1/2 p-6 flex flex-col overflow-hidden" delay={0.4}>
      <h2 className="text-sm font-bold text-emerald-600 dark:text-emerald-300 uppercase tracking-wider mb-4 flex items-center gap-2 transition-colors duration-300">
        <Terminal className="w-4 h-4" /> System Logs
      </h2>

      {testHistory.length === 0 && !isRunningTest ? (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 dark:text-gray-500/50 transition-colors duration-300">
          <Clock className="w-12 h-12 mb-2 opacity-20" />
          <p className="font-mono text-sm">NO DATA AVAILABLE</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto pr-2 space-y-6 custom-scrollbar">
          <AnimatePresence mode="popLayout">
            {testHistory.map((run) => (
              <motion.div
                key={run.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3 }}
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
