import { useState } from 'react';

// Se encarga de lo repetido de cualquier formulario: guardar lo que se escribe,
// mandar los datos y poner al lado de cada campo el error que devuelve Django.
/* Estado de un formulario: los datos, los errores por campo que devuelve la API y si se está
   enviando. `enviar(guardar, alTerminar)` llama al servicio y, si sale bien, a `alTerminar`. */
export function useFormulario(inicial) {
  const [datos, setDatos] = useState(inicial);
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);

  const cambiar = (e) => {
    const { name, value, type, checked } = e.target;
    setDatos((d) => ({ ...d, [name]: type === 'checkbox' ? checked : value }));
  };

  const enviar = async (guardar, alTerminar) => {
    setEnviando(true);
    setErrores({});
    try {
      const respuesta = await guardar(datos);
      alTerminar(respuesta);
    } catch (err) {
      setErrores({ __all__: err.message, ...err.errores });
      setEnviando(false);
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  };

  // las props comunes de un <Campo>: valor, cambio y error
  const campo = (name) => ({ name, value: datos[name] ?? '', onChange: cambiar, error: errores[name] });

  return { datos, setDatos, errores, enviando, cambiar, enviar, campo };
}
