import React, { useState } from "react";
import {
  Globe,
  CheckCircle,
  Activity,
  MessageSquare,
  Play,
  Zap,
  Loader2,
} from "lucide-react";
import clsx from "clsx";
import { GlassCard } from "./ui/GlassCard";
import { GlowButton } from "./ui/GlowButton";

export const ControlPanel = ({
  isConnected,
  isScanning,
  isRunningTest,
  isFullScanning,
  onConnect,
  onRunTest,
  onFullScan,
}) => {
  const [targetUrl, setTargetUrl] = useState("");
  const [userPrompt, setUserPrompt] = useState("");

  const handleConnect = () => {
    onConnect(targetUrl);
  };

  const handleRunTest = () => {
    onRunTest(userPrompt);
  };

  return (
    <GlassCard className="w-1/3 p-6 flex flex-col gap-8" delay={0.2}>
      {/* URL Section */}
      <div className="space-y-3">
        <label className="text-sm font-bold text-blue-600 dark:text-blue-300 uppercase tracking-wider flex items-center gap-2 transition-colors duration-300">
          <Globe className="w-4 h-4" /> Target Interface
        </label>
        <div className="flex gap-2">
          <div className="relative flex-1 group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl opacity-20 group-hover:opacity-50 transition duration-500 blur"></div>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              disabled={isConnected || isScanning}
              placeholder="https://target-system.com"
              className={clsx(
                "relative w-full bg-white dark:bg-black/50 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-mono text-sm",
                (isConnected || isScanning) && "opacity-50 cursor-not-allowed"
              )}
            />
          </div>

          <GlowButton
            onClick={handleConnect}
            disabled={isConnected || isScanning || !targetUrl}
            className={clsx(
              "min-w-[100px]",
              isConnected
                ? "bg-emerald-600 hover:bg-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.4)]"
                : ""
            )}
          >
            {isConnected ? (
              <CheckCircle className="w-5 h-5" />
            ) : isScanning ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              "Connect"
            )}
          </GlowButton>
        </div>

        {isConnected && (
          <div className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2 font-mono animate-pulse transition-colors duration-300">
            <span className="w-1.5 h-1.5 bg-emerald-500 dark:bg-emerald-400 rounded-full"></span>
            UPLINK ESTABLISHED
          </div>
        )}
      </div>

      {/* Prompt Section */}
      <div className="flex-1 flex flex-col space-y-3">
        <label className="text-sm font-bold text-purple-600 dark:text-purple-300 uppercase tracking-wider flex items-center gap-2 transition-colors duration-300">
          <MessageSquare className="w-4 h-4" /> Directive Input
        </label>
        <div className="relative flex-1 group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-blue-500 rounded-xl opacity-20 group-hover:opacity-40 transition duration-500 blur"></div>
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            disabled={!isConnected}
            placeholder={
              isConnected
                ? "// Enter natural language test parameters..."
                : "// Awaiting target connection..."
            }
            className={clsx(
              "relative w-full h-full bg-white dark:bg-black/50 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-4 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all font-mono text-sm resize-none",
              !isConnected && "opacity-50 cursor-not-allowed"
            )}
          />
        </div>
      </div>

      <div className="flex flex-col gap-4 pt-4 border-t border-gray-200 dark:border-white/5 transition-colors duration-300">
        <GlowButton
          onClick={handleRunTest}
          disabled={
            isRunningTest || isFullScanning || !isConnected || !userPrompt
          }
          variant="primary"
          icon={isRunningTest ? Loader2 : Play}
          className={isRunningTest ? "animate-pulse" : ""}
        >
          {isRunningTest ? "EXECUTING PROTOCOL..." : "INITIATE TEST SEQUENCE"}
        </GlowButton>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-gray-200 dark:border-white/10 transition-colors duration-300"></div>
          <span className="flex-shrink-0 mx-4 text-gray-400 dark:text-gray-600 text-[10px] uppercase tracking-widest transition-colors duration-300">
            System Override
          </span>
          <div className="flex-grow border-t border-gray-200 dark:border-white/10 transition-colors duration-300"></div>
        </div>

        <GlowButton
          onClick={onFullScan}
          disabled={isRunningTest || isFullScanning || !isConnected}
          variant="secondary"
          icon={isFullScanning ? Loader2 : Zap}
          className={isFullScanning ? "animate-pulse" : ""}
        >
          {isFullScanning ? "SCANNING NETWORK..." : "FULL SYSTEM AUDIT"}
        </GlowButton>
      </div>
    </GlassCard>
  );
};
