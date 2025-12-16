import React from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

export const GlassCard = ({ children, className, delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: delay, ease: "easeOut" }}
      className={clsx(
        "bg-white/80 dark:bg-white/5 backdrop-blur-xl border border-gray-200 dark:border-white/10 shadow-xl dark:shadow-2xl rounded-2xl overflow-hidden transition-colors duration-500",
        className
      )}
    >
      {children}
    </motion.div>
  );
};
