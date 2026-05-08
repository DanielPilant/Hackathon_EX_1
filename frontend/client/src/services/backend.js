import axios from "axios";
import { API_BASE_URL } from "../config";

export const backend = {
  // 1. Create Session
  createSession: async (url, allowedDomain) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/sessions`, {
        start_url: url,
        allowed_domain: allowedDomain,
      });
      return response.data; // Returns { session_id, snapshot }
    } catch (error) {
      console.error("Backend: Create session failed:", error);
      throw error;
    }
  },

  // 2. Send Prompt
  sendPrompt: async (prompt, sessionId) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/sessions/${sessionId}/prompt`,
        {
          prompt: prompt,
          max_attempts: 4,
        }
      );
      return response.data; // Returns { ok, output, snapshot }
    } catch (error) {
      console.error("Backend: Send prompt failed:", error);
      throw error;
    }
  },

  // 3. Get Suggestion
  getSuggestion: async (sessionId) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/sessions/${sessionId}/suggest`
      );
      return response.data; // Returns { suggestion: "..." }
    } catch (error) {
      console.error("Backend: Get suggestion failed:", error);
      throw error;
    }
  },

  // 4. Get Manual Suggestions (Deep Scan)
  getManualSuggestions: async (sessionId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/sessions/${sessionId}/suggestions`
      );
      return response.data;
    } catch (error) {
      console.error("Backend: Get manual suggestions failed:", error);
      throw error;
    }
  },

  // Alias for Deep Scan
  getPageSuggestions: async (sessionId) => {
    return backend.getManualSuggestions(sessionId);
  },

  // 5. Reset browser to blank (called on frontend page load to give a clean slate)
  resetBrowser: async () => {
    try {
      await axios.post(`${API_BASE_URL}/browser/reset`);
    } catch (error) {
      console.warn("Backend: browser reset failed (non-fatal):", error);
    }
  },

  // 6. Log to Terminal
  logToTerminal: async (data) => {
    try {
      await axios.post(`${API_BASE_URL}/client-log`, { message: data });
    } catch (error) {
      console.error("Backend: Log to terminal failed:", error);
    }
  },
};
