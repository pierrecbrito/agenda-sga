/**
 * cidadao-autocomplete.js
 * Componente de autocomplete para busca de cidadãos por CPF ou nome.
 *
 * Uso: adicionar data-cidadao-autocomplete ao campo de input e
 * data-cidadao-url ao elemento ou ao document.
 *
 * O campo oculto [data-cidadao-cpf-hidden] recebe o CPF selecionado
 * que é o valor efetivamente submetido para o backend buscar o cidadão.
 */
(function () {
  'use strict';

  // URL do endpoint de autocomplete — pode ser sobrescrita via data attribute
  const DEFAULT_URL = '/api/cidadaos/autocomplete/';

  /**
   * Formata CPF: 000.000.000-00
   */
  function formatarCpf(value) {
    const digits = value.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 3) return digits;
    if (digits.length <= 6) return digits.slice(0, 3) + '.' + digits.slice(3);
    if (digits.length <= 9) return digits.slice(0, 3) + '.' + digits.slice(3, 6) + '.' + digits.slice(6);
    return digits.slice(0, 3) + '.' + digits.slice(3, 6) + '.' + digits.slice(6, 9) + '-' + digits.slice(9);
  }

  /**
   * Monta e conecta o autocomplete a um input específico.
   * @param {HTMLInputElement} input
   */
  function initAutocomplete(input) {
    const url = input.dataset.cidadaoUrl || document.body.dataset.cidadaoAutocompleteUrl || DEFAULT_URL;

    // Cria o contêiner de dropdown
    const wrapper = document.createElement('div');
    wrapper.className = 'cidadao-autocomplete';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const dropdown = document.createElement('ul');
    dropdown.className = 'cidadao-dropdown';
    dropdown.setAttribute('role', 'listbox');
    dropdown.hidden = true;
    wrapper.appendChild(dropdown);

    let currentQuery = '';
    let debounceTimer = null;
    let activeIndex = -1;

    function close() {
      dropdown.hidden = true;
      dropdown.innerHTML = '';
      activeIndex = -1;
    }

    function setActive(index) {
      const items = dropdown.querySelectorAll('[role="option"]');
      items.forEach((item, i) => {
        item.classList.toggle('is-active', i === index);
        if (i === index) item.scrollIntoView({ block: 'nearest' });
      });
      activeIndex = index;
    }

    function select(item) {
      input.value = item.nome + ' — ' + formatarCpf(item.cpf);
      // Grava o CPF puro como o valor de busca para o backend
      input.dataset.selectedCpf = item.cpf;
      input.dataset.selectedNome = item.nome;
      close();
      input.dispatchEvent(new CustomEvent('cidadao-selected', { detail: item, bubbles: true }));
    }

    function renderResults(results) {
      dropdown.innerHTML = '';
      activeIndex = -1;

      if (!results.length) {
        const empty = document.createElement('li');
        empty.className = 'cidadao-dropdown__empty';
        empty.textContent = 'Nenhum cidadão encontrado.';
        dropdown.appendChild(empty);
        dropdown.hidden = false;
        return;
      }

      results.forEach((item, i) => {
        const li = document.createElement('li');
        li.className = 'cidadao-dropdown__item';
        li.setAttribute('role', 'option');
        li.setAttribute('tabindex', '-1');
        li.innerHTML =
          '<span class="cidadao-dropdown__nome">' + item.nome + '</span>' +
          '<span class="cidadao-dropdown__cpf">' + formatarCpf(item.cpf) + '</span>';

        li.addEventListener('mousedown', (e) => {
          e.preventDefault(); // evita blur antes do click
          select(item);
        });

        dropdown.appendChild(li);
      });

      dropdown.hidden = false;
    }

    function fetchResults(q) {
      if (q.length < 2) { close(); return; }
      currentQuery = q;
      fetch(url + '?q=' + encodeURIComponent(q))
        .then((r) => r.json())
        .then((data) => {
          if (currentQuery === q) renderResults(data.results || []);
        })
        .catch(() => close());
    }

    input.addEventListener('input', () => {
      const q = input.value.trim();
      // Se o usuário limpar o campo, limpa a seleção
      if (!q) {
        delete input.dataset.selectedCpf;
        delete input.dataset.selectedNome;
        close();
        return;
      }
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => fetchResults(q), 220);
    });

    input.addEventListener('keydown', (e) => {
      const items = dropdown.querySelectorAll('[role="option"]');
      if (!items.length) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActive(Math.min(activeIndex + 1, items.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActive(Math.max(activeIndex - 1, 0));
      } else if (e.key === 'Enter' && activeIndex >= 0) {
        e.preventDefault();
        items[activeIndex].dispatchEvent(new MouseEvent('mousedown'));
      } else if (e.key === 'Escape') {
        close();
      }
    });

    input.addEventListener('blur', () => {
      // Pequeno delay para permitir o clique no item
      setTimeout(close, 150);
    });

    // Fecha ao clicar fora
    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) close();
    });
  }

  // Inicializa todos os inputs com data-cidadao-autocomplete na página
  function init() {
    document.querySelectorAll('[data-cidadao-autocomplete]').forEach(initAutocomplete);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expõe para uso externo (dialogs abertos dinamicamente)
  window.initCidadaoAutocomplete = initAutocomplete;
})();
