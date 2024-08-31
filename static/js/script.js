let dropArea = document.getElementById("drop-area");

["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

["dragenter", "dragover"].forEach((eventName) => {
  dropArea.addEventListener(
    eventName,
    () => dropArea.classList.add("highlight"),
    false
  );
});

["dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(
    eventName,
    () => dropArea.classList.remove("highlight"),
    false
  );
});

dropArea.addEventListener("drop", handleDrop, false);

function handleDrop(e) {
  let dt = e.dataTransfer;
  let files = dt.files;

  handleFiles(files);
}

function handleFiles(files) {
  [...files].forEach(uploadFile);
}

// function uploadFile(file) {
//   let url = "/upload";
//   let formData = new FormData();
//   formData.append("file", file);

//   let gallery = document.getElementById("gallery");

//   let fileContainer = document.createElement("div");
//   fileContainer.classList.add("file-container");

//   let fileName = document.createElement("div");
//   fileName.classList.add("file-name");
//   fileName.textContent = file.name;

//   let progressWrapper = document.createElement("div");
//   progressWrapper.classList.add("progress-wrapper");

//   let progressBar = document.createElement("progress");
//   progressBar.classList.add("progress-bar");
//   progressBar.max = 100;
//   progressBar.value = 0;

//   progressWrapper.appendChild(progressBar);
//   fileContainer.appendChild(fileName);
//   fileContainer.appendChild(progressWrapper);
//   gallery.appendChild(fileContainer);

//   fetch(url, {
//     method: "POST",
//     body: formData,
//   })
//     .then((response) => response.json())
//     .then((data) => {
//       console.log("File uploaded successfully:", data);
//       progressBar.value = 100;
//     })
//     .catch((error) => {
//       console.error("Error uploading file:", error);
//       progressBar.value = 0; // Reset on error
//     });

//   // Simulate progress for the sake of the example (remove this in a real implementation)
//   let simulateProgress = setInterval(() => {
//     if (progressBar.value < 100) {
//       progressBar.value += 10;
//     } else {
//       clearInterval(simulateProgress);
//     }
//   }, 100);
// }

function formatFileSize(bytes) {
  const units = ["Bytes", "KB", "MB", "GB", "TB"];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}
