import React from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

export const GlassCard = ({ children, className, delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: delay, ease: "easeOut" }}
      className={clsx(
        "bg-white dark:bg-zinc-900 border border-gray-200 dark:border-gray-800 shadow-sm rounded-lg overflow-hidden",
        className
      )}
    >
      {children}
    </motion.div>
  );
};
