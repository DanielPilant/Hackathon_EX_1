import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

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
};
