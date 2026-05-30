document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll("[data-cpf-mask]");

  const formatCpf = (value) => {
    const digits = value.replace(/\D/g, "").slice(0, 11);
    return digits
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1-$2");
  };

  inputs.forEach((input) => {
    input.addEventListener("input", (event) => {
      const target = event.target;
      target.value = formatCpf(target.value);
    });

    input.addEventListener("blur", (event) => {
      const target = event.target;
      target.value = formatCpf(target.value);
    });
  });
});