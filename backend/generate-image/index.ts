/**
 * Business: Generate AI-styled images using Google Gemini API
 * Args: event with POST body containing imageBase64; context with requestId
 * Returns: HTTP response with generated image data
 */

const { GoogleGenerativeAI } = require("@google/generative-ai");

module.exports.handler = async (event, context) => {
  const { httpMethod, body } = event;

  if (httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
      },
      body: "",
    };
  }

  if (httpMethod !== "POST") {
    return {
      statusCode: 405,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({ error: "Method not allowed" }),
    };
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return {
      statusCode: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({ error: "API key not configured" }),
    };
  }

  const requestData = JSON.parse(body || "{}");
  const { imageBase64 } = requestData;

  if (!imageBase64) {
    return {
      statusCode: 400,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({ error: "Image is required" }),
    };
  }

  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

  const customPrompt = `Transform this image into a vintage-style greeting card with warm, nostalgic colors. 
Add a soft glow effect and make it look like a classic handmade postcard from the 1960s. 
Keep the main subject but enhance it with artistic flourishes and decorative elements in a retro style.`;

  const imageParts = [
    {
      inlineData: {
        data: imageBase64.split(",")[1],
        mimeType: imageBase64.split(";")[0].split(":")[1],
      },
    },
  ];

  try {
    const result = await model.generateContent([customPrompt, ...imageParts]);
    const response = result.response;
    const generatedText = response.text();

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      isBase64Encoded: false,
      body: JSON.stringify({
        success: true,
        result: generatedText,
        requestId: context.requestId,
      }),
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      isBase64Encoded: false,
      body: JSON.stringify({
        success: false,
        error: error.message || "Generation failed",
        requestId: context.requestId,
      }),
    };
  }
};