import { useState, useEffect } from "react";
import { backend } from "../services/backend";

export const useTestAgent = () => {
  const [sessionId, setSessionId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [isFullScanning, setIsFullScanning] = useState(false);
  const [testHistory, setTestHistory] = useState([]);

  // -------------------------------------------
  // הוספת ה-WebSocket Listener
  // -------------------------------------------
  useEffect(() => {
    // אם אין סשן, אין לאן להתחבר
    if (!sessionId) return;

    console.log(`🔌 Opening WebSocket for session: ${sessionId}`);

    // יצירת החיבור
    const ws = new WebSocket(`ws://localhost:8000/ws/sessions/${sessionId}`);

    // כשהחיבור נפתח
    ws.onopen = () => {
      console.log("✅ WS Connected!");
      // אופציונלי: שליחת פינג ראשוני
      // ws.send("ping");
    };

    // כשמתקבלת הודעה מהשרת (לוגים של MCP)
    ws.onmessage = (event) => {
      try {
        const logData = JSON.parse(event.data);
        console.log("🚀 [MCP LOG]:", logData);

        // Extract message content
        const message =
          logData.message || logData.content || JSON.stringify(logData);

        // Smart Status Detection
        let status = "info";
        if (/pass|success/i.test(message)) status = "pass";
        else if (/fail|error|exception/i.test(message)) status = "fail";
        else if (/processing|running|start/i.test(message)) status = "running";

        // Create new history entry
        const newEntry = {
          id: Date.now() + Math.random(), // Ensure unique ID
          title: "System Event",
          timestamp: new Date().toLocaleString(),
          isLog: true, // Flag to distinguish from user prompts if needed
          steps: [
            {
              id: Date.now(),
              stepName: message,
              status: status,
              description: logData.details || "",
              timestamp: new Date().toLocaleTimeString(),
              duration: "0.1s",
            },
          ],
        };

        setTestHistory((prev) => [newEntry, ...prev]);
      } catch {
        console.log("Received raw message:", event.data);
      }
    };

    ws.onerror = (error) => {
      console.error("❌ WS Error:", error);
    };

    ws.onclose = () => {
      console.log("🔌 WS Disconnected");
    };

    // Cleanup: סגירת החיבור כשהקומפוננטה יורדת או כשהסשן מתחלף
    return () => {
      ws.close();
    };
  }, [sessionId]); // <--- הפונקציה תרוץ מחדש רק כשה-sessionId משתנה

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
    const startTime = Date.now();

    try {
      console.log("Hook: Sending prompt:", prompt);
      const data = await backend.sendPrompt(prompt, sessionId);

      // Backend returns { ok, output }, not { results }
      if (data.ok) {
        const output = data.output || "";
        const isFail = output.toUpperCase().includes("FAIL");
        const status = isFail ? "fail" : "pass";

        // Clean up output: Remove "STATE:" block and trim
        const cleanOutput = output.split(/STATE:/i)[0].trim();

        const duration = ((Date.now() - startTime) / 1000).toFixed(1) + "s";

        const newRun = {
          id: Date.now(),
          title: prompt.length > 30 ? prompt.substring(0, 30) + "..." : prompt,
          timestamp: new Date().toLocaleString(),
          steps: [
            {
              id: Date.now(),
              stepName: isFail
                ? "Action Failed"
                : cleanOutput || "Action Completed",
              status: status,
              errorMessage: isFail ? cleanOutput : undefined,
              timestamp: new Date().toLocaleTimeString(),
              duration: duration,
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

      // Add a failed run to history so user sees it in the log
      const newRun = {
        id: Date.now(),
        title: prompt.length > 30 ? prompt.substring(0, 30) + "..." : prompt,
        timestamp: new Date().toLocaleString(),
        steps: [
          {
            id: Date.now(),
            stepName: "System Error",
            status: "fail",
            errorMessage: errorMsg,
            timestamp: new Date().toLocaleTimeString(),
            duration: "0s",
          },
        ],
      };
      setTestHistory((prev) => [newRun, ...prev]);

      // Optional: still alert if critical
      // alert(`Test Failed: ${errorMsg}`);
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
