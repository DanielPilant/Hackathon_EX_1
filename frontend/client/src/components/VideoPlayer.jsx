import React from "react";
import { Activity, Play } from "lucide-react";

export const VideoPlayer = () => {
  return (
    <div className="h-1/2 border-b border-gray-800 p-6 flex flex-col">
      <h2 className="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
        <Activity className="w-4 h-4" /> Live Execution View
      </h2>
      <div className="flex-1 bg-black rounded-xl border border-gray-800 flex items-center justify-center relative overflow-hidden group">
        {/* Placeholder for Video Player */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 to-black opacity-50" />
        <div className="text-center z-10">
          <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
            <Play className="w-8 h-8 text-gray-600" />
          </div>
          <p className="text-gray-500 font-medium">
            Waiting for execution stream...
          </p>
        </div>
      </div>
    </div>
  );
};
