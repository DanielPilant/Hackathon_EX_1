import React from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { Sidebar } from "./components/Sidebar";
import { ControlPanel } from "./components/ControlPanel";
import { VideoPlayer } from "./components/VideoPlayer";
import { ResultsLog } from "./components/ResultsLog";
import { useTestAgent } from "./hooks/useTestAgent";
import { ExecutionLoader } from "./components/ExecutionLoader";
import { AnimatePresence } from "framer-motion";

function App() {
  const {
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
  } = useTestAgent();

  return (
    <div className="dark flex h-screen w-screen bg-gray-50 dark:bg-black text-gray-900 dark:text-gray-100 font-sans overflow-hidden selection:bg-zinc-200 dark:selection:bg-zinc-800 transition-colors duration-500">
      {/* Futuristic Background */}
      <div className="fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-black to-zinc-950" />
      <div className="fixed inset-0 z-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay" />

      <div className="relative z-10 w-full h-full">
        <PanelGroup direction="horizontal">
          {/* Panel A: Sidebar & Mission Control */}
          <Panel defaultSize={40} minSize={20} maxSize={60} className="flex flex-col h-full overflow-hidden">
            <div className="flex h-full p-4 pr-2 gap-4">
              <Sidebar userId={userId} />
              <ControlPanel
                className="flex-1 h-full"
                isConnected={isConnected}
                isScanning={isScanning}
                isRunningTest={isRunningTest}
                isFullScanning={isFullScanning}
                isSuggesting={isSuggesting}
                onConnect={connectToUrl}
                onRunTest={runPrompt}
                onFullScan={runFullScan}
                onGenerateSuggestion={generateSuggestion}
              />
            </div>
          </Panel>

          {/* Vertical Resize Handle */}
          <PanelResizeHandle className="w-1.5 bg-transparent hover:bg-blue-500/20 transition-colors flex items-center justify-center group focus:outline-none">
            <div className="w-px h-8 bg-zinc-800 group-hover:bg-blue-500 transition-colors" />
          </PanelResizeHandle>

          {/* Panel B: Main Content Area */}
          <Panel defaultSize={60} minSize={40} className="flex flex-col h-full overflow-hidden">
            <PanelGroup direction="vertical">
              {/* Panel B1: Visual Feed */}
              <Panel defaultSize={65} minSize={30} className="flex flex-col h-full overflow-hidden p-4 pl-2 pb-2">
                <div className="relative flex-1 min-h-0 w-full h-full">
                  <VideoPlayer sessionId={userId} />
                  <AnimatePresence>
                    {(isRunningTest || isScanning) && <ExecutionLoader />}
                  </AnimatePresence>
                </div>
              </Panel>

              {/* Horizontal Resize Handle */}
              <PanelResizeHandle className="h-1.5 bg-transparent hover:bg-blue-500/20 transition-colors flex items-center justify-center group focus:outline-none">
                <div className="h-px w-8 bg-zinc-800 group-hover:bg-blue-500 transition-colors" />
              </PanelResizeHandle>

              {/* Panel B2: Execution Log */}
              <Panel defaultSize={35} minSize={10} className="flex flex-col h-full overflow-hidden p-4 pl-2 pt-2">
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
