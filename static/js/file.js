//File Input JS
let currentGRNPage = 1;
let selectedGRNDate;
let totalPages = 1;

const fileInput = document.getElementById("file-input");
const fileListContainer = document.getElementById("file-list");
const button = document.getElementById("button");
const fileentry = document.getElementById("fileform");
fileentry.addEventListener("click", function () {
  fileInput.click();
});

fileInput.addEventListener("change", function () {
  fileListContainer.innerHTML = ""; // Clear previous file list

  Array.from(fileInput.files).forEach(function (file) {
    const fileItem = document.createElement("div");
    fileItem.classList.add("file-item");

    const fileName = document.createElement("span");

    fileName.textContent = file.name;
    fileItem.appendChild(fileName);

    var loadingIndicator = document.createElement("span");
    loadingIndicator.classList.add("loading-indicator");
    loadingIndicator.classList.add("animate");
    loadingIndicator.textContent = "⏳";
    fileItem.appendChild(loadingIndicator);

    fileListContainer.appendChild(fileItem);
  });
  button.style.display = "none";
});

document
  .getElementById("fileSubmit")
  .addEventListener("click", function (event) {
    event.preventDefault();
    var files = document.getElementById("file-input").files;
    if (files.length > 0) {
      var formData = new FormData();

      for (var i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
      }

      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/FILEDATA");
      xhr.onloadstart = function () {
        document
          .querySelectorAll(".loading-indicator")
          .forEach(function (indicator) {
            indicator.style.display = "inline"; // Show loading indicator
          });
      };
      xhr.onload = function () {
        var response = JSON.parse(xhr.responseText);
        updateFileStatus(response);
      };
      xhr.onerror = function () {
        updateFileStatus({
          error: "An error occurred while uploading files.",
        });
      };
      xhr.send(formData);
    }
  });

function updateFileStatus(response) {
  var fileListContainer = document.getElementById("file-list");

  for (var i = 0; i < response.length; i++) {
    var fileItem = fileListContainer.children[i];

    if (response[i].success) {
      fileItem.classList.add("success");
      fileItem.querySelector(".loading-indicator").textContent = "✔️"; // Success indicator
      fileItem.querySelector(".loading-indicator").classList.remove("animate");
    } else {
      fileItem.classList.add("error");
      fileItem.querySelector(".loading-indicator").textContent = "❌"; // Error indicator
      fileItem.querySelector(".loading-indicator").classList.remove("animate");
    }
  }
}

document
  .getElementById("filepickedDate")
  .addEventListener("change", function () {
    selectedGRNDate = this.value;
    if (selectedGRNDate) {
      fetchAndDisplayGRNData(selectedGRNDate);
    }
  });

function displayGRNData(data) {
  // data.sort((a, b) => a.item.localeCompare(b.item));
  const table = document.createElement("table");
  table.innerHTML = `
                  <tr>
                      <th style="width:35%">ITEM</th>
                      <th style="width:10%">QTY </th>
                      <th style="width:10%">PRICE</th>
                      <th style="width:13%">TOTAL</th>
                      <th >STORENAME</th>
                      <th>ACTIONS</th>
                  </tr>
              `;

  const startGRNIndex = (currentGRNPage - 1) * pageSize;
  const endGRNIndex = Math.min(startGRNIndex + pageSize, data.length);

  // Shorten the Store Name
  for (let i = startGRNIndex; i < endGRNIndex; i++) {
    const row = data[i];
    row.STORENAME = row.STORENAME.split("_")
      .map((part) => part.substring(0, Math.min(4, part.length)))
      .join("");
    if (row.STORENAME.length > 12) {
      const extraLettersToRemove = row.STORENAME.length - 12;
      row.STORENAME = row.STORENAME.substring(extraLettersToRemove);
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
                      <td>${row.ITEM}</td>
                      <td contenteditable="false">${row.QUANTITY}</td>
                      <td contenteditable="false">${row.PRICE}</td>
                      <td >${row.TOTAL}</td>
                      <td >${row.STORENAME}</td>
                     <td>
                      <span class="actions">
                      <span class="edit-icon" onclick="editRow(this, ${row.SR_NO})">✏️</span>
                      <span class="delete-icon" onclick="deleteRow(this, ${row.SR_NO})">🗑️</span>
                    </span>
                    </td>
                  `;
    table.appendChild(tr);
    updateGRNPagination();
  }

  const dataTable = document.getElementById("filedataTable");
  dataTable.innerHTML = "";
  dataTable.appendChild(table);
}
function fetchAndDisplayGRNData(date) {
  fetch(`/FILEDATA?reqdate=${date}`)
    .then((response) => response.json())
    .then((responseData) => {
      totalPages = Math.ceil(responseData.length / pageSize);
      displayGRNData(responseData);
    })
    .catch((error) => console.error("Error fetching data:", error));
}
// Function to update pagination controls based on current page and total pages
function updateGRNPagination() {
  document.getElementById(
    "currentGRNPage"
  ).textContent = `Page ${currentGRNPage}/${totalPages}`;
}

// Function to go to the first page
function showFirstPageGRNData() {
  currentGRNPage = 1;
  fetchAndDisplayGRNData(selectedGRNDate);
  updateGRNPagination();
}
function showPrevGRNData() {
  if (currentGRNPage > 1) {
    currentGRNPage--;
    fetchAndDisplayGRNData(selectedGRNDate);
    updateGRNPagination();
  }
}

function showNextGRNData() {
  currentGRNPage++;
  fetchAndDisplayGRNData(selectedGRNDate);
  updateGRNPagination();
}
function showLastPageGRNData() {
  //   currentGRNPage = totalPages;
  console.log(selectedGRNDate);
  fetchAndDisplayGRNData(selectedGRNDate);
  updateGRNPagination();
}

function editRow(editIcon, srNo) {
  console.log("Editing row:", srNo); // Debugging log
  const row = editIcon.closest("tr");
  row.classList.add("focused-row");
  row.cells[1].contentEditable = "true";
  row.cells[2].contentEditable = "true";

  row.cells[1].classList.add("editable");
  row.cells[2].classList.add("editable");
  console.log("clicked");
  const saveButton = document.createElement("button");
  saveButton.textContent = "Save";
  saveButton.onclick = function () {
    const quantity = row.cells[1].textContent;
    const price = row.cells[2].textContent;
    const total = quantity * price;
    row.cells[3].textContent = total.toFixed(2);

    const updatedData = {
      SR_NO: srNo,
      QUANTITY: quantity,
      PRICE: price,
      TOTAL: total,
    };

    fetch(`/updateRow`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updatedData),
    })
      .then((response) => response.json())
      .then((data) => {
        showNotification("Row updated successfully", "success");
        row.classList.remove("focused-row");
        row.cells[1].contentEditable = "false";
        row.cells[2].contentEditable = "false";
        row.cells[1].classList.remove("editable");
        row.cells[2].classList.remove("editable");
        saveButton.remove();
      })
      .catch((error) => {
        showNotification("Error updating row", "error");

        console.error("Error updating row:", error);
      });
  };

  row.cells[5].appendChild(saveButton);
}

function showNotification(message, type) {
  const notification = document.getElementById("notification");
  notification.textContent = message;
  notification.classList.add(type);
  notification.classList.add("show");

  setTimeout(() => {
    notification.classList.remove("show");
    notification.classList.remove(type);
  }, 3000); // Remove notification after 3 seconds
}

function deleteRow(deleteIcon, srNo) {
  fetch(`/deleteRow`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ SR_NO: srNo }),
  })
    .then((response) => response.json())
    .then((data) => {
      showNotification("Row deleted successfully", "success");
      fetchAndDisplayGRNData(selectedGRNDate); // Refresh the table data
    })
    .catch((error) => {
      showNotification("Error deleting row", "error");
      console.error("Error deleting row:", error);
    });
}
updateGRNPagination();
