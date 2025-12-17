import React, { useState } from "react";
import {
  Globe,
  CheckCircle,
  MessageSquare,
  Play,
  Zap,
  Loader2,
  Command,
  Sparkles,
} from "lucide-react";
import clsx from "clsx";
import { GlassCard } from "./ui/GlassCard";
import { GlowButton } from "./ui/GlowButton";

const TargetSection = React.memo(
  ({ targetUrl, setTargetUrl, isConnected, isScanning, onConnect }) => {
    return (
      <div className="space-y-3">
        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <Globe className="w-3.5 h-3.5" /> Target System
        </label>
        <div className="flex gap-2">
          <div className="relative flex-1 group">
            <div className="absolute inset-0 bg-blue-500/20 rounded-xl blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              disabled={isConnected || isScanning}
              placeholder="https://target-system.com"
              className={clsx(
                "relative w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:bg-black/60 transition-all font-mono",
                (isConnected || isScanning) &&
                  "opacity-50 cursor-not-allowed text-slate-400"
              )}
            />
          </div>

          <GlowButton
            onClick={() => onConnect(targetUrl)}
            disabled={isConnected || isScanning || !targetUrl}
            className="min-w-[110px]"
            variant={isConnected ? "success" : "primary"}
          >
            {isConnected ? (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Linked</span>
              </>
            ) : isScanning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Linking</span>
              </>
            ) : (
              "Connect"
            )}
          </GlowButton>
        </div>

        {isConnected && (
          <div className="text-xs text-emerald-400 flex items-center gap-2 font-mono bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20">
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
            UPLINK ESTABLISHED :: {new URL(targetUrl).hostname}
          </div>
        )}
      </div>
    );
  }
);

const DirectiveSection = React.memo(
  ({
    userPrompt,
    setUserPrompt,
    isConnected,
    isSuggesting,
    onGenerateSuggestion,
  }) => {
    const handleSuggestion = async () => {
      const suggestion = await onGenerateSuggestion();
      if (suggestion) {
        setUserPrompt(suggestion);
      }
    };

    return (
      <div className="flex-1 flex flex-col space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <MessageSquare className="w-3.5 h-3.5" /> Directive
          </label>

          {isConnected && (
            <button
              onClick={handleSuggestion}
              disabled={isSuggesting}
              className="flex items-center gap-1.5 text-[10px] font-bold text-purple-400 hover:text-purple-300 transition-colors uppercase tracking-wider disabled:opacity-50"
            >
              {isSuggesting ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Sparkles className="w-3 h-3" />
              )}
              {isSuggesting ? "Thinking..." : "Auto-Suggest"}
            </button>
          )}
        </div>

        <div className="relative flex-1 group">
          <div className="absolute inset-0 bg-purple-500/10 rounded-xl blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            disabled={!isConnected}
            placeholder={
              isConnected
                ? "// Enter test parameters...\n> Verify login functionality\n> Check dashboard metrics"
                : "// Waiting for target connection..."
            }
            className={clsx(
              "relative w-full h-full bg-black/40 border border-white/10 rounded-xl px-4 py-4 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-purple-500/50 focus:bg-black/60 transition-all resize-none font-mono leading-relaxed",
              !isConnected && "opacity-50 cursor-not-allowed"
            )}
          />
        </div>
      </div>
    );
  }
);

export const ControlPanel = ({
  isConnected,
  isScanning,
  isRunningTest,
  isFullScanning,
  isSuggesting,
  onConnect,
  onRunTest,
  onFullScan,
  onGenerateSuggestion,
  className,
}) => {
  const [targetUrl, setTargetUrl] = useState("");
  const [userPrompt, setUserPrompt] = useState("");

  const handleRunTest = () => {
    onRunTest(userPrompt);
  };

  return (
    <GlassCard
      className={clsx("p-6 flex flex-col gap-6", className)}
      delay={0.2}
    >
      {/* Header */}
      <div className="flex items-center gap-2 pb-4 border-b border-white/5">
        <Command className="w-5 h-5 text-blue-400" />
        <h2 className="text-lg font-bold text-white tracking-tight">
          Mission Control
        </h2>
      </div>

      <TargetSection
        targetUrl={targetUrl}
        setTargetUrl={setTargetUrl}
        isConnected={isConnected}
        isScanning={isScanning}
        onConnect={onConnect}
      />

      <DirectiveSection
        userPrompt={userPrompt}
        setUserPrompt={setUserPrompt}
        isConnected={isConnected}
        isSuggesting={isSuggesting}
        onGenerateSuggestion={onGenerateSuggestion}
      />

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 pt-2">
        <GlowButton
          onClick={handleRunTest}
          disabled={!isConnected || isRunningTest || !userPrompt}
          variant="primary"
          icon={Play}
          className="bg-gradient-to-r from-blue-600 to-blue-500 border-0"
        >
          {isRunningTest ? "Executing..." : "Execute"}
        </GlowButton>

        <GlowButton
          onClick={onFullScan}
          disabled={!isConnected || isFullScanning}
          variant="secondary"
          icon={isFullScanning ? Loader2 : Sparkles}
          className={clsx(
            "bg-purple-500/10 hover:bg-purple-500/20 border-purple-500/30 text-purple-300",
            isFullScanning && "animate-pulse"
          )}
        >
          {isFullScanning ? "Scanning..." : "Auto-Scan"}
        </GlowButton>
      </div>
    </GlassCard>
  );
};
