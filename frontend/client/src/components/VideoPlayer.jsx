import { useEffect, useState } from "react";
import { Monitor, Signal, WifiOff, MousePointer, Eye } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";
import clsx from "clsx";
import { buildWsCandidates } from "../config";

// VITE_BROWSER_VIEW_MODE=novnc → Docker mode: embed real browser via noVNC iframe
// VITE_BROWSER_VIEW_MODE=screenshots (default) → local mode: WebSocket screenshot stream
const BROWSER_VIEW_MODE = import.meta.env.VITE_BROWSER_VIEW_MODE || "screenshots";
const NOVNC_URL = import.meta.env.VITE_NOVNC_URL || "";

// --- noVNC mode: embed the real Chromium window in an iframe ---
const NoVncViewer = () => {
  // Default: view-only. Toggle to allow mouse/keyboard input into the VNC session.
  const [interactive, setInteractive] = useState(false);

  // Changing the src reconnects the iframe with the correct viewOnly setting
  const iframeSrc = interactive ? `${NOVNC_URL}?interactive=1` : NOVNC_URL;

  return (
    <GlassCard className="h-full p-0 flex flex-col overflow-hidden" delay={0.3}>
      <div className="p-4 border-b border-white/5 flex items-center gap-3 bg-white/5 backdrop-blur-md">
        <Monitor className="w-4 h-4 text-blue-400" />
        <h2 className="text-sm font-bold text-white tracking-wide uppercase">
          Visual Feed
        </h2>
        <div className="ml-auto flex items-center gap-2">
          {/* Toggle view-only ↔ interactive */}
          <button
            onClick={() => setInteractive((v) => !v)}
            title={interactive ? "Switch to view-only" : "Enable mouse & keyboard"}
            className={clsx(
              "p-1.5 rounded border transition-all duration-200",
              interactive
                ? "border-emerald-500/50 text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20"
                : "border-white/10 text-slate-500 hover:text-slate-300 hover:border-white/20"
            )}
          >
            {interactive ? (
              <Eye className="w-3.5 h-3.5" />
            ) : (
              <MousePointer className="w-3.5 h-3.5" />
            )}
          </button>

          <div className="w-2 h-2 rounded-full bg-emerald-500 text-emerald-500 animate-pulse shadow-[0_0_8px_currentColor]" />
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
            {interactive ? "Interactive" : "Live Browser"}
          </span>
        </div>
      </div>

      {/* Real Chromium window via noVNC — fills container, scales dynamically */}
      <div className="flex-1 min-h-0 bg-black relative overflow-hidden">
        <iframe
          src={iframeSrc}
          className="w-full h-full border-0"
          title="Live Browser (noVNC)"
        />
        {/* Overlay blocks mouse/keyboard when view-only; removed when interactive */}
        {!interactive && <div className="absolute inset-0 z-10" />}
      </div>
    </GlassCard>
  );
};

// --- Screenshots mode: existing WebSocket screenshot stream (unchanged) ---
const ScreenshotViewer = ({ sessionId }) => {
  const [src, setSrc] = useState("");
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // חייב להיות uuid hex באורך 32 (uuid.uuid4().hex)
    const validSession = /^[a-f0-9]{32}$/i.test(sessionId ?? "");
    if (!validSession) {
      setConnected(false);
      setSrc("");
      return;
    }

    const candidates = buildWsCandidates(`/ws/sessions/${sessionId}/frames`);
    let ws;
    let candidateIndex = 0;
    let connected = false;

    const openCandidate = () => {
      if (candidateIndex >= candidates.length) {
        setConnected(false);
        console.error("VideoPlayer: all frame WS endpoints failed", candidates);
        return;
      }

      const wsUrl = candidates[candidateIndex++];
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        connected = true;
        setConnected(true);
      };

      ws.onclose = () => {
        if (!connected) {
          openCandidate();
          return;
        }
        setConnected(false);
      };

      ws.onerror = () => {
        if (!connected) {
          console.debug("Frames WS probe failed, trying next endpoint...");
        }
        setConnected(false);
      };

      ws.onmessage = (e) => {
        try {
          const ev = JSON.parse(e.data);

          if (ev?.type === "frame") {
            if (ev.frame) {
              setSrc(ev.frame);
              return;
            }

            if (ev.mime && ev.data) {
              setSrc(`data:${ev.mime};base64,${ev.data}`);
              return;
            }
          }
        } catch {
          console.error("VideoPlayer: Failed to parse WS message", e.data);
        }
      };
    };

    openCandidate();

    // keep-alive קטן כדי שהשרת יקבל משהו מדי פעם
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 15000);

    return () => {
      clearInterval(heartbeat);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
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
              {sessionId ? "Waiting for frame data" : "Initiate session to view"}
            </p>
          </div>
        )}
      </div>
    </GlassCard>
  );
};

export const VideoPlayer = ({ sessionId }) => {
  if (BROWSER_VIEW_MODE === "novnc") return <NoVncViewer />;
  return <ScreenshotViewer sessionId={sessionId} />;
};
