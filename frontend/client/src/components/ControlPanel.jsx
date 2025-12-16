import React, { useState } from "react";
import {
  Globe,
  CheckCircle,
  Activity,
  MessageSquare,
  Play,
  Zap,
} from "lucide-react";
import clsx from "clsx";

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
    <div className="w-1/3 p-6 border-r border-gray-700 flex flex-col gap-6 bg-gray-900/50">
      {/* URL Section */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
          <Globe className="w-4 h-4" /> Target Website URL
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            disabled={isConnected || isScanning}
            placeholder="https://example.com"
            className={clsx(
              "flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all",
              (isConnected || isScanning) && "opacity-50 cursor-not-allowed"
            )}
          />
          <button
            onClick={handleConnect}
            disabled={isConnected || isScanning || !targetUrl}
            className={clsx(
              "px-4 rounded-lg font-bold text-sm flex items-center justify-center transition-all",
              isConnected
                ? "bg-green-600 text-white cursor-default"
                : "bg-blue-600 hover:bg-blue-500 text-white",
              (isScanning || !targetUrl) &&
                !isConnected &&
                "opacity-50 cursor-not-allowed"
            )}
          >
            {isConnected ? (
              <CheckCircle className="w-5 h-5" />
            ) : isScanning ? (
              <Activity className="w-5 h-5 animate-spin" />
            ) : (
              "Scan"
            )}
          </button>
        </div>
        {isConnected && (
          <div className="mt-2 text-xs text-green-400 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" /> Connected to Brain
          </div>
        )}
      </div>

      {/* Prompt Section */}
      <div className="flex-1 flex flex-col">
        <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
          <MessageSquare className="w-4 h-4" /> Test Instructions
        </label>
        <textarea
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          disabled={!isConnected}
          placeholder={
            isConnected
              ? "Describe your test case..."
              : "Please connect to a URL first."
          }
          className={clsx(
            "w-full flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none transition-all",
            !isConnected && "opacity-50 cursor-not-allowed"
          )}
        />
      </div>

      <div className="flex flex-col gap-3">
        <button
          onClick={handleRunTest}
          disabled={
            isRunningTest || isFullScanning || !isConnected || !userPrompt
          }
          className={clsx(
            "w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-2 transition-all",
            isRunningTest || isFullScanning || !isConnected || !userPrompt
              ? "bg-gray-700 text-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20"
          )}
        >
          {isRunningTest ? (
            <>
              <Activity className="w-5 h-5 animate-spin" /> Processing Prompt...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" /> Run Autonomous Test
            </>
          )}
        </button>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-gray-700"></div>
          <span className="flex-shrink-0 mx-4 text-gray-500 text-xs uppercase tracking-wider">
            Or
          </span>
          <div className="flex-grow border-t border-gray-700"></div>
        </div>

        <button
          onClick={onFullScan}
          disabled={isRunningTest || isFullScanning || !isConnected}
          className={clsx(
            "w-full py-3 rounded-lg font-bold text-md flex items-center justify-center gap-2 transition-all border border-purple-500/30",
            isRunningTest || isFullScanning || !isConnected
              ? "bg-gray-800 text-gray-500 cursor-not-allowed"
              : "bg-purple-900/20 hover:bg-purple-900/40 text-purple-300 hover:text-purple-200"
          )}
        >
          {isFullScanning ? (
            <>
              <Activity className="w-5 h-5 animate-spin" /> Scanning Entire
              Site...
            </>
          ) : (
            <>
              <Zap className="w-5 h-5" /> Run Full Site QA Scan
            </>
          )}
        </button>
      </div>
    </div>
  );
};
