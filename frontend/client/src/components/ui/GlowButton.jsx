import React from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

export const GlowButton = ({
  children,
  onClick,
  disabled,
  variant = "primary",
  className,
  icon: Icon,
}) => {
  const variants = {
    primary:
      "bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_20px_rgba(37,99,235,0.5)]",
    secondary:
      "bg-purple-100 dark:bg-purple-600/20 hover:bg-purple-200 dark:hover:bg-purple-600/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30 shadow-[0_0_15px_rgba(147,51,234,0.2)]",
    danger:
      "bg-red-100 dark:bg-red-600/20 hover:bg-red-200 dark:hover:bg-red-600/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-500/30",
    ghost:
      "bg-transparent hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white",
  };

  return (
    <motion.button
      whileHover={
        !disabled
          ? { scale: 1.02, boxShadow: "0 0 25px rgba(59, 130, 246, 0.4)" }
          : {}
      }
      whileTap={!disabled ? { scale: 0.98 } : {}}
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "relative px-6 py-3 rounded-xl font-bold transition-all duration-300 flex items-center justify-center gap-2",
        variants[variant],
        disabled && "opacity-50 cursor-not-allowed grayscale",
        className
      )}
    >
      {Icon && (
        <Icon className={clsx("w-5 h-5", disabled ? "animate-none" : "")} />
      )}
      {children}
    </motion.button>
  );
};
