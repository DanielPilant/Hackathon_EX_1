import React from "react";
import { Monitor, Play } from "lucide-react";
import { Panel } from "./ui/Panel";
import { PanelHeader } from "./ui/PanelHeader";

export const VideoPlayer = () => {
  return (
    <Panel className="w-full h-full flex flex-col overflow-hidden">
      <PanelHeader icon={Monitor} title="Live Preview">
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-zinc-700" />
          <span className="text-xs text-zinc-500 font-medium">Offline</span>
        </div>
      </PanelHeader>

      <div className="flex-1 bg-zinc-950 flex items-center justify-center relative">
        <div className="text-center">
          <div className="w-12 h-12 bg-zinc-900 rounded-full flex items-center justify-center mx-auto mb-3 border border-zinc-800 shadow-sm">
            <Play className="w-5 h-5 text-zinc-600 ml-0.5" />
          </div>
          <p className="text-sm text-zinc-500 font-medium">No active session</p>
        </div>
      </div>
    </Panel>
  );
};
