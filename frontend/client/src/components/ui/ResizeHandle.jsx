import React from "react";
import { PanelResizeHandle } from "react-resizable-panels";
import clsx from "clsx";
import { GripVertical, GripHorizontal } from "lucide-react";

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
          "absolute bg-gray-200 dark:bg-gray-800 transition-all duration-200 rounded-full group-hover:bg-blue-500 group-active:bg-blue-600",
          orientation === "vertical"
            ? "w-0.5 h-8 group-hover:h-full group-active:h-full inset-y-0 my-auto"
            : "h-0.5 w-8 group-hover:w-full group-active:w-full inset-x-0 mx-auto"
        )}
      />
    </PanelResizeHandle>
  );
};
