import { useState, useEffect, useRef } from "react";
import { backend } from "../services/backend";

export const useTestAgent = () => {
  const [sessionId, setSessionId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [isFullScanning, setIsFullScanning] = useState(false);
  const [testHistory, setTestHistory] = useState([]);

  // Buffer for incoming logs to prevent excessive re-renders
  const logBufferRef = useRef([]);

  // -------------------------------------------
  // WebSocket Listener with Batching
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
        const msg = JSON.parse(event.data);

        // -------------------------------------------
        // 1. Handle Failure Analysis (The Good Stuff)
        // -------------------------------------------
        if (msg.type === "failure_analysis") {
          const analysis = msg.data;

          const newEntry = {
            id: Date.now() + Math.random(),
            type: "failure_card", // Custom type for rendering
            status: "fail", // Triggers red styling
            title: analysis.failure_category || "Unknown Failure",
            summary: analysis.summary,
            fix: analysis.suggested_fix,
            reason: analysis.why,
            timestamp: new Date().toLocaleTimeString(),
            steps: [], // Empty steps as we render a custom card
          };
          logBufferRef.current.push(newEntry);
          return;
        }

        // -------------------------------------------
        // 2. Handle Standard Logs (Smart Filtering)
        // -------------------------------------------
        const content = msg.content || msg.message || JSON.stringify(msg);

        // FILTER LOGIC:
        // If it looks like a raw error/failure, IGNORE IT.
        // We trust the "failure_analysis" event to handle it beautifully.
        if (/error|fail|timeout|exception/i.test(content)) {
          return;
        }

        // Otherwise, display as info/pass
        let status = "info";
        if (/pass|success/i.test(content)) status = "pass";
        else if (/processing|running|start/i.test(content)) status = "running";

        const newEntry = {
          id: Date.now() + Math.random(),
          title: "System Event",
          timestamp: new Date().toLocaleString(),
          isLog: true,
          steps: [
            {
              id: Date.now(),
              stepName: content,
              status: status,
              description: msg.details || "",
              timestamp: new Date().toLocaleTimeString(),
              duration: "0.1s",
            },
          ],
        };

        logBufferRef.current.push(newEntry);
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

  // -------------------------------------------
  // Flush Loop (Interval)
  // -------------------------------------------
  useEffect(() => {
    const intervalId = setInterval(() => {
      if (logBufferRef.current.length > 0) {
        const newLogs = [...logBufferRef.current];
        logBufferRef.current = []; // Clear buffer

        setTestHistory((prev) => {
          // Combine and limit to last 200 items to prevent memory issues
          // Note: We prepend new logs because the UI shows newest first
          const updated = [...newLogs.reverse(), ...prev];
          return updated.slice(0, 200);
        });
      }
    }, 500); // Flush every 500ms

    return () => clearInterval(intervalId);
  }, []);

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
    sessionId,
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
