import React from "react";
import clsx from "clsx";

export const Panel = ({ children, className, ...props }) => {
  return (
    <div
      className={clsx(
        "bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden flex flex-col",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
