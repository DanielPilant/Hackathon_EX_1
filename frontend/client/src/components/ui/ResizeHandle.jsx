import React from "react";
import { PanelResizeHandle } from "react-resizable-panels";
import clsx from "clsx";

export const ResizeHandle = ({ className, id, orientation = "vertical" }) => {
  return (
    <PanelResizeHandle
      className={clsx(
        "relative flex items-center justify-center bg-transparent transition-all duration-200 outline-none group",
        orientation === "vertical"
          ? "w-2 cursor-col-resize"
          : "h-2 cursor-row-resize",
        className
      )}
      id={id}
    >
      <div
        className={clsx(
          "absolute bg-zinc-800 transition-all duration-200 rounded-full group-hover:bg-zinc-600 group-active:bg-blue-500",
          orientation === "vertical"
            ? "w-0.5 h-8 group-hover:h-12 group-active:h-12 inset-y-0 my-auto"
            : "h-0.5 w-8 group-hover:w-12 group-active:w-12 inset-x-0 mx-auto"
        )}
      />
    </PanelResizeHandle>
  );
};
