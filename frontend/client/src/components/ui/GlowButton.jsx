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
      "bg-blue-600/20 hover:bg-blue-600/30 text-blue-100 border border-blue-500/50 shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_30px_rgba(37,99,235,0.5)]",
    secondary:
      "bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 hover:border-white/20",
    success:
      "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-100 border border-emerald-500/50 shadow-[0_0_20px_rgba(16,185,129,0.3)]",
    danger:
      "bg-red-500/20 hover:bg-red-500/30 text-red-100 border border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.3)]",
  };

  return (
    <motion.button
      whileHover={!disabled ? { scale: 1.02 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "relative px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 flex items-center justify-center gap-2 backdrop-blur-sm",
        variants[variant],
        disabled && "opacity-50 cursor-not-allowed grayscale",
        className
      )}
    >
      {Icon && <Icon className="w-4 h-4" />}
      {children}
    </motion.button>
  );
};
