document.addEventListener("DOMContentLoaded", () => {
  const toasts = document.querySelectorAll(".toast");

  toasts.forEach((toast) => {
    window.setTimeout(() => {
      toast.remove();
    }, 4000);
  });
});