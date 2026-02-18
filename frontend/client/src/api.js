import axios from "axios";
import { API_BASE_URL } from "./config";

// זו הכתובת של הבאקנד החדש שלך (המוח)

export const apiService = {
  // פונקציה 1: מתחילה שיחה חדשה
  // היא מקבלת URL ודומיין, ושולחת אותם לשרת
  createSession: async (url, domain) => {
    const response = await axios.post(`${API_BASE_URL}/sessions`, {
      start_url: url,
      allowed_domain: domain,
    });
    // השרת מחזיר אובייקט עם session_id. אנחנו מחזירים אותו למי שקרא לנו.
    return response.data;
  },

  // פונקציה 2: שולחת הוראה (פרומפט)
  // היא חייבת לקבל את ה-sessionId כדי שהשרת יידע על איזה דפדפן מדובר
  sendPrompt: async (prompt, sessionId) => {
    const response = await axios.post(
      `${API_BASE_URL}/sessions/${sessionId}/prompt`,
      {
        prompt: prompt,
        max_attempts: 4,
      }
    );
    return response.data;
  },
};
