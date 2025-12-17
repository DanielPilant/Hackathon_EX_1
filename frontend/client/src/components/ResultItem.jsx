import React, { useState, memo } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Info,
  ChevronDown,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
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
      border: "border-red-500/30",
      bg: "bg-red-500/5",
      icon: XCircle,
      iconColor: "text-red-400",
      glow: "shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:shadow-[0_0_20px_rgba(239,68,68,0.2)]",
      accent: "bg-red-500",
    },
    pass: {
      border: "border-emerald-500/30",
      bg: "bg-emerald-500/5",
      icon: CheckCircle2,
      iconColor: "text-emerald-400",
      glow: "shadow-[0_0_15px_rgba(16,185,129,0.1)] hover:shadow-[0_0_20px_rgba(16,185,129,0.2)]",
      accent: "bg-emerald-500",
    },
    running: {
      border: "border-blue-500/30",
      bg: "bg-blue-500/5",
      icon: Loader2,
      iconColor: "text-blue-400 animate-spin",
      glow: "shadow-[0_0_15px_rgba(59,130,246,0.1)] hover:shadow-[0_0_20px_rgba(59,130,246,0.2)]",
      accent: "bg-blue-500",
    },
    info: {
      border: "border-slate-700/50",
      bg: "bg-slate-800/20",
      icon: Info,
      iconColor: "text-slate-400",
      glow: "shadow-none hover:bg-slate-800/30",
      accent: "bg-slate-500",
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
        "relative overflow-hidden rounded-xl border transition-all duration-300 group cursor-pointer backdrop-blur-sm",
        config.border,
        config.bg,
        config.glow
      )}
    >
      {/* Decorative Side Bar with Glow */}
      <div
        className={clsx(
          "absolute left-0 top-0 bottom-0 w-1 shadow-[0_0_8px_currentColor]",
          config.accent
        )}
      />

      <div className="p-3 pl-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <StatusIcon className={clsx("w-4 h-4", config.iconColor)} />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              {run.title || "System Event"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-slate-500">
              {run.timestamp}
            </span>
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </motion.div>
          </div>
        </div>

        {/* Steps / Content */}
        <div className="space-y-2">
          {run.steps.map((step) => (
            <div key={step.id} className="flex flex-col gap-1">
              <div className="flex items-start gap-2 text-sm text-slate-300">
                <span className="leading-relaxed font-medium break-words">
                  {step.stepName}
                </span>
              </div>

              {step.description && (
                <motion.div
                  layout
                  className={clsx(
                    "ml-0 text-xs text-slate-400 bg-black/40 p-2 rounded border border-white/5 font-mono break-all overflow-hidden",
                    !isExpanded && "line-clamp-2"
                  )}
                >
                  {typeof step.description === "object"
                    ? JSON.stringify(step.description, null, 2)
                    : step.description}
                </motion.div>
              )}

              {step.errorMessage && (
                <div className="mt-1 flex items-start gap-2 text-xs text-red-300 bg-red-500/10 p-2 rounded break-words border border-red-500/20">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-red-400" />
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
