import React from "react";
import {
  CheckCircle,
  XCircle,
  Activity,
  Clock,
  AlertCircle,
} from "lucide-react";
import clsx from "clsx";
import { motion } from "framer-motion";

export const ResultItem = ({ run }) => {
  return (
    <div className="flex flex-col gap-2">
      {/* Test Run Header */}
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-white/10 pb-2 mb-2 transition-colors duration-300">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
          <h3 className="font-bold text-gray-900 dark:text-blue-100 tracking-wide transition-colors duration-300">
            {run.title}
          </h3>
        </div>
        <span className="text-[10px] text-gray-500 dark:text-blue-300/50 font-mono uppercase tracking-widest transition-colors duration-300">
          {run.timestamp}
        </span>
      </div>

      {/* Steps List */}
      <div className="space-y-2">
        {run.steps.map((step, index) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={clsx(
              "border rounded-lg p-3 flex items-center justify-between transition-all duration-300",
              step.status === "fail"
                ? "bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-500/30 hover:bg-red-100 dark:hover:bg-red-900/20"
                : "bg-white dark:bg-white/5 border-gray-200 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/10 hover:border-gray-300 dark:hover:border-white/20"
            )}
          >
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-3">
                {step.status === "pass" && (
                  <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
                )}
                {step.status === "fail" && (
                  <XCircle className="w-4 h-4 text-red-600 dark:text-red-400 drop-shadow-[0_0_8px_rgba(248,113,113,0.6)]" />
                )}
                {step.status === "running" && (
                  <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin" />
                )}
                {step.status === "pending" && (
                  <Clock className="w-4 h-4 text-gray-400 dark:text-gray-600" />
                )}

                <span
                  className={clsx(
                    "font-medium text-sm transition-colors duration-300",
                    step.status === "pending"
                      ? "text-gray-400 dark:text-gray-500"
                      : "text-gray-700 dark:text-gray-200",
                    step.status === "fail" && "text-red-700 dark:text-red-200"
                  )}
                >
                  {step.stepName}
                </span>
              </div>

              {/* Error Message Display */}
              {step.status === "fail" && step.errorMessage && (
                <div className="ml-7 text-xs text-red-600/80 dark:text-red-300/80 flex items-center gap-1 font-mono bg-red-50 dark:bg-red-950/30 p-1 rounded border border-red-200 dark:border-red-500/20 transition-colors duration-300">
                  <AlertCircle className="w-3 h-3" />
                  {step.errorMessage}
                </div>
              )}
            </div>

            <div className="flex flex-col items-end gap-1">
              <div className="text-xs font-mono text-gray-500 dark:text-gray-500 transition-colors duration-300">
                {step.duration}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
