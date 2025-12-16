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
    <div className="flex flex-col gap-2">
      {/* Test Run Header */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-2 mb-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500"></div>
          <h3 className="font-semibold text-gray-200">{run.title}</h3>
        </div>
        <span className="text-xs text-gray-500 font-mono">{run.timestamp}</span>
      </div>

      {/* Steps List */}
      <div className="space-y-2">
        {run.steps.map((step) => (
          <div
            key={step.id}
            className={clsx(
              "border rounded-lg p-4 flex items-center justify-between transition-colors",
              step.status === "fail"
                ? "bg-red-900/10 border-red-900/30 hover:border-red-800/50"
                : "bg-gray-900 border-gray-800 hover:border-gray-700"
            )}
          >
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-3">
                {step.status === "pass" && (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                )}
                {step.status === "fail" && (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                {step.status === "running" && (
                  <Activity className="w-5 h-5 text-blue-500 animate-spin" />
                )}
                {step.status === "pending" && (
                  <Clock className="w-5 h-5 text-gray-600" />
                )}

                <span
                  className={clsx(
                    "font-medium",
                    step.status === "pending"
                      ? "text-gray-500"
                      : "text-gray-200",
                    step.status === "fail" && "text-red-200"
                  )}
                >
                  {step.stepName}
                </span>
              </div>

              {/* Error Message Display */}
              {step.status === "fail" && step.errorMessage && (
                <div className="ml-8 text-xs text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {step.errorMessage}
                </div>
              )}
            </div>

            <div className="flex flex-col items-end gap-1">
              <div className="text-sm font-mono text-gray-500">
                {step.duration}
              </div>
              <div className="text-xs text-gray-600">{step.timestamp}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
