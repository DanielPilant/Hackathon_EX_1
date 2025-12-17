import React, { useState, memo } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Info,
  ChevronDown,
} from "lucide-react";
import clsx from "clsx";

export const ResultItem = memo(({ run }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine overall status from steps
  const isFail = run.steps.some((s) => s.status === "fail");
  const isRunning = run.steps.some((s) => s.status === "running");
  const isInfo = run.steps.every((s) => s.status === "info");

  // Dynamic Styles based on status
  const statusConfig = {
    fail: {
      border: "border-red-200 dark:border-red-900/50",
      bg: "bg-red-50/50 dark:bg-red-950/10",
      icon: XCircle,
      iconColor: "text-red-500",
      glow: "shadow-[0_0_15px_-3px_rgba(239,68,68,0.15)]",
    },
    pass: {
      border: "border-green-200 dark:border-green-900/50",
      bg: "bg-green-50/50 dark:bg-green-950/10",
      icon: CheckCircle2,
      iconColor: "text-green-500",
      glow: "shadow-[0_0_15px_-3px_rgba(34,197,94,0.15)]",
    },
    running: {
      border: "border-blue-200 dark:border-blue-900/50",
      bg: "bg-blue-50/50 dark:bg-blue-950/10",
      icon: Loader2,
      iconColor: "text-blue-500 animate-spin",
      glow: "shadow-[0_0_15px_-3px_rgba(59,130,246,0.15)]",
    },
    info: {
      border: "border-gray-200 dark:border-zinc-800",
      bg: "bg-white dark:bg-zinc-900",
      icon: Info,
      iconColor: "text-gray-400",
      glow: "shadow-sm",
    },
  };

  const currentStatus = isFail
    ? "fail"
    : isRunning
    ? "running"
    : isInfo
    ? "info"
    : "pass";
  const config = statusConfig[currentStatus];
  const StatusIcon = config.icon;

  return (
    <motion.div
      layout
      onClick={() => setIsExpanded(!isExpanded)}
      className={clsx(
        "relative overflow-hidden rounded-xl border transition-all duration-300 group cursor-pointer",
        config.border,
        config.bg,
        config.glow,
        "hover:shadow-md dark:hover:shadow-none"
      )}
    >
      {/* Decorative Side Bar */}
      <div
        className={clsx(
          "absolute left-0 top-0 bottom-0 w-1",
          isFail
            ? "bg-red-500"
            : isRunning
            ? "bg-blue-500"
            : isInfo
            ? "bg-gray-300"
            : "bg-green-500"
        )}
      />

      <div className="p-3 pl-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <StatusIcon className={clsx("w-4 h-4", config.iconColor)} />
            <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              {run.title || "System Event"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-gray-400">
              {run.timestamp}
            </span>
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </motion.div>
          </div>
        </div>

        {/* Steps / Content */}
        <div className="space-y-2">
          {run.steps.map((step) => (
            <div key={step.id} className="flex flex-col gap-1">
              <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-200">
                <span className="leading-relaxed font-medium break-words">
                  {step.stepName}
                </span>
              </div>

              {step.description && (
                <motion.div
                  layout
                  className={clsx(
                    "ml-0 text-xs text-gray-300 bg-zinc-950/50 p-2 rounded border border-white/5 font-mono break-all overflow-hidden",
                    !isExpanded && "line-clamp-2"
                  )}
                >
                  {typeof step.description === "object"
                    ? JSON.stringify(step.description, null, 2)
                    : step.description}
                </motion.div>
              )}

              {step.errorMessage && (
                <div className="mt-1 flex items-start gap-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded break-words">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                  <span>{step.errorMessage}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
});
