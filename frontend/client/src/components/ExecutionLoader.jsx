import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Scan, Activity, Target } from "lucide-react";

const LOADING_TEXTS = [
  "NEURAL LINK ACTIVE",
  "SCANNING DOM NODES",
  "ANALYZING VIEWPORT",
  "EXECUTING PROTOCOL",
  "VERIFYING SELECTORS",
  "AWAITING LLM RESPONSE",
];

export const ExecutionLoader = () => {
  const [textIndex, setTextIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTextIndex((prev) => (prev + 1) % LOADING_TEXTS.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 pointer-events-none overflow-hidden"
    >
      {/* 1. Active HUD Border (Pulsing) */}
      <motion.div
        animate={{ opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="absolute inset-0 border-[2px] border-blue-500/30 shadow-[inset_0_0_30px_rgba(59,130,246,0.1)]"
      />

      {/* 2. Corner Brackets (The "Targeting" Look) */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-blue-400 rounded-tl-lg" />
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-blue-400 rounded-tr-lg" />
      <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-blue-400 rounded-bl-lg" />
      <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-blue-400 rounded-br-lg" />

      {/* 3. Subtle Scanner Line (Laser Sweep) */}
      <motion.div
        initial={{ top: "-10%" }}
        animate={{ top: "110%" }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-400/50 to-transparent shadow-[0_0_10px_rgba(59,130,246,0.3)]"
      />

      {/* 4. Status Badge (Top-Right HUD) */}
      <div className="absolute top-4 right-4 flex items-center gap-3">
        {/* Blinking Red Recording Dot */}
        <motion.div
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
          className="flex items-center gap-1.5 bg-red-500/10 border border-red-500/20 px-2 py-1 rounded-md backdrop-blur-md"
        >
          <div className="w-1.5 h-1.5 bg-red-500 rounded-full shadow-[0_0_5px_#ef4444]" />
          <span className="text-[10px] font-mono font-bold text-red-400 tracking-wider">
            REC
          </span>
        </motion.div>

        {/* Main Status Pill */}
        <div className="flex items-center gap-3 bg-black/60 border border-blue-500/20 px-3 py-1.5 rounded-md backdrop-blur-md shadow-lg">
          <Activity className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <div className="w-[140px] relative h-4 overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={textIndex}
                initial={{ y: 15, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -15, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="absolute inset-0 flex items-center"
              >
                <span className="text-[10px] font-mono font-bold text-blue-100 tracking-widest truncate">
                  {LOADING_TEXTS[textIndex]}
                </span>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* 5. Center Crosshair (Very subtle) */}
      <div className="absolute inset-0 flex items-center justify-center opacity-20">
        <Target className="w-12 h-12 text-blue-300 stroke-[0.5]" />
      </div>
    </motion.div>
  );
};
