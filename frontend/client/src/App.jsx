import React from "react";
import { Sidebar } from "./components/Sidebar";
import { ControlPanel } from "./components/ControlPanel";
import { ResultsLog } from "./components/ResultsLog";
import { useTestAgent } from "./hooks/useTestAgent"; // <--- ייבוא המוח

function App() {
  // 1. שימוש במוח שבנינו
  const {
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
        {/* 2. העברת הפונקציות לתוך הפאנל */}
        <ControlPanel
          isConnected={isConnected}
          isScanning={isScanning}
          isRunningTest={isRunningTest}
          // כשהכפתור נלחץ בפאנל -> תפעיל את הפונקציה החכמה שלנו
          onConnect={(url) => connectToUrl(url)}
          onRunTest={(prompt) => runPrompt(prompt)}
        />

        {/* הצגת התוצאות */}
        <ResultsLog testHistory={testHistory} />
      </main>
    </div>
  );
}

export default App;
