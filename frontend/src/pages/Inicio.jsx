import { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useInfoPublica } from '../hooks/useInfoPublica';
import { ErrorAlert } from '../components/ErrorAlert';
import { EMPRESA, ESPECIALIDADES, RAZONES } from '../data/empresa';
import { iconoServicio } from '../utils/servicios';

const PASOS = [
  { icono: 'bi-person-plus', titulo: 'Creá tu cuenta', texto: 'Con tu DNI y tu correo, en un minuto.' },
  { icono: 'bi-clipboard-check', titulo: 'Cargá tu pedido', texto: 'La fecha, las direcciones, qué hay que llevar y el camión que necesitás.' },
  { icono: 'bi-geo-alt', titulo: 'Seguí tu mudanza', texto: 'Te avisamos cuando se confirma y ves en qué estado está.' },
];

const whatsapp = `https://wa.me/${EMPRESA.whatsapp}`;

// Para los enlaces del menú: «/#servicios» lleva hasta esa parte de la página
function useIrAlAncla(listo) {
  const { hash } = useLocation();
  useEffect(() => {
    if (hash && listo) document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'instant' });
  }, [hash, listo]);
}

function Seccion({ id, titulo, bajada, children }) {
  return (
    <section id={id} className="seccion-inicio">
      <h2 className="h3 fw-bold mb-1">{titulo}</h2>
      {bajada && <p className="text-muted mb-4">{bajada}</p>}
      {children}
    </section>
  );
}

export function Inicio() {
  const { usuario } = useAuth();
  const { info, error, refetch } = useInfoPublica();
  useIrAlAncla(Boolean(info || error));

  const pedibles = info ? [...info.principales, ...info.adicionales] : [];

  return (
    <div>
      {/* ---------- portada ---------- */}
      <section className="heroe-marca p-4 p-md-5 mb-4">
        <div className="row g-4 align-items-center">
          <div className="col-lg-7">
            <span className="etiqueta-blanca mb-3"><i className="bi bi-truck" />Mudanzas y fletes · {EMPRESA.anios} años en el rubro</span>
            <h1 className="display-5 fw-bold mb-3">{EMPRESA.eslogan}</h1>
            <p className="fs-5 texto-suave mb-4">{EMPRESA.bajada}</p>
            <div className="d-flex flex-wrap gap-2">
              <Link to="/pedidos/nuevo" className="btn btn-light btn-lg"><i className="bi bi-box-seam me-2" />Pedir mi mudanza</Link>
              <a href="#servicios" className="btn btn-outline-light btn-lg">Ver servicios</a>
            </div>
            {!usuario && (
              <p className="small texto-suave mt-3 mb-0">¿Ya tenés cuenta? <Link to="/login" className="enlace-degrade">Ingresá</Link></p>
            )}
          </div>
          <div className="col-lg-5">
            <div className="tarjeta-precios p-4">
              <p className="fw-bold fs-5 mb-1">Servicio disponible y respuesta inmediata</p>
              <p className="mb-3">Dejá tus pertenencias en manos expertas. Nos ocupamos de todo.</p>
              <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="btn btn-whatsapp w-100 mb-2">
                <i className="bi bi-whatsapp me-2" />Consultanos por WhatsApp
              </a>
              <p className="small mb-0"><i className="bi bi-cash-coin me-1 text-marca" />{EMPRESA.pagos}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- números ---------- */}
      <div className="row row-cols-1 row-cols-sm-2 g-3 mb-5">
        <div className="col"><div className="card-panel p-3 text-center h-100"><p className="dato-grande">+{EMPRESA.anios}</p><p className="text-muted mb-0">años en el rubro</p></div></div>
        <div className="col"><div className="card-panel p-3 text-center h-100"><p className="dato-grande">Todo el país</p><p className="text-muted mb-0">dentro y fuera de Salta</p></div></div>
      </div>

      {error && <ErrorAlert message={`No pudimos cargar los servicios. ${error}`} onRetry={refetch} />}

      {/* ---------- servicios ---------- */}
      <Seccion id="servicios" titulo="Servicios" bajada="Tu hogar o negocio, en cualquier rincón del país.">
        <div className="row row-cols-1 row-cols-md-3 g-3">
          {ESPECIALIDADES.map((s) => (
            <div key={s.titulo} className="col">
              <div className="card-panel p-4 h-100">
                <span className="icono-marca mb-3"><i className={`bi ${s.icono} fs-4`} /></span>
                <h3 className="h5 fw-bold">{s.titulo}</h3>
                <p className="text-muted mb-0">{s.texto}</p>
              </div>
            </div>
          ))}
        </div>
        {pedibles.length > 0 && (
          <>
            <h3 className="h6 fw-bold mt-4 mb-2">Lo que podés pedir online</h3>
            <div className="d-flex flex-wrap gap-2">
              {pedibles.map((s) => (
                <span key={s.id} className="chip-adicional"><i className={`bi ${iconoServicio(s.nombre)} me-1 text-marca`} />{s.nombre}</span>
              ))}
            </div>
          </>
        )}
      </Seccion>

      {/* ---------- camiones ---------- */}
      {info?.camiones.length > 0 && (
        <Seccion id="camiones" titulo="Nuestros camiones" bajada="Elegís el tamaño según lo que tengas que llevar.">
          <div className="row row-cols-1 row-cols-md-3 g-3">
            {info.camiones.map((c) => (
              <div key={c.tipo} className="col">
                <div className="card-panel p-4 h-100 text-center">
                  <i className={`bi bi-truck text-marca camion-${c.tipo.split(' ').pop().toLowerCase()}`} />
                  <h3 className="h5 fw-bold mt-2">{c.tipo}</h3>
                  <p className="mb-0">Hasta {c.capacidad_kg.toLocaleString('es-AR')} kg · {c.capacidad_m3.toLocaleString('es-AR')} m³</p>
                </div>
              </div>
            ))}
          </div>
        </Seccion>
      )}

      {/* ---------- cómo funciona ---------- */}
      <Seccion id="como-funciona" titulo="Cómo funciona" bajada="Pedí tu mudanza online, sin llamar ni esperar.">
        <ol className="row row-cols-1 row-cols-md-3 g-3 list-unstyled">
          {PASOS.map((p, n) => (
            <li key={p.titulo} className="col">
              <div className="card-panel p-4 h-100">
                <div className="d-flex align-items-center gap-3 mb-2">
                  <span className="numero-paso">{n + 1}</span>
                  <i className={`bi ${p.icono} fs-3 text-marca`} />
                </div>
                <h3 className="h5 fw-bold">{p.titulo}</h3>
                <p className="text-muted mb-0">{p.texto}</p>
              </div>
            </li>
          ))}
        </ol>
      </Seccion>

      {/* ---------- por qué elegirnos ---------- */}
      <Seccion id="por-que" titulo="¿Por qué elegirnos?">
        <div className="row row-cols-1 row-cols-sm-2 row-cols-lg-3 g-4">
          {RAZONES.map((r) => (
            <div key={r.titulo} className="col">
              <div className="d-flex gap-3">
                <span className="icono-marca flex-shrink-0"><i className={`bi ${r.icono} fs-5`} /></span>
                <div><h3 className="h6 fw-bold mb-1">{r.titulo}</h3><p className="small text-muted mb-0">{r.texto}</p></div>
              </div>
            </div>
          ))}
        </div>
        <h3 className="h6 fw-bold mt-4 mb-2">Destinos frecuentes</h3>
        <div className="d-flex flex-wrap gap-2">
          {EMPRESA.destinos.map((d) => (
            <span key={d} className="chip-adicional"><i className="bi bi-geo-alt me-1 text-marca" />{d}</span>
          ))}
        </div>
      </Seccion>

      {/* ---------- llamado a la acción ---------- */}
      <section className="heroe-marca p-4 p-md-5 text-center mb-5">
        <h2 className="h2 fw-bold mb-2">¿Te mudás? Empezá ahora</h2>
        <p className="texto-suave mb-4">Cargá tu pedido en pocos minutos y la empresa te lo confirma.</p>
        <Link to={usuario ? '/pedidos/nuevo' : '/registro'} className="btn btn-light btn-lg">
          {usuario ? 'Pedir mudanza' : 'Crear mi cuenta gratis'}
        </Link>
      </section>

      {/* ---------- contacto ---------- */}
      <Seccion id="contacto" titulo="Contacto" bajada="Consultanos lo que necesites y te respondemos de inmediato.">
        <div className="row g-3">
          <div className="col-md-6">
            <div className="card-panel p-4 h-100">
              <p className="mb-2"><i className="bi bi-whatsapp me-2 text-marca" /><a href={whatsapp} target="_blank" rel="noopener noreferrer">{EMPRESA.telefono}</a></p>
              <p className="mb-2"><i className="bi bi-envelope me-2 text-marca" /><a href={`mailto:${EMPRESA.correo}`}>{EMPRESA.correo}</a></p>
              <p className="mb-2"><i className="bi bi-instagram me-2 text-marca" /><a href={`https://www.instagram.com/${EMPRESA.instagram}`} target="_blank" rel="noopener noreferrer">@{EMPRESA.instagram}</a></p>
              <p className="mb-3"><i className="bi bi-facebook me-2 text-marca" /><a href={`https://www.facebook.com/${EMPRESA.facebook}`} target="_blank" rel="noopener noreferrer">{EMPRESA.facebook}</a></p>
              <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="btn btn-whatsapp">
                <i className="bi bi-whatsapp me-2" />Escribinos por WhatsApp
              </a>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card-panel p-4 h-100">
              <h3 className="h6 fw-bold"><i className="bi bi-map me-2 text-marca" />Dónde trabajamos</h3>
              <p className="text-muted">{EMPRESA.zona} Destinos frecuentes: {EMPRESA.destinos.join(', ')}.</p>
              <h3 className="h6 fw-bold"><i className="bi bi-cash-coin me-2 text-marca" />Formas de pago</h3>
              <p className="text-muted">{EMPRESA.pagos}</p>
              <h3 className="h6 fw-bold"><i className="bi bi-globe me-2 text-marca" />Sitio web</h3>
              <p className="mb-0"><a href={EMPRESA.sitio} target="_blank" rel="noopener noreferrer">{EMPRESA.sitio.replace('https://', '')}</a></p>
            </div>
          </div>
        </div>
      </Seccion>
    </div>
  );
}
