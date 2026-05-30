document.addEventListener("DOMContentLoaded", () => {
  const toasts = document.querySelectorAll(".toast");

  toasts.forEach((toast) => {
    window.setTimeout(() => {
      toast.classList.add("toast--hide");
      window.setTimeout(() => toast.remove(), 300);
    }, 4000);
  });
});