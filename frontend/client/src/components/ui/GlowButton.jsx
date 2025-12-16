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
      "bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-white dark:text-black dark:hover:bg-gray-200 border border-transparent shadow-sm",
    secondary:
      "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 dark:bg-zinc-900 dark:text-gray-300 dark:border-gray-800 dark:hover:bg-zinc-800 shadow-sm",
    danger:
      "bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900/30",
    ghost:
      "bg-transparent hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-500 dark:text-gray-400",
  };

  return (
    <motion.button
      whileHover={!disabled ? { scale: 1.01 } : {}}
      whileTap={!disabled ? { scale: 0.99 } : {}}
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "relative px-4 py-2 rounded-md font-medium text-sm transition-colors duration-200 flex items-center justify-center gap-2",
        variants[variant],
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      {Icon && (
        <Icon className={clsx("w-4 h-4", disabled ? "animate-none" : "")} />
      )}
      {children}
    </motion.button>
  );
};
