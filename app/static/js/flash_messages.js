$(document).ready(function () {
  // Remove the flash message after 2 seconds (2000 milliseconds)
  setTimeout(function () {
    $(".alert").alert("close");
  }, 2000);
});
