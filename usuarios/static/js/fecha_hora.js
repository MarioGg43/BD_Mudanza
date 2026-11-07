// Fecha y hora del pedido (pedir, modificar y reprogramar):
// - la fecha con un calendario en castellano (Flatpickr) que no deja elegir días pasados ni más de un año;
// - en la lista de horas, si el día elegido es hoy, las que ya pasaron quedan apagadas.
// El servidor revisa lo mismo (reglas._validar_fecha y _validar_hora): esto solo evita el error.
(function () {
  const dos = (n) => String(n).padStart(2, '0');
  const hoyISO = () => { const d = new Date(); return d.getFullYear() + '-' + dos(d.getMonth() + 1) + '-' + dos(d.getDate()); };

  // Apaga las horas pasadas cuando la fecha es hoy, y avisa debajo de la lista
  function revisarHoras(selectHora, inputFecha) {
    const esHoy = inputFecha.value === hoyISO();
    const ahora = new Date();
    const yaPaso = dos(ahora.getHours()) + ':' + dos(ahora.getMinutes());
    let primera = null;
    [...selectHora.options].forEach((o) => {
      if (!o.value) return;
      o.disabled = esHoy && o.value <= yaPaso;
      if (!o.disabled && !primera) primera = o.value;
    });
    if (selectHora.selectedOptions[0] && selectHora.selectedOptions[0].disabled) selectHora.value = '';
    let ayuda = selectHora.parentElement.querySelector('[data-ayuda-hora]');
    if (!ayuda) {
      ayuda = document.createElement('div');
      ayuda.className = 'form-text';
      ayuda.dataset.ayudaHora = '';
      selectHora.after(ayuda);
    }
    ayuda.textContent = !esHoy ? '' : primera ? 'Para hoy, desde las ' + primera + '.' : 'Hoy ya no quedan horarios: elegí otro día.';
  }

  document.querySelectorAll('input[data-calendario]').forEach((input) => {
    const selectHora = document.querySelector('select[data-hora-de="' + input.id + '"]');
    flatpickr(input, {
      locale: 'es',
      dateFormat: 'Y-m-d',            // lo que se manda al servidor
      altInput: true,
      altFormat: 'l j \\de F \\de Y', // lo que ve la persona: «martes 17 de noviembre de 2026»
      minDate: input.dataset.min,
      maxDate: input.dataset.max,
      disableMobile: true,            // el mismo calendario también en el celular
      // en castellano el día y el mes van en minúscula: «sábado 7 de noviembre de 2026»
      formatDate: (fecha, formato) => formato === 'Y-m-d'
        ? flatpickr.formatDate(fecha, formato)
        : flatpickr.formatDate(fecha, formato, flatpickr.l10ns.es).toLowerCase(),
      onChange: () => {
        if (selectHora) revisarHoras(selectHora, input);
        input.dispatchEvent(new Event('change', { bubbles: true })); // busca los vehículos libres
      },
    });
    if (selectHora) {
      revisarHoras(selectHora, input);
      // si la página queda abierta, cada minuto se apaga la hora que va pasando
      setInterval(() => revisarHoras(selectHora, input), 60000);
    }
  });
})();
