import React from "react";
import clsx from "clsx";

export const Button = ({
  children,
  variant = "primary",
  className,
  icon: Icon,
  ...props
}) => {
  return (
    <button
      className={clsx(
        "flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary"
          ? "bg-white text-black hover:bg-zinc-200"
          : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700",
        className
      )}
      {...props}
    >
      {Icon && <Icon className="w-4 h-4" />}
      {children}
    </button>
  );
};
