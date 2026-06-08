document.addEventListener("DOMContentLoaded", () => {
  const toasts = document.querySelectorAll(".toast");

  toasts.forEach((toast) => {
    // Add close button dynamically
    const closeBtn = document.createElement("button");
    closeBtn.className = "toast__close";
    closeBtn.innerHTML = "&times;";
    closeBtn.setAttribute("aria-label", "Fechar notificação");
    closeBtn.style.background = "none";
    closeBtn.style.border = "none";
    closeBtn.style.color = "currentColor";
    closeBtn.style.fontSize = "1.25rem";
    closeBtn.style.lineHeight = "1";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.padding = "0 4px";
    closeBtn.style.marginLeft = "auto";
    closeBtn.style.opacity = "0.7";
    closeBtn.style.transition = "opacity 0.2s";
    
    closeBtn.addEventListener("mouseover", () => closeBtn.style.opacity = "1");
    closeBtn.addEventListener("mouseout", () => closeBtn.style.opacity = "0.7");
    
    let timeoutId;
    
    const dismiss = () => {
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "opacity 0.2s ease, transform 0.2s ease";
      window.setTimeout(() => toast.remove(), 200);
    };

    closeBtn.addEventListener("click", dismiss);
    toast.appendChild(closeBtn);

    timeoutId = window.setTimeout(dismiss, 5000);
  });
});