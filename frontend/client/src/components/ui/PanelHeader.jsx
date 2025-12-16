import React from "react";

export const PanelHeader = ({ icon: Icon, title, rightContent }) => {
  return (
    <div className="h-10 min-h-[2.5rem] border-b border-zinc-800 flex items-center px-4 bg-zinc-900/50 select-none">
      <div className="flex items-center gap-2 text-zinc-400">
        {Icon && <Icon className="w-4 h-4" />}
        <span className="text-xs font-medium uppercase tracking-wider">
          {title}
        </span>
      </div>
      {rightContent && <div className="ml-auto">{rightContent}</div>}
    </div>
  );
};
