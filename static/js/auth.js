function getApiKey() {
  const apiKey = localStorage.getItem("apiKey");
  const apiKeyExpiration = localStorage.getItem("apiKeyExpiration");

  if (apiKey && apiKeyExpiration) {
    const expirationDate = new Date(apiKeyExpiration);
    if (new Date() < expirationDate) {
      return apiKey;
    } else {
      // API key expired, remove from local storage
      localStorage.removeItem("apiKey");
      localStorage.removeItem("apiKeyExpiration");
      alert("API key expired. Please log in again.");
      window.location.href = "/auth/login"; // Redirect to login page
      return null;
    }
  }
  window.location.href = "/auth/login"; // Redirect to login page if no API key is found
  return null;
}

// Function to make a request with the API key
function makeAuthenticatedRequest(url, options = {}) {
  const apiKey = getApiKey();
  if (!apiKey) {
    return Promise.reject("No valid API key found");
  }

  // Ensure headers exist in options
  if (!options.headers) {
    options.headers = {};
  }

  // Add the API key to the headers
  options.headers["x-api-key"] = apiKey;

  return fetch(url, options)
    .then((response) => {
      if (response.status === 401) {
        alert("Unauthorized access. Please log in again.");
        window.location.href = "/auth/login";
      }
      return response;
    })
    .catch((error) => {
      console.error("Request failed:", error);
    });
}

// Automatically add the API key to all fetch requests on page load
document.addEventListener("DOMContentLoaded", () => {
  const apiKey = getApiKey();
  if (!apiKey) {
    // If no valid API key is found, redirect to login
    window.location.href = "/auth/login";
  }
});
