import React, { useState } from "react";
import {
  Globe,
  CheckCircle,
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
    <GlassCard className="w-full h-full p-6 flex flex-col gap-6" delay={0.2}>
      {/* URL Section */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <Globe className="w-3.5 h-3.5" /> Target URL
        </label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              disabled={isConnected || isScanning}
              placeholder="https://example.com"
              className={clsx(
                "w-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-gray-800 rounded-md px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all",
                (isConnected || isScanning) &&
                  "opacity-50 cursor-not-allowed bg-gray-50 dark:bg-zinc-800"
              )}
            />
          </div>

          <GlowButton
            onClick={handleConnect}
            disabled={isConnected || isScanning || !targetUrl}
            className="min-w-[90px]"
          >
            {isConnected ? (
              <CheckCircle className="w-4 h-4" />
            ) : isScanning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Connect"
            )}
          </GlowButton>
        </div>

        {isConnected && (
          <div className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1.5 font-medium">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
            Connected successfully
          </div>
        )}
      </div>

      {/* Prompt Section */}
      <div className="flex-1 flex flex-col space-y-2">
        <label className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <MessageSquare className="w-3.5 h-3.5" /> Test Instructions
        </label>
        <div className="relative flex-1">
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            disabled={!isConnected}
            placeholder={
              isConnected
                ? "Describe the test scenario (e.g., 'Log in as admin and check the dashboard')..."
                : "Connect to a target URL to start testing..."
            }
            className={clsx(
              "w-full h-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-gray-800 rounded-md px-3 py-3 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none",
              !isConnected &&
                "opacity-50 cursor-not-allowed bg-gray-50 dark:bg-zinc-800"
            )}
          />
        </div>
      </div>

      <div className="flex flex-col gap-3 pt-4 border-t border-gray-200 dark:border-gray-800">
        <GlowButton
          onClick={handleRunTest}
          disabled={
            isRunningTest || isFullScanning || !isConnected || !userPrompt
          }
          variant="primary"
          icon={isRunningTest ? Loader2 : Play}
        >
          {isRunningTest ? "Running Test..." : "Run Test"}
        </GlowButton>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-gray-200 dark:border-gray-800"></div>
          <span className="flex-shrink-0 mx-3 text-gray-400 text-[10px] font-medium uppercase tracking-wider">
            Automated Analysis
          </span>
          <div className="flex-grow border-t border-gray-200 dark:border-gray-800"></div>
        </div>

        <GlowButton
          onClick={onFullScan}
          disabled={isRunningTest || isFullScanning || !isConnected}
          variant="secondary"
          icon={isFullScanning ? Loader2 : Zap}
        >
          {isFullScanning ? "Scanning..." : "Full Audit"}
        </GlowButton>
      </div>
    </GlassCard>
  );
};
