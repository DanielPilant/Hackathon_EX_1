import React from "react";
import { Sidebar } from "./components/Sidebar";
import { ControlPanel } from "./components/ControlPanel";
import { VideoPlayer } from "./components/VideoPlayer";
import { ResultsLog } from "./components/ResultsLog";
import { useTestAgent } from "./hooks/useTestAgent";

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
    <div className="dark flex h-screen w-full bg-gray-50 dark:bg-slate-950 dark:bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] dark:from-slate-900 dark:via-slate-950 dark:to-black text-gray-900 dark:text-white font-sans overflow-hidden selection:bg-blue-500/30 transition-colors duration-500">
      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay dark:mix-blend-normal"></div>

      <div className="relative z-10 flex w-full h-full p-4 gap-4">
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

          <div className="flex-1 flex flex-col gap-4">
            <VideoPlayer />
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
