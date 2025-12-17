import { useEffect, useState } from "react";
import { Monitor, Play } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";

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
      } catch {}
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
      <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center gap-2">
        <Monitor className="w-4 h-4 text-gray-500" />
        <h2 className="text-sm font-semibold">Live Preview</h2>

        <div className="ml-auto flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              connected ? "bg-green-500" : "bg-gray-400"
            }`}
          />
          <span className="text-xs text-gray-500 font-medium">
            {connected ? "Live" : "Offline"}
          </span>
        </div>
      </div>

      {/* Video Area */}
      <div className="flex-1 min-h-0 bg-gray-100 dark:bg-zinc-950 flex items-center justify-center relative">
        {src ? (
          <img
            src={src}
            alt="Live preview"
            className="w-full h-full object-contain pointer-events-none select-none"
            draggable={false}
          />
        ) : (
          <div className="text-center">
            <div className="w-12 h-12 bg-white dark:bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-3 border border-gray-200 dark:border-gray-700 shadow-sm">
              <Play className="w-5 h-5 text-gray-400 ml-0.5" />
            </div>
            <p className="text-sm text-gray-500 font-medium">
              {sessionId ? "Waiting for frames..." : "No active session"}
            </p>
          </div>
        )}
      </div>
    </GlassCard>
  );
};
