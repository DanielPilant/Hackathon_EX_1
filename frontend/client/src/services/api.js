import axios from "axios";
import { MOCK_TEST_RESULTS } from "../data/mockData";

const USE_MOCK = true;
const API_BASE_URL = "http://localhost:8000/api"; // Placeholder for future backend

const simulateDelay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const apiService = {
  /**
   * Sets the target URL for the test session.
   * @param {string} url
   * @returns {Promise<{status: string, message: string}>}
   */
  setTargetUrl: async (url) => {
    if (USE_MOCK) {
      console.log(`[Mock API] Setting target URL: ${url}`);
      await simulateDelay(1500);
      return { status: "success", message: "Target locked" };
    } else {
      const response = await axios.post(`${API_BASE_URL}/target`, { url });
      return response.data;
    }
  },

  /**
   * Sends the user prompt to the AI agent and retrieves test results.
   * @param {string} prompt
   * @returns {Promise<{status: string, results: Array}>}
   */
  sendPrompt: async (prompt) => {
    if (USE_MOCK) {
      console.log(`[Mock API] Sending prompt: ${prompt}`);
      await simulateDelay(3000);
      return { status: "completed", results: MOCK_TEST_RESULTS };
    } else {
      const response = await axios.post(`${API_BASE_URL}/generate`, { prompt });
      return response.data;
    }
  },
};
