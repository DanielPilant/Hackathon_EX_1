import axios from "axios";

const API_BASE_URL = "http://localhost:8000"; // כתובת השרת החדש

export const apiService = {
  // 1. יצירת סשן חדש (במקום setTargetUrl)
  connectToUrl: async (url, allowedDomain = "savingplan.web.app") => {
    try {
      const response = await axios.post(`${API_BASE_URL}/sessions`, {
        start_url: url,
        allowed_domain: allowedDomain,
      });
      // השרת מחזיר session_id, אנחנו צריכים לשמור אותו
      return {
        status: "success",
        sessionId: response.data.session_id,
        snapshot: response.data.snapshot,
      };
    } catch (error) {
      console.error("Connection failed:", error);
      throw error;
    }
  },

  // 2. שליחת פרומפט (במקום sendPrompt)
  runPrompt: async (prompt, sessionId) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/sessions/${sessionId}/prompt`,
        {
          prompt: prompt,
          max_attempts: 4,
        }
      );

      // המרת התשובה הטקסטואלית של ה-Agent למבנה שהפרונט מכיר
      // (בשרת הנוכחי הוא מחזיר טקסט ולא JSON של צעדים, אז אנחנו עוטפים אותו)
      return {
        status: "completed",
        results: [
          {
            id: Date.now(),
            stepName: "AI Execution Report",
            status: "pass", // מניחים הצלחה אם ה-HTTP עבר
            description: response.data.output, // הטקסט שה-AI כתב
            timestamp: new Date().toLocaleTimeString(),
          },
        ],
      };
    } catch (error) {
      console.error("Prompt failed:", error);
      return {
        status: "failed",
        results: [
          {
            id: Date.now(),
            stepName: "System Error",
            status: "fail",
            description: error.message,
            timestamp: new Date().toLocaleTimeString(),
          },
        ],
      };
    }
  },
};
