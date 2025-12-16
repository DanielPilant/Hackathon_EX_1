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
    <div className="dark flex h-screen w-full bg-gray-50 dark:bg-black text-gray-900 dark:text-gray-100 font-sans overflow-hidden selection:bg-zinc-200 dark:selection:bg-zinc-800 transition-colors duration-500">
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

        <div className="flex-1 flex flex-col gap-4 min-h-0">
            <div className="flex-[2] min-h-0">
              <VideoPlayer />
            </div>

            <div className="flex-[1] min-h-0">
              <ResultsLog
                testHistory={testHistory}
                isRunningTest={isRunningTest}
              />
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}

export default App;
