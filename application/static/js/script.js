// Function to show the modal
function showModal(modalId) {
  var modal = new bootstrap.Modal(document.getElementById(modalId));
  modal.show();
}

// Function to close the modal
function closeModal(modalId) {
  var modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
  modal.hide();
}

// Attach click event listener to the login button
document.getElementById("login").addEventListener("click", function () {
  showModal("loginModal");
});

// Attach click event listener to the register button
document.getElementById("register").addEventListener("click", function () {
  showModal("registerModal");
});


// Attach click event listener to the modal close buttons
document
  .querySelectorAll(".modal .btn-close")
  .forEach(function (closeButton) {
    closeButton.addEventListener("click", function () {
      var modalId = this.closest(".modal").id;
      closeModal(modalId);
    });
  });