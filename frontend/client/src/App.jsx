import { useState, useEffect } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { Menu, X } from "lucide-react";
import { Sidebar } from "./components/Sidebar";
import { ControlPanel } from "./components/ControlPanel";
import { VideoPlayer } from "./components/VideoPlayer";
import { ResultsLog } from "./components/ResultsLog";
import { useTestAgent } from "./hooks/useTestAgent";
import { ExecutionLoader } from "./components/ExecutionLoader";
import { AnimatePresence, motion } from "framer-motion";
import { backend } from "./services/backend";

const BROWSER_VIEW_MODE = import.meta.env.VITE_BROWSER_VIEW_MODE || "screenshots";

function App() {
  const {
    sessionId,
    userId,
    testHistory,
    isScanning,
    isConnected,
    isRunningTest,
    isFullScanning,
    isSuggesting,
    connectToUrl,
    runPrompt,
    runFullScan,
    generateSuggestion,
    getManualSuggestions,
    logToTerminal,
    shouldTriggerScan,
    setShouldTriggerScan,
    resetSession,
  } = useTestAgent();

  // targetUrl lifted here so it survives the pre-active → active layout swap
  const [targetUrl, setTargetUrl] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Reset browser once on page load (Docker mode only)
  useEffect(() => {
    if (BROWSER_VIEW_MODE === "novnc") {
      backend.resetBrowser();
    }
  }, []);

  const handleReset = () => {
    setTargetUrl("");
    resetSession();
  };

  const outerClass =
    "dark flex h-screen w-screen bg-gray-50 dark:bg-black text-gray-900 dark:text-gray-100 font-sans overflow-hidden selection:bg-zinc-200 dark:selection:bg-zinc-800 transition-colors duration-500";

  const bgLayers = (
    <>
      <div className="fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-black to-zinc-950" />
      <div className="fixed inset-0 z-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay" />
    </>
  );

  const controlPanelProps = {
    sessionId,
    isConnected,
    isScanning,
    isRunningTest,
    isFullScanning,
    isSuggesting,
    onConnect: connectToUrl,
    onRunTest: runPrompt,
    onFullScan: runFullScan,
    onGenerateSuggestion: generateSuggestion,
    onGetManualSuggestions: getManualSuggestions,
    onLogToTerminal: logToTerminal,
    onReset: handleReset,
    shouldTriggerScan,
    setShouldTriggerScan,
    targetUrl,
    onTargetUrlChange: setTargetUrl,
  };

  const hResizeHandle = (
    <PanelResizeHandle className="w-1.5 bg-transparent hover:bg-blue-500/20 transition-colors flex items-center justify-center group focus:outline-none">
      <div className="w-px h-8 bg-zinc-800 group-hover:bg-blue-500 transition-colors" />
    </PanelResizeHandle>
  );

  const vResizeHandle = (
    <PanelResizeHandle className="h-1.5 bg-transparent hover:bg-blue-500/20 transition-colors flex items-center justify-center group focus:outline-none">
      <div className="h-px w-8 bg-zinc-800 group-hover:bg-blue-500 transition-colors" />
    </PanelResizeHandle>
  );

  // ─── Docker mode ──────────────────────────────────────────────────────────
  if (BROWSER_VIEW_MODE === "novnc") {
    const isActive = isConnected || isScanning;

    // ── Pre-active: Sidebar + Mission Control only, right panel doesn't exist ──
    if (!isActive) {
      return (
        <div className={outerClass}>
          {bgLayers}
          <div className="relative z-10 w-full h-full flex p-4 gap-4">
            <Sidebar userId={userId} />
            <ControlPanel className="flex-1 h-full" {...controlPanelProps} />
          </div>
        </div>
      );
    }

    // ── Active: resizable panels, sidebar togglable ───────────────────────────
    const showSidebar = !isActive || sidebarOpen;

    return (
      <div className={outerClass}>
        {bgLayers}
        <div className="relative z-10 w-full h-full flex overflow-hidden">

          {/* Sidebar — animated in/out */}
          <AnimatePresence initial={false}>
            {showSidebar && (
              <motion.div
                key="sidebar"
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 304, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
                className="overflow-hidden shrink-0 h-full"
              >
                <div className="w-[304px] h-full p-4 pr-0">
                  <Sidebar userId={userId} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <PanelGroup direction="horizontal" className="flex-1 min-w-0">

            {/* Left: Mission Control */}
            <Panel
              defaultSize={35}
              minSize={15}
              maxSize={70}
              className="flex flex-col h-full overflow-hidden"
            >
              <div className="flex flex-col h-full p-4 pr-2 gap-2">
                {isConnected && (
                  <button
                    onClick={() => setSidebarOpen((v) => !v)}
                    title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
                    className="self-start p-1.5 rounded border border-white/10 text-slate-500 hover:text-slate-300 hover:border-white/20 transition-all duration-200"
                  >
                    {sidebarOpen ? (
                      <X className="w-3.5 h-3.5" />
                    ) : (
                      <Menu className="w-3.5 h-3.5" />
                    )}
                  </button>
                )}
                <ControlPanel className="flex-1 min-h-0" {...controlPanelProps} />
              </div>
            </Panel>

            {hResizeHandle}

            {/* Right: Visual Feed + Execution Log */}
            <Panel
              defaultSize={65}
              minSize={30}
              className="flex flex-col h-full overflow-hidden"
            >
              <PanelGroup direction="vertical">
                <Panel
                  defaultSize={65}
                  minSize={20}
                  className="flex flex-col h-full overflow-hidden p-4 pl-2 pb-2"
                >
                  <div className="relative flex-1 min-h-0 w-full h-full">
                    <VideoPlayer sessionId={sessionId} />
                    <AnimatePresence>
                      {(isRunningTest || isScanning) && <ExecutionLoader />}
                    </AnimatePresence>
                  </div>
                </Panel>

                {vResizeHandle}

                <Panel
                  defaultSize={35}
                  minSize={10}
                  className="flex flex-col h-full overflow-hidden p-4 pl-2 pt-2"
                >
                  <ResultsLog
                    testHistory={testHistory}
                    isRunningTest={isRunningTest}
                  />
                </Panel>
              </PanelGroup>
            </Panel>

          </PanelGroup>
        </div>
      </div>
    );
  }

  // ─── Screenshots mode (local dev): original static layout, unchanged ────────
  return (
    <div className={outerClass}>
      {bgLayers}
      <div className="relative z-10 w-full h-full">
        <PanelGroup direction="horizontal">
          <Panel
            defaultSize={40}
            minSize={20}
            maxSize={60}
            className="flex flex-col h-full overflow-hidden"
          >
            <div className="flex h-full p-4 pr-2 gap-4">
              <Sidebar userId={userId} />
              <ControlPanel className="flex-1 h-full" {...controlPanelProps} />
            </div>
          </Panel>

          {hResizeHandle}

          <Panel
            defaultSize={60}
            minSize={40}
            className="flex flex-col h-full overflow-hidden"
          >
            <PanelGroup direction="vertical">
              <Panel
                defaultSize={65}
                minSize={30}
                className="flex flex-col h-full overflow-hidden p-4 pl-2 pb-2"
              >
                <div className="relative flex-1 min-h-0 w-full h-full">
                  <VideoPlayer sessionId={sessionId} />
                  <AnimatePresence>
                    {(isRunningTest || isScanning) && <ExecutionLoader />}
                  </AnimatePresence>
                </div>
              </Panel>

              {vResizeHandle}

              <Panel
                defaultSize={35}
                minSize={10}
                className="flex flex-col h-full overflow-hidden p-4 pl-2 pt-2"
              >
                <ResultsLog
                  testHistory={testHistory}
                  isRunningTest={isRunningTest}
                />
              </Panel>
            </PanelGroup>
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}

export default App;
