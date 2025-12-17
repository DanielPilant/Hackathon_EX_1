import React from "react";
import { Sidebar } from "./components/Sidebar";
import { ControlPanel } from "./components/ControlPanel";
import { ResultsLog } from "./components/ResultsLog";
import { VideoPlayer } from "./components/VideoPlayer";
import { useTestAgent } from "./hooks/useTestAgent"; // <--- ייבוא המוח

function App() {
  // 1. שימוש במוח שבנינו
  const {
    sessionId,
    isConnected,
    isScanning,
    isRunningTest,
    testHistory,
    connectToUrl, // הפונקציה החכמה
    runPrompt, // הפונקציה החכמה
  } = useTestAgent();

  return (
    <div className="flex h-screen bg-black text-white">
      <Sidebar />

      <main className="flex-1 p-6 flex flex-col gap-6">
        {/* Top Row: Control Panel + Video Player */}
        <div className="flex gap-6 h-1/2">
          <ControlPanel
            isConnected={isConnected}
            isScanning={isScanning}
            isRunningTest={isRunningTest}
            // כשהכפתור נלחץ בפאנל -> תפעיל את הפונקציה החכמה שלנו
            onConnect={(url) => connectToUrl(url)}
            onRunTest={(prompt) => runPrompt(prompt)}
          />

          <div className="flex-1 h-full">
            <VideoPlayer sessionId={sessionId} />
          </div>
        </div>

        {/* הצגת התוצאות */}
        <ResultsLog testHistory={testHistory} isRunningTest={isRunningTest} />
      </main>
    </div>
  );
}

export default App;
