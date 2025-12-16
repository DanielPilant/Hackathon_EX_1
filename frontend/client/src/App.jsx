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
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      <Sidebar userId={userId} />

      <main className="flex-1 flex overflow-hidden">
        <ControlPanel
          isConnected={isConnected}
          isScanning={isScanning}
          isRunningTest={isRunningTest}
          isFullScanning={isFullScanning}
          onConnect={connectToUrl}
          onRunTest={runPrompt}
          onFullScan={runFullScan}
        />

        <div className="flex-1 flex flex-col bg-gray-950">
          <VideoPlayer />
          <ResultsLog testHistory={testHistory} isRunningTest={isRunningTest} />
        </div>
      </main>
    </div>
  );
}

export default App;
