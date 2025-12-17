import { useEffect, useState } from "react";
import { Monitor, Play, Signal, WifiOff } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";
import clsx from "clsx";

export const VideoPlayer = ({ sessionId }) => {
  const [src, setSrc] = useState("");
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // אין סשן => לא מתחברים
    if (!sessionId) {
      setConnected(false);
      setSrc("");
      return;
    }

    const ws = new WebSocket(
      `ws://127.0.0.1:8000/ws/sessions/${sessionId}/frames`
    );

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data);

        if (ev?.type === "frame" && ev?.frame) {
          // כי זה כבר data URL מלא
          setSrc(ev.frame);
        }
      } catch {
        console.error("VideoPlayer: Failed to parse WS message", e.data);
      }
    };

    // keep-alive קטן כדי שהשרת (שקורא receive_text) יקבל משהו מדי פעם
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 15000);

    return () => {
      clearInterval(heartbeat);
      ws.close();
    };
  }, [sessionId]);

  return (
    <GlassCard className="h-full p-0 flex flex-col overflow-hidden" delay={0.3}>
      {/* Header */}
      <div className="p-4 border-b border-white/5 flex items-center gap-3 bg-white/5 backdrop-blur-md">
        <Monitor className="w-4 h-4 text-blue-400" />
        <h2 className="text-sm font-bold text-white tracking-wide uppercase">
          Visual Feed
        </h2>

        <div className="ml-auto flex items-center gap-2">
          <div
            className={clsx(
              "w-2 h-2 rounded-full shadow-[0_0_8px_currentColor]",
              connected
                ? "bg-emerald-500 text-emerald-500 animate-pulse"
                : "bg-slate-600 text-slate-600"
            )}
          />
          <span
            className={clsx(
              "text-[10px] font-mono font-bold uppercase tracking-wider",
              connected ? "text-emerald-400" : "text-slate-500"
            )}
          >
            {connected ? "Live Signal" : "Offline"}
          </span>
        </div>
      </div>

      {/* Video Area */}
      <div className="flex-1 min-h-0 bg-black flex items-center justify-center relative overflow-hidden">
        {/* Grid Overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none z-20" />

        {src ? (
          <img
            src={src}
            alt="Live preview"
            className="w-full h-full object-contain pointer-events-none select-none relative z-10"
            draggable={false}
          />
        ) : (
          <div className="text-center relative z-10">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4 border border-white/5 backdrop-blur-sm">
              {sessionId ? (
                <Signal className="w-6 h-6 text-blue-400 animate-pulse" />
              ) : (
                <WifiOff className="w-6 h-6 text-slate-600" />
              )}
            </div>
            <p className="text-sm text-slate-400 font-medium tracking-wide">
              {sessionId ? "Establishing Uplink..." : "No Active Feed"}
            </p>
            <p className="text-xs text-slate-600 mt-1 font-mono">
              {sessionId
                ? "Waiting for frame data"
                : "Initiate session to view"}
            </p>
          </div>
        )}
      </div>
    </GlassCard>
  );
};
