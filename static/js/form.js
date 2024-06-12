document
  .getElementById("dataForm")
  .addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent default form submission

    // Perform any necessary actions here, such as sending an AJAX request to submit the form data
    sendDataToServer();

    // Display a notification or perform other actions as needed
    document.getElementById("notification").style.display = "block";
    clearForm();
    setTimeout(function () {
      document.getElementById("notification").style.display = "none";
    }, 3000); // Hide notification after 3 seconds
  });

// JavaScript function to send form data to the server
function sendDataToServer() {
  // Example code to send form data using AJAX (you need to implement this according to your server-side logic)
  var formData = new FormData(document.getElementById("dataForm"));
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/submit", true);
  xhr.send(formData);
}

let currentPage = 1;
const pageSize = 10; // Number of rows per page
let selectedDate;
// Add event listener to date input to fetch data on date change
document.getElementById("pickedDate").addEventListener("change", function () {
  selectedDate = this.value;
  if (selectedDate) {
    fetchAndDisplayData(selectedDate);
  }
});

function displayData(data) {
  // data.sort((a, b) => a.item.localeCompare(b.item));
  const table = document.createElement("table");
  table.innerHTML = `
              <tr>
                  
                  <th style="width:50%">Item</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>Total</th>
              </tr>
          `;

  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, data.length);

  for (let i = startIndex; i < endIndex; i++) {
    const row = data[i];
    const tr = document.createElement("tr");
    tr.innerHTML = `
                  <td>${row.item}</td>
                  <td>${row.qty}</td>
                  <td>${row.price}</td>
                  <td>${row.total}</td>
              `;
    table.appendChild(tr);
  }

  const dataTable = document.getElementById("dataTable");
  dataTable.innerHTML = "";
  dataTable.appendChild(table);
}

// Function to update pagination controls based on current page and total pages
function updatePagination() {
  document.getElementById("currentPage").textContent = `Page ${currentPage}`;
}

function fetchAndDisplayData(date) {
  fetch(`/get_data?reqdate=${date}`)
    .then((response) => response.json())
    .then((responseData) => {
      displayData(responseData);
    })
    .catch((error) => console.error("Error fetching data:", error));
}
// Function to go to the first page
function showFirstPageData() {
  currentPage = 1;
  fetchAndDisplayData(selectedDate);
  updatePagination();
}
function showPrevData() {
  if (currentPage > 1) {
    currentPage--;
    fetchAndDisplayData(selectedDate);
    updatePagination();
  }
}

function showNextData() {
  currentPage++;
  fetchAndDisplayData(selectedDate);
  updatePagination();
}
function showLastPageData() {
  currentPage = totalPages;
  fetchAndDisplayData(selectedDate);
  updatePagination();
}

// Initially fetch and display data for the first page
// fetchAndDisplayData(selectedDate);
updatePagination();

// JavaScript for calculating total price
document.getElementById("price").addEventListener("input", updateTotal);

function updateTotal() {
  var qty = parseFloat(document.getElementById("qty").value);
  var price = parseFloat(document.getElementById("price").value);
  var total = qty * price;
  document.getElementById("total").value = total.toFixed(2);
}

function clearForm() {
  document.getElementById("item").value = "";
  document.getElementById("qty").value = "";
  document.getElementById("price").value = "";
  document.getElementById("total").value = "";
}
