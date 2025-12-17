import React from "react";
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
    connectToUrl,
    runPrompt,
    runFullScan,
  } = useTestAgent();

  return (
    <div className="dark flex h-screen w-full bg-gray-50 dark:bg-black text-gray-900 dark:text-gray-100 font-sans overflow-hidden selection:bg-zinc-200 dark:selection:bg-zinc-800 transition-colors duration-500">
      {/* Futuristic Background */}
      <div className="fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-black to-zinc-950" />
      <div className="fixed inset-0 z-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay" />

      <div className="relative z-10 flex w-full h-full p-6 gap-6">
        <Sidebar userId={userId} />

        <main className="flex-1 flex gap-4 overflow-hidden">
          <ControlPanel
            isConnected={isConnected}
            isScanning={isScanning}
            isRunningTest={isRunningTest}
            isFullScanning={isFullScanning}
            onConnect={connectToUrl}
            onRunTest={runPrompt}
            onFullScan={runFullScan}
          />

          <div className="flex-1 flex flex-col gap-4 h-full overflow-hidden">
            <div className="relative flex-1 min-h-0">
              <VideoPlayer sessionId={userId} />
              <AnimatePresence>
                {(isRunningTest || isScanning) && <ExecutionLoader />}
              </AnimatePresence>
            </div>
            <ResultsLog
              testHistory={testHistory}
              isRunningTest={isRunningTest}
            />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
