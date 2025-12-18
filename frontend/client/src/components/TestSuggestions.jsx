import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldAlert,
  MousePointerClick,
  Lightbulb,
  Scan,
  Loader2,
  Zap,
} from "lucide-react";
import clsx from "clsx";
import { backend } from "../services/backend";

export const TestSuggestions = ({ sessionId, onSelectSuggestion }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);
    setSuggestions([]);

    try {
      const data = await backend.getPageSuggestions(sessionId);

      // Log the raw JSON to the terminal for debugging
      await backend.logToTerminal({
        type: "DEEP_SCAN_RESULTS",
        count: data?.length || 0,
        suggestions: data,
      });

      setSuggestions(data || []);
    } catch (err) {
      console.error("Scan failed:", err);
      setError("Failed to generate test suggestions.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0 bg-black/20 rounded-xl border border-white/5 overflow-hidden backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-white/5 bg-white/5">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-bold text-blue-100 uppercase tracking-wider">
            Test Suggestions
          </span>
        </div>
        <button
          onClick={handleScan}
          disabled={isLoading || !sessionId}
          className={clsx(
            "flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
            isLoading || !sessionId
              ? "text-slate-500 cursor-not-allowed"
              : "text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
          )}
        >
          {isLoading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Scan className="w-3 h-3" />
          )}
          {isLoading ? "Scanning..." : "Deep Scan"}
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar relative">
        <AnimatePresence mode="popLayout">
          {/* Empty State */}
          {!isLoading && suggestions.length === 0 && !error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-full text-center p-4 opacity-50"
            >
              <Lightbulb className="w-8 h-8 text-slate-600 mb-2" />
              <p className="text-xs text-slate-500">
                No risks detected yet.
                <br />
                Run a Deep Scan to analyze the current page.
              </p>
            </motion.div>
          )}

          {/* Error State */}
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs"
            >
              {error}
            </motion.div>
          )}

          {/* Loading Skeleton */}
          {isLoading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="h-24 rounded-lg bg-white/5 animate-pulse border border-white/5"
                />
              ))}
            </div>
          )}

          {/* Suggestions List */}
          {suggestions.map((suggestion, index) => (
            <motion.button
              key={suggestion.id || index}
              layout
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              onClick={() => onSelectSuggestion(suggestion.description)}
              className="w-full text-left group relative p-4 rounded-xl bg-black/40 border border-white/10 hover:border-blue-500/50 hover:bg-blue-900/10 transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(59,130,246,0.15)]"
            >
              {/* Glow Effect */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-500/0 via-blue-500/0 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

              <div className="relative z-10">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <h3 className="text-sm font-bold text-blue-300 group-hover:text-blue-200 transition-colors leading-tight">
                    {suggestion.title}
                  </h3>
                  <MousePointerClick className="w-4 h-4 text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
                </div>

                <p className="text-xs text-slate-400 group-hover:text-slate-300 leading-relaxed line-clamp-3">
                  {suggestion.description}
                </p>

                <div className="mt-3 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform translate-y-2 group-hover:translate-y-0">
                  <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    Apply Test
                  </span>
                </div>
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};
