import React, { useState } from "react";
import { Globe, CheckCircle, Terminal, Play, Zap, Loader2 } from "lucide-react";
import clsx from "clsx";
import { Panel } from "./ui/Panel";
import { PanelHeader } from "./ui/PanelHeader";
import { Button } from "./ui/Button";

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
    <Panel className="w-full h-full">
      <PanelHeader icon={Terminal} title="Control Center" />

      <div className="p-4 flex flex-col gap-6 h-full overflow-y-auto custom-scrollbar">
        {/* URL Section */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-zinc-400 flex items-center gap-2">
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
                  "w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all",
                  (isConnected || isScanning) && "opacity-50 cursor-not-allowed"
                )}
              />
            </div>

            <Button
              onClick={handleConnect}
              disabled={isConnected || isScanning || !targetUrl}
              className="min-w-[90px]"
              variant={isConnected ? "secondary" : "primary"}
            >
              {isConnected ? (
                <CheckCircle className="w-4 h-4 text-emerald-500" />
              ) : isScanning ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Connect"
              )}
            </Button>
          </div>

          {isConnected && (
            <div className="text-xs text-emerald-500 flex items-center gap-1.5 font-medium">
              <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
              Connected successfully
            </div>
          )}
        </div>

        {/* Prompt Section */}
        <div className="flex-1 flex flex-col space-y-2">
          <label className="text-xs font-medium text-zinc-400 flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5" /> Test Instructions
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
                "w-full h-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none font-mono",
                !isConnected && "opacity-50 cursor-not-allowed"
              )}
            />
            {isConnected && (
              <div className="absolute bottom-3 right-3 text-[10px] text-zinc-500 font-medium pointer-events-none bg-zinc-900/80 px-1.5 py-0.5 rounded border border-zinc-800">
                Press ⌘ + Enter to run
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-3 pt-4 border-t border-zinc-800">
          <Button
            onClick={handleRunTest}
            disabled={
              isRunningTest || isFullScanning || !isConnected || !userPrompt
            }
            variant="primary"
            icon={isRunningTest ? Loader2 : Play}
            className="w-full"
          >
            {isRunningTest ? "Running Test..." : "Run Test"}
          </Button>

          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-zinc-800"></div>
            <span className="flex-shrink-0 mx-3 text-zinc-600 text-[10px] font-medium uppercase tracking-wider">
              Automated Analysis
            </span>
            <div className="flex-grow border-t border-zinc-800"></div>
          </div>

          <Button
            onClick={onFullScan}
            disabled={isRunningTest || isFullScanning || !isConnected}
            variant="secondary"
            icon={isFullScanning ? Loader2 : Zap}
            className="w-full"
          >
            {isFullScanning ? "Scanning..." : "Full Audit"}
          </Button>
        </div>
      </div>
    </Panel>
  );
};
