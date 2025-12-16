import axios from "axios";
import { MOCK_TEST_RESULTS, MOCK_FULL_SCAN_RESULTS } from "../data/mockData";

const USE_MOCK = true;
const API_BASE_URL = "http://localhost:8000/api"; // Placeholder for future backend

const simulateDelay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const apiService = {
  /**
   * Sets the target URL for the test session.
   * @param {string} url
   * @param {string} userId
   * @returns {Promise<{status: string, message: string}>}
   */
  setTargetUrl: async (url, userId) => {
    // Construct the exact payload expected by the backend
    const payload = {
      user_id: userId,
      url: url,
    };

    if (USE_MOCK) {
      console.log(
        "🚀 [Mock Request] setTargetUrl Payload:",
        JSON.stringify(payload, null, 2)
      );
      await simulateDelay(2000);
      return {
        status: "success",
        message: "Target scanned and loaded into memory",
      };
    } else {
      const response = await axios.post(`${API_BASE_URL}/target`, payload);
      return response.data;
    }
  },

  /**
   * Sends the user prompt to the AI agent and retrieves test results.
   * @param {string} prompt
   * @param {string} userId
   * @returns {Promise<{status: string, title: string, results: Array}>}
   */
  runTestPrompt: async (prompt, userId) => {
    // Construct the exact payload expected by the backend
    const payload = {
      user_id: userId,
      prompt: prompt,
    };

    if (USE_MOCK) {
      console.log(
        "🚀 [Mock Request] runTestPrompt Payload:",
        JSON.stringify(payload, null, 2)
      );
      await simulateDelay(3000);

      // Mock Title Generation Logic (Simulating LLM summarization)
      let title = "Ad-hoc User Test";
      const p = prompt.toLowerCase();
      if (p.includes("login") || p.includes("sign in")) {
        title = "Login Validation - Negative Flow";
      } else if (p.includes("cart") || p.includes("checkout")) {
        title = "E-commerce Checkout Flow";
      } else if (p.includes("search")) {
        title = "Search Functionality Verification";
      } else if (p.includes("form") || p.includes("contact")) {
        title = "Form Submission Test";
      } else if (p.length > 0) {
        // Capitalize first letter and truncate
        title = prompt.charAt(0).toUpperCase() + prompt.slice(1, 25) + (prompt.length > 25 ? "..." : "");
      }

      return { 
        status: "completed", 
        title: title,
        results: MOCK_TEST_RESULTS 
      };
    } else {
      const response = await axios.post(`${API_BASE_URL}/generate`, payload);
      return response.data;
    }
  },

  /**
   * Triggers a full autonomous site scan.
   * @param {string} userId
   * @returns {Promise<{status: string, title: string, results: Array}>}
   */
  runFullSiteScan: async (userId) => {
    // Construct the exact payload expected by the backend
    const payload = {
      user_id: userId,
      action: "full_scan",
    };

    if (USE_MOCK) {
      console.log(
        "🚀 [Mock Request] runFullSiteScan Payload:",
        JSON.stringify(payload, null, 2)
      );
      await simulateDelay(3000);
      return { 
        status: "completed", 
        title: "Autonomous Full Site Audit",
        results: MOCK_FULL_SCAN_RESULTS 
      };
    } else {
      const response = await axios.post(`${API_BASE_URL}/scan`, payload);
      return response.data;
    }
  },
};
