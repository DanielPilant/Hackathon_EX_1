import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Cpu, Activity, Radio, ScanLine, Loader2 } from "lucide-react";

const LOADING_TEXTS = [
  "Initializing Neural Link...",
  "Scanning DOM Structure...",
  "Analyzing Visual Context...",
  "Executing Test Protocols...",
  "Verifying Selectors...",
  "Processing LLM Response...",
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
      className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm rounded-2xl"
    >
      {/* Main Card */}
      <div className="relative w-80 p-8 rounded-2xl bg-black/90 border border-white/10 shadow-2xl overflow-hidden flex flex-col items-center gap-6">
        {/* Background Gradients */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-50" />
        <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-purple-500 to-transparent opacity-50" />

        {/* Scanner Line Animation */}
        <motion.div
          animate={{ top: ["0%", "100%", "0%"] }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
          className="absolute left-0 w-full h-[2px] bg-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.5)] z-0 pointer-events-none"
        />

        {/* Central Icon with Pulse */}
        <div className="relative z-10">
          <motion.div
            animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute inset-0 bg-blue-500 rounded-full blur-xl"
          />
          <div className="relative w-16 h-16 bg-black rounded-full border border-blue-500/30 flex items-center justify-center shadow-[0_0_30px_rgba(59,130,246,0.2)]">
            <Cpu className="w-8 h-8 text-blue-400" />
          </div>

          {/* Orbiting Dot */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className="absolute inset-[-6px] rounded-full border-t-2 border-transparent border-t-blue-500/50"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
            className="absolute inset-[-12px] rounded-full border-b-2 border-transparent border-b-purple-500/30"
          />
        </div>

        {/* Text Animation */}
        <div className="h-10 flex flex-col items-center justify-center w-full z-10">
          <AnimatePresence mode="wait">
            <motion.p
              key={textIndex}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="text-xs font-mono text-blue-200 tracking-widest uppercase text-center"
            >
              {LOADING_TEXTS[textIndex]}
            </motion.p>
          </AnimatePresence>
          <div className="flex gap-1 mt-2">
            <motion.div
              animate={{ opacity: [0.2, 1, 0.2] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0 }}
              className="w-1 h-1 bg-blue-400 rounded-full"
            />
            <motion.div
              animate={{ opacity: [0.2, 1, 0.2] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
              className="w-1 h-1 bg-blue-400 rounded-full"
            />
            <motion.div
              animate={{ opacity: [0.2, 1, 0.2] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
              className="w-1 h-1 bg-blue-400 rounded-full"
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
};
