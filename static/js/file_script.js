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

// function refetchTableContainer() {
//   const currentFolderId = '{{ current_folder.id if current_folder else "" }}';

//   fetch(`{{ url_for('main.list_files') }}?folder_id=${currentFolderId}`)
//     .then((response) => response.text())
//     .then((html) => {
//       const tempDiv = document.createElement("div");
//       tempDiv.innerHTML = html;
//       const newTableBody = tempDiv.querySelector("#file-list-body");
//       const tableContainer = document.querySelector(".table-container tbody");

//       // Replace the old table body with the new one
//       if (newTableBody && tableContainer) {
//         tableContainer.innerHTML = newTableBody.innerHTML;
//       }

//       // Reapply formatting to the newly fetched elements
//       applyFormatting();
//     })
//     .catch((error) => {
//       console.error("Error refetching table container:", error);
//     });
// }

function uploadFile(file) {
  let url = "/upload";
  let formData = new FormData();
  const parentId = '{{ current_folder.id if current_folder else "" }}';
  formData.append("file", file);
  formData.append("parent_id", parentId);

  let gallery = document.getElementById("gallery");

  let fileContainer = document.createElement("div");
  fileContainer.classList.add("file-container");

  let fileIcon = document.createElement("i");
  fileIcon.classList.add("file-icon");

  // Determine the file type and set the appropriate icon
  let fileType = file.type.split("/")[0];
  switch (fileType) {
    case "image":
      fileIcon.classList.add("fas", "fa-image");
      break;
    case "application":
      if (file.type.includes("pdf")) {
        fileIcon.classList.add("fas", "fa-file-pdf");
      } else {
        fileIcon.classList.add("fas", "fa-file-alt");
      }
      break;
    case "text":
      fileIcon.classList.add("fas", "fa-file-alt");
      break;
    default:
      fileIcon.classList.add("fas", "fa-file");
      break;
  }

  let fileDetails = document.createElement("div");
  fileDetails.classList.add("file-details");

  let fileName = document.createElement("div");
  fileName.classList.add("file-name");
  fileName.textContent = file.name;

  let fileSize = document.createElement("div");
  fileSize.classList.add("file-size");
  fileSize.textContent = formatFileSize(file.size);

  fileDetails.appendChild(fileName);
  fileDetails.appendChild(fileSize);

  let progressWrapper = document.createElement("div");
  progressWrapper.classList.add("progress-wrapper");

  let progressBar = document.createElement("progress");
  progressBar.classList.add("progress-bar");
  progressBar.max = 100;
  progressBar.value = 0;

  progressWrapper.appendChild(progressBar);

  fileContainer.appendChild(fileIcon);
  fileContainer.appendChild(fileDetails);
  fileContainer.appendChild(progressWrapper);
  gallery.appendChild(fileContainer);

  fetch(url, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("File uploaded successfully:", data);
      progressBar.value = 100;
      // refetchTableContainer(); // Refetch the table container
    })
    .catch((error) => {
      console.error("Error uploading file:", error);
      progressBar.value = 0; // Reset on error
    });

  // Simulate progress for the sake of the example (remove this in a real implementation)
  let simulateProgress = setInterval(() => {
    if (progressBar.value < 100) {
      progressBar.value += 10;
    } else {
      clearInterval(simulateProgress);
    }
  }, 100);
}

document.addEventListener("DOMContentLoaded", function () {
  let currentPage = "{{ files.page }}";
  const perPage = "{{ files.per_page }}";
  const totalPages = "{{ files.pages }}";
  const fileListBody = document.getElementById("file-list-body");
  const tableContainer = document.querySelector(".table-container");
  const loadingIndicator = document.getElementById("loading-indicator");
  let isLoading = false;

  function formatDate(utcDateStr) {
    const date = new Date(utcDateStr + "Z");
    const options = { year: "numeric", month: "short", day: "numeric" };
    return new Intl.DateTimeFormat(navigator.language, options).format(date);
  }

  function formatFileSize(bytes) {
    const units = ["Bytes", "KB", "MB", "GB", "TB", "PB"];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }

  function applyFormatting() {
    // Format dates and file sizes for existing elements
    document.querySelectorAll(".upload-date").forEach((el) => {
      const utcDateStr = el.getAttribute("data-utc");
      if (utcDateStr) {
        el.textContent = formatDate(utcDateStr);
      } else {
        el.textContent = "Invalid date";
      }
    });

    document.querySelectorAll(".file-size").forEach((el) => {
      const sizeInBytes = parseInt(el.getAttribute("data-size"), 10);
      if (!isNaN(sizeInBytes)) {
        el.textContent = formatFileSize(sizeInBytes);
      } else {
        el.textContent = "Invalid size";
      }
    });
  }

  function appendFiles(html) {
    // Create a temporary container to parse the HTML
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = html;
    const newRows = tempDiv.querySelectorAll("#file-list-body tr");

    newRows.forEach((row) => {
      fileListBody.appendChild(row);
    });

    // Reapply formatting to newly added elements
    applyFormatting();
  }

  function fetchNextPage() {
    if (isLoading || currentPage >= totalPages) return;
    isLoading = true;
    loadingIndicator.style.display = "block";

    fetch(
      `{{ url_for('main.list_files') }}?page=${
        currentPage + 1
      }&per_page=${perPage}`
    )
      .then((response) => response.text())
      .then((html) => {
        // Check if there are new files in the response
        if (html.includes('<tbody id="file-list-body">')) {
          appendFiles(html);
          currentPage++;
        }
        isLoading = false;
        loadingIndicator.style.display = "none";
      })
      .catch((error) => {
        console.error("Error fetching files:", error);
        isLoading = false;
        loadingIndicator.style.display = "none";
      });
  }

  // Debounce function
  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }

  // Create a debounced version of fetchNextPage
  const debouncedFetchNextPage = debounce(fetchNextPage, 200);

  // Initial formatting for existing elements
  applyFormatting();

  tableContainer.addEventListener("scroll", () => {
    if (
      tableContainer.scrollTop + tableContainer.clientHeight >=
      tableContainer.scrollHeight - 200
    ) {
      debouncedFetchNextPage();
    }
  });

  const searchBar = document.getElementById("search-bar");
  const searchDropdown = document.getElementById("search-dropdown");

  // Show dropdown when search bar is focused
  searchBar.addEventListener("focus", function () {
    searchBar.classList.add("active");
    searchDropdown.classList.add("show");
  });

  // Hide dropdown and reset search bar shape when clicking outside
  document.addEventListener("click", function (event) {
    if (
      !searchBar.contains(event.target) &&
      !searchDropdown.contains(event.target)
    ) {
      searchDropdown.classList.remove("show");
      searchBar.classList.remove("active");
    }
  });

  // Handle advanced search button click
  document
    .getElementById("advanced-search-btn")
    .addEventListener("click", function () {
      // Redirect to advanced search page or show advanced search options
      alert("Advanced Search clicked!");
    });

  const newButton = document.querySelector(".sidebar .fa-plus").parentElement;
  const infobar = document.getElementById("new-options-infobar");
  const uploadPopup = document.getElementById("upload-popup");
  const closePopup = document.getElementById("close-popup");
  const newFolderPopup = document.getElementById("new-folder-popup");
  const closeNewFolderPopup = document.getElementById("close-new-folder-popup");

  // Show infobar
  newButton.addEventListener("click", function (event) {
    event.stopPropagation(); // Prevent event from propagating to window click event
    infobar.style.display =
      infobar.style.display === "block" ? "none" : "block";
  });

  // Hide infobar when clicking outside
  window.addEventListener("click", function (event) {
    if (event.target !== newButton && !infobar.contains(event.target)) {
      infobar.style.display = "none";
    }
  });

  document
    .getElementById("create-folder-btn")
    .addEventListener("click", function () {
      newFolderPopup.style.display = "flex"; // Show the new folder popup
    });

  document
    .getElementById("upload-file-btn")
    .addEventListener("click", function () {
      uploadPopup.style.display = "flex";
    });

  // Close the upload popup
  closePopup.addEventListener("click", function () {
    uploadPopup.style.display = "none";
  });

  // Hide upload popup when clicking outside
  window.addEventListener("click", function (event) {
    if (event.target === uploadPopup) {
      uploadPopup.style.display = "none";
    }
  });

  // Close the new folder popup
  closeNewFolderPopup.addEventListener("click", function () {
    newFolderPopup.style.display = "none";
  });

  // Hide new folder popup when clicking outside
  window.addEventListener("click", function (event) {
    if (event.target === newFolderPopup) {
      newFolderPopup.style.display = "none";
    }
  });

  const createFolderConfirmBtn = document.getElementById(
    "create-folder-confirm-btn"
  );
  const folderNameInput = document.getElementById("folder-name-input");

  createFolderConfirmBtn.addEventListener("click", function () {
    const folderName = folderNameInput.value.trim();
    const parentId = '{{ current_folder.id if current_folder else "" }}';

    if (folderName) {
      fetch("/create_folder", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          folder_name: folderName,
          parent_id: parentId,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.error) {
            // alert(data.error);
          } else {
            // alert(data.message);
            // refetchTableContainer(); // Refetch the table container
            newFolderPopup.style.display = "none"; // Hide the folder popup
          }
        })
        .catch((error) => {
          console.error("Error creating folder:", error);
          alert("An error occurred while creating the folder.");
        });
    } else {
      alert("Folder name cannot be empty.");
    }
  });
});
