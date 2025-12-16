import { useState, useEffect, useCallback } from "react";
import { apiService } from "../services/api";

export const useTestAgent = () => {
  const [userId, setUserId] = useState("");
  const [testHistory, setTestHistory] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [isFullScanning, setIsFullScanning] = useState(false);

  // Generate Session ID on mount
  useEffect(() => {
    const newUserId = `user_${Date.now()}_${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    setUserId(newUserId);
    console.log("Session ID:", newUserId);
  }, []);

  const connectToUrl = useCallback(
    async (url) => {
      if (!url) return;
      setIsScanning(true);
      try {
        await apiService.setTargetUrl(url, userId);
        setIsConnected(true);
      } catch (error) {
        console.error("Connection failed:", error);
      } finally {
        setIsScanning(false);
      }
    },
    [userId]
  );

  const runPrompt = useCallback(
    async (prompt) => {
      if (!prompt || !isConnected) return;

      setIsRunningTest(true);
      try {
        const response = await apiService.sendPrompt(prompt, userId);

        if (response.status === "completed") {
          const newRun = {
            id: Date.now(),
            title: response.title || "Untitled Test Run",
            timestamp: new Date().toLocaleString(),
            steps: response.results,
          };
          setTestHistory((prev) => [newRun, ...prev]);
        }
      } catch (error) {
        console.error("Test execution failed:", error);
      } finally {
        setIsRunningTest(false);
      }
    },
    [userId, isConnected]
  );

  const runFullScan = useCallback(async () => {
    if (!isConnected) return;

    setIsFullScanning(true);
    try {
      const response = await apiService.runFullSiteScan(userId);

      if (response.status === "completed") {
        const newRun = {
          id: Date.now(),
          title: response.title || "Full Site Scan",
          timestamp: new Date().toLocaleString(),
          steps: response.results,
        };
        setTestHistory((prev) => [newRun, ...prev]);
      }
    } catch (error) {
      console.error("Full scan failed:", error);
    } finally {
      setIsFullScanning(false);
    }
  }, [userId, isConnected]);

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
