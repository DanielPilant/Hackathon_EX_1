import { useState } from "react";
import {
  Play,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  Globe,
  MessageSquare,
} from "lucide-react";
import { setTargetUrl, sendPrompt } from "./api";
import clsx from "clsx";

function App() {
  const [targetUrl, setTargetUrlState] = useState("");
  const [prompt, setPrompt] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [testResults, setTestResults] = useState([
    { id: 1, name: "Navigate to Homepage", status: "pass", time: "0.8s" },
    { id: 2, name: "Check Login Button", status: "pass", time: "0.2s" },
    { id: 3, name: "Verify Page Title", status: "fail", time: "0.1s" },
    { id: 4, name: "Input Credentials", status: "pending", time: "-" },
  ]);

  const handleRunTest = async () => {
    if (!targetUrl || !prompt) return;
    setIsProcessing(true);
    try {
      await setTargetUrl(targetUrl);
      await sendPrompt(prompt);
      // Simulate adding a new result
      setTestResults((prev) => [
        ...prev,
        {
          id: Date.now(),
          name: "New Test Step",
          status: "running",
          time: "...",
        },
      ]);
      setTimeout(() => {
        setTestResults((prev) =>
          prev.map((r) =>
            r.status === "running" ? { ...r, status: "pass", time: "1.2s" } : r
          )
        );
        setIsProcessing(false);
      }, 2000);
    } catch (error) {
      console.error(error);
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      {/* Sidebar / Header */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-6 border-b border-gray-700 flex items-center gap-3">
          <Activity className="text-blue-500 w-6 h-6" />
          <h1 className="text-xl font-bold tracking-tight">TestFlow AI</h1>
        </div>
        <div className="p-4 flex-1">
          <div className="flex items-center gap-2 text-sm text-green-400 bg-green-400/10 px-3 py-2 rounded-md border border-green-400/20">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            System Connected
          </div>
        </div>
        <div className="p-4 text-xs text-gray-500 text-center">
          v0.1.0 Alpha
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Input Zone (Left Panel) */}
        <div className="w-1/3 p-6 border-r border-gray-700 flex flex-col gap-6 bg-gray-900/50">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
              <Globe className="w-4 h-4" /> Target Website URL
            </label>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrlState(e.target.value)}
              placeholder="https://example.com"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
            />
          </div>

          <div className="flex-1 flex flex-col">
            <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> Test Instructions
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your test case (e.g., 'Go to login page, enter valid credentials, and verify dashboard loads')..."
              className="w-full flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none transition-all"
            />
          </div>

          <button
            onClick={handleRunTest}
            disabled={isProcessing}
            className={clsx(
              "w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-2 transition-all",
              isProcessing
                ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20"
            )}
          >
            {isProcessing ? (
              <>
                <Activity className="w-5 h-5 animate-spin" /> Processing...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" /> Run Test
              </>
            )}
          </button>
        </div>

        {/* Right Panel */}
        <div className="flex-1 flex flex-col bg-gray-950">
          {/* Visual Feedback Zone (Top) */}
          <div className="h-1/2 border-b border-gray-800 p-6 flex flex-col">
            <h2 className="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4" /> Live Execution View
            </h2>
            <div className="flex-1 bg-black rounded-xl border border-gray-800 flex items-center justify-center relative overflow-hidden group">
              {/* Placeholder for Video Player */}
              <div className="absolute inset-0 bg-gradient-to-br from-gray-900 to-black opacity-50" />
              <div className="text-center z-10">
                <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Play className="w-8 h-8 text-gray-600" />
                </div>
                <p className="text-gray-500 font-medium">
                  Waiting for execution stream...
                </p>
              </div>
            </div>
          </div>

          {/* Results Zone (Bottom) */}
          <div className="h-1/2 p-6 flex flex-col overflow-hidden">
            <h2 className="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> Test Results
            </h2>
            <div className="flex-1 overflow-y-auto pr-2 space-y-2">
              {testResults.map((step) => (
                <div
                  key={step.id}
                  className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-center justify-between hover:border-gray-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {step.status === "pass" && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {step.status === "fail" && (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                    {step.status === "running" && (
                      <Activity className="w-5 h-5 text-blue-500 animate-spin" />
                    )}
                    {step.status === "pending" && (
                      <Clock className="w-5 h-5 text-gray-600" />
                    )}
                    <span
                      className={clsx(
                        "font-medium",
                        step.status === "pending"
                          ? "text-gray-500"
                          : "text-gray-200"
                      )}
                    >
                      {step.name}
                    </span>
                  </div>
                  <div className="text-sm font-mono text-gray-500">
                    {step.time}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
