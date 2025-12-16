export const setTargetUrl = async (url) => {
  console.log("Setting target URL:", url);
  return new Promise((resolve) => setTimeout(resolve, 1000));
};

export const sendPrompt = async (prompt) => {
  console.log("Sending prompt:", prompt);
  return new Promise((resolve) => setTimeout(resolve, 2000));
};
