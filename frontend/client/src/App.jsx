import React from "react";
import { Panel, PanelGroup } from "react-resizable-panels";
import { Sidebar } from "./components/Sidebar";
import { ControlPanel } from "./components/ControlPanel";
import { VideoPlayer } from "./components/VideoPlayer";
import { ResultsLog } from "./components/ResultsLog";
import { ResizeHandle } from "./components/ui/ResizeHandle";
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
      <div className="relative z-10 w-full h-full p-2">
        <PanelGroup direction="horizontal" className="gap-2">
          {/* Sidebar Panel */}
          <Panel
            defaultSize={20}
            minSize={15}
            maxSize={30}
            className="flex flex-col"
          >
            <Sidebar userId={userId} />
          </Panel>

          <ResizeHandle orientation="vertical" />

          {/* Main Content Area */}
          <Panel className="flex flex-col">
            <PanelGroup direction="horizontal" className="gap-2">
              {/* Control Panel */}
              <Panel defaultSize={30} minSize={25} className="flex flex-col">
                <ControlPanel
                  isConnected={isConnected}
                  isScanning={isScanning}
                  isRunningTest={isRunningTest}
                  isFullScanning={isFullScanning}
                  onConnect={connectToUrl}
                  onRunTest={runPrompt}
                  onFullScan={runFullScan}
                />
              </Panel>

              <ResizeHandle orientation="vertical" />

              {/* Right Zone (Preview + Logs) */}
              <Panel className="flex flex-col">
                <PanelGroup direction="vertical" className="gap-2">
                  {/* Live Preview */}
                  <Panel
                    defaultSize={50}
                    minSize={30}
                    className="flex flex-col"
                  >
                    <VideoPlayer />
                  </Panel>

                  <ResizeHandle orientation="horizontal" />

                  {/* Results Log */}
                  <Panel minSize={20} className="flex flex-col">
                    <ResultsLog
                      testHistory={testHistory}
                      isRunningTest={isRunningTest}
                    />
                  </Panel>
                </PanelGroup>
              </Panel>
            </PanelGroup>
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}

export default App;
