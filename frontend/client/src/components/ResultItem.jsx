import React from "react";
import {
  CheckCircle,
  XCircle,
  Activity,
  Clock,
  AlertCircle,
} from "lucide-react";
import clsx from "clsx";

export const ResultItem = ({ run }) => {
  return (
    <div className="flex flex-col gap-3">
      {/* Test Run Header */}
      <div className="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-blue-500"></div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            {run.title}
          </h3>
        </div>
        <span className="text-xs text-gray-400 font-medium">
          {run.timestamp}
        </span>
      </div>

      {/* Steps List */}
      <div className="space-y-2">
        {run.steps.map((step, index) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className={clsx(
              "group flex items-start justify-between p-3 rounded-md border transition-all",
              step.status === "fail"
                ? "bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30"
                : "bg-white dark:bg-zinc-900 border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700"
            )}
          >
            <div className="flex flex-col gap-1.5 w-full">
              <div className="flex items-center gap-3">
                {step.status === "pass" && (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                )}
                {step.status === "fail" && (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
                {step.status === "running" && (
                  <Activity className="w-4 h-4 text-blue-500 animate-spin" />
                )}
                {step.status === "pending" && (
                  <Clock className="w-4 h-4 text-gray-300 dark:text-gray-600" />
                )}

                <span
                  className={clsx(
                    "text-sm font-medium",
                    step.status === "pending"
                      ? "text-gray-400 dark:text-gray-500"
                      : "text-gray-700 dark:text-gray-200",
                    step.status === "fail" && "text-red-700 dark:text-red-400"
                  )}
                >
                  {step.stepName}
                </span>

                <div className="ml-auto text-xs text-gray-400 font-mono">
                  {step.duration}
                </div>
              </div>

              {/* Error Message Display */}
              {step.status === "fail" && step.errorMessage && (
                <div className="ml-7 mt-1 text-xs text-red-600 dark:text-red-400 flex items-start gap-1.5 bg-white dark:bg-black/20 p-2 rounded border border-red-100 dark:border-red-900/30">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                  <span className="leading-relaxed">{step.errorMessage}</span>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
