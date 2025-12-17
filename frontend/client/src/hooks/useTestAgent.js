import { useState } from "react";
import { backend } from "../services/backend";

export const useTestAgent = () => {
  const [sessionId, setSessionId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [isFullScanning, setIsFullScanning] = useState(false);
  const [testHistory, setTestHistory] = useState([]);

  // User ID for display only (Sidebar)
  const userId = sessionId || "Not Connected";

  // --- Connection Function ---
  const connectToUrl = async (url) => {
    if (!url) return;

    setIsScanning(true);
    try {
      // 1. Extract domain from URL
      const domain = new URL(url).hostname;
      console.log("Hook: Connecting to", url, "Domain:", domain);

      // 2. Call backend API
      const data = await backend.createSession(url, domain);

      console.log("Hook: API Response", data);

      // 3. Save session ID (backend uses snake_case)
      if (data.session_id) {
        setSessionId(data.session_id);
        setIsConnected(true);
        console.log("✅ Connected! Session ID:", data.session_id);
      }
    } catch (error) {
      console.error("Hook Error:", error);
      const errorMsg =
        error.response?.data?.detail || error.message || "Unknown error";
      alert(`Connection Failed: ${errorMsg}`);
    } finally {
      setIsScanning(false);
    }
  };

  // --- Run Prompt Function ---
  const runPrompt = async (prompt) => {
    if (!sessionId) {
      alert("Please connect first!");
      return;
    }

    setIsRunningTest(true);
    try {
      console.log("Hook: Sending prompt:", prompt);
      const data = await backend.sendPrompt(prompt, sessionId);

      // Backend returns { ok, output }, not { results }
      if (data.ok) {
        const newRun = {
          id: Date.now(),
          title: prompt.length > 30 ? prompt.substring(0, 30) + "..." : prompt,
          timestamp: new Date().toLocaleString(),
          steps: [
            {
              id: Date.now(),
              stepName: "AI Response",
              status: "pass",
              description: data.output,
              timestamp: new Date().toLocaleTimeString(),
              duration: "2s",
            },
          ],
        };
        setTestHistory((prev) => [newRun, ...prev]);
        console.log("✅ Prompt executed successfully");
      }
    } catch (error) {
      console.error("Prompt Error:", error);
      const errorMsg =
        error.response?.data?.detail || error.message || "Unknown error";
      alert(`Test Failed: ${errorMsg}`);
    } finally {
      setIsRunningTest(false);
    }
  };

  const runFullScan = async () => {
    setIsFullScanning(true);
    // כרגע רק סימולציה של סריקה
    setTimeout(() => setIsFullScanning(false), 2000);
  };

  return {
    userId,
    testHistory,
    isScanning,
    isConnected,
    isRunningTest,
    isFullScanning,
    connectToUrl,
    runPrompt,
    runFullScan,
  };
};
