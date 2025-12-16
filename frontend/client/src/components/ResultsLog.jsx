import React from "react";
import { Clock, List } from "lucide-react";
import { ResultItem } from "./ResultItem";
import { Panel } from "./ui/Panel";
import { PanelHeader } from "./ui/PanelHeader";
import { motion, AnimatePresence } from "framer-motion";

export const ResultsLog = ({ testHistory, isRunningTest }) => {
  return (
    <Panel className="w-full h-full flex flex-col overflow-hidden">
      <PanelHeader icon={List} title="Execution Log">
        <span className="ml-auto text-xs text-zinc-500 font-medium bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-full">
          {testHistory.length} Runs
        </span>
      </PanelHeader>

      {testHistory.length === 0 && !isRunningTest ? (
        <div className="flex-1 flex flex-col items-center justify-center text-zinc-600">
          <Clock className="w-8 h-8 mb-3 opacity-20" />
          <p className="text-sm font-medium text-zinc-500">
            No test history available
          </p>
          <p className="text-xs text-zinc-600 mt-1">
            Run a test to see results here
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
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
    </Panel>
  );
};
