import { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useInfoPublica } from '../hooks/useInfoPublica';
import { ErrorAlert } from '../components/ErrorAlert';
import { EMPRESA } from '../data/empresa';
import { dinero } from '../utils/formato';
import { descripcionServicio, iconoServicio } from '../utils/servicios';

const PASOS = [
  { icono: 'bi-person-plus', titulo: 'Creá tu cuenta', texto: 'Con tu DNI y tu correo, en un minuto.' },
  { icono: 'bi-clipboard-check', titulo: 'Cargá tu pedido', texto: 'Fecha, direcciones, qué hay que llevar y el camión. Ves el precio al instante.' },
  { icono: 'bi-geo-alt', titulo: 'Seguí tu mudanza', texto: 'Te avisamos cuando se confirma y podés ver en qué estado está.' },
];

const RAZONES = [
  { icono: 'bi-cash-coin', titulo: 'Precio claro', texto: 'Sabés cuánto sale antes de confirmar. Sin sorpresas.' },
  { icono: 'bi-phone', titulo: 'Todo online', texto: 'Pedís, seguís y descargás tu comprobante desde el celular.' },
  { icono: 'bi-calendar2-week', titulo: 'Cambios sin drama', texto: '' },
  { icono: 'bi-people', titulo: 'Personal propio', texto: 'Choferes y ayudantes de la empresa, con experiencia.' },
];

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

  const desde = info?.principales.length ? Math.min(...info.principales.map((s) => s.precio)) : null;
  const flota = info?.camiones.reduce((t, c) => t + c.cantidad, 0);
  const razones = RAZONES.map((r) => (r.texto ? r : {
    ...r, texto: `Modificás o cancelás tu pedido hasta ${info?.horas_limite ?? 24} horas antes.`,
  }));

  return (
    <div>
      {/* ---------- portada ---------- */}
      <section className="heroe-marca p-4 p-md-5 mb-4">
        <div className="row g-4 align-items-center">
          <div className="col-lg-7">
            <span className="etiqueta-blanca mb-3"><i className="bi bi-truck" />Mudanzas y fletes en Salta · {EMPRESA.anios} años</span>
            <h1 className="display-5 fw-bold mb-3">{EMPRESA.eslogan}</h1>
            <p className="fs-5 texto-suave mb-4">{EMPRESA.bajada}</p>
            <div className="d-flex flex-wrap gap-2">
              <Link to="/pedidos/nuevo" className="btn btn-light btn-lg"><i className="bi bi-box-seam me-2" />Pedir mi mudanza</Link>
              <a href="#servicios" className="btn btn-outline-light btn-lg">Ver servicios y precios</a>
            </div>
            {!usuario && (
              <p className="small texto-suave mt-3 mb-0">¿Ya tenés cuenta? <Link to="/login" className="enlace-degrade">Ingresá</Link></p>
            )}
          </div>
          <div className="col-lg-5">
            <div className="tarjeta-precios p-4">
              <p className="small text-uppercase fw-bold text-muted mb-2">Precios desde</p>
              {info ? info.principales.map((s) => (
                <div key={s.id} className="d-flex justify-content-between align-items-center py-2 border-bottom">
                  <span><i className={`bi ${iconoServicio(s.nombre)} me-2 text-marca`} />{s.nombre}</span>
                  <span className="fw-bold">{dinero(s.precio)}</span>
                </div>
              )) : <p className="text-muted mb-0">Cargando precios...</p>}
              <p className="small text-muted mt-2 mb-0">El precio final depende del tamaño del camión que elijas.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- números ---------- */}
      <div className="row row-cols-1 row-cols-sm-3 g-3 mb-5">
        <div className="col"><div className="card-panel p-3 text-center h-100"><p className="dato-grande">{EMPRESA.anios}+</p><p className="text-muted mb-0">años mudando salteños</p></div></div>
        <div className="col"><div className="card-panel p-3 text-center h-100"><p className="dato-grande">{flota ?? '—'}</p><p className="text-muted mb-0">camiones propios</p></div></div>
        <div className="col"><div className="card-panel p-3 text-center h-100"><p className="dato-grande">{desde ? dinero(desde) : '—'}</p><p className="text-muted mb-0">el servicio más económico</p></div></div>
      </div>

      {error && <ErrorAlert message={`No pudimos cargar los servicios. ${error}`} onRetry={refetch} />}

      {/* ---------- servicios ---------- */}
      {info && (
        <Seccion id="servicios" titulo="Servicios" bajada="Elegís uno y, si querés, le sumás adicionales.">
          <div className="row row-cols-1 row-cols-md-3 g-3">
            {info.principales.map((s) => (
              <div key={s.id} className="col">
                <div className="card-panel p-4 h-100 d-flex flex-column">
                  <span className="icono-marca mb-3"><i className={`bi ${iconoServicio(s.nombre)} fs-4`} /></span>
                  <h3 className="h5 fw-bold">{s.nombre}</h3>
                  <p className="text-muted flex-grow-1">{descripcionServicio(s.nombre)}</p>
                  <p className="mb-0"><span className="small text-muted">desde </span><span className="fs-4 fw-bold">{dinero(s.precio)}</span></p>
                  <p className="small text-muted mb-0">unas {s.horas} horas</p>
                </div>
              </div>
            ))}
          </div>
          {info.adicionales.length > 0 && (
            <>
              <h3 className="h6 fw-bold mt-4 mb-2">Y si querés, le sumás</h3>
              <div className="d-flex flex-wrap gap-2">
                {info.adicionales.map((s) => (
                  <span key={s.id} className="chip-adicional">
                    <i className={`bi ${iconoServicio(s.nombre)} me-1`} />{s.nombre}
                    <b className="ms-1">{s.precio > 0 ? `+ ${dinero(s.precio)}` : 'sin cargo'}</b>
                  </span>
                ))}
              </div>
            </>
          )}
        </Seccion>
      )}

      {/* ---------- camiones ---------- */}
      {info?.camiones.length > 0 && (
        <Seccion id="camiones" titulo="Nuestros camiones" bajada="Elegís el tamaño según lo que tengas que llevar.">
          <div className="row row-cols-1 row-cols-md-3 g-3">
            {info.camiones.map((c) => (
              <div key={c.tipo} className="col">
                <div className="card-panel p-4 h-100 text-center">
                  <i className={`bi bi-truck text-marca camion-${c.tipo.split(' ').pop().toLowerCase()}`} />
                  <h3 className="h5 fw-bold mt-2">{c.tipo}</h3>
                  <p className="mb-1">Hasta {c.capacidad_kg.toLocaleString('es-AR')} kg · {c.capacidad_m3.toLocaleString('es-AR')} m³</p>
                  <span className={`badge rounded-pill ${c.recargo ? 'text-bg-warning' : 'text-bg-light border'}`}>
                    {c.recargo ? `+${c.recargo} % sobre el servicio` : 'Sin recargo'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Seccion>
      )}

      {/* ---------- cómo funciona ---------- */}
      <Seccion id="como-funciona" titulo="Cómo funciona" bajada="Sin llamar ni esperar a que te pasen un presupuesto.">
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
      <Seccion id="por-que" titulo="Por qué elegirnos">
        <div className="row row-cols-1 row-cols-sm-2 row-cols-lg-4 g-3">
          {razones.map((r) => (
            <div key={r.titulo} className="col">
              <div className="d-flex gap-3">
                <span className="icono-marca flex-shrink-0"><i className={`bi ${r.icono} fs-5`} /></span>
                <div><h3 className="h6 fw-bold mb-1">{r.titulo}</h3><p className="small text-muted mb-0">{r.texto}</p></div>
              </div>
            </div>
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
      <Seccion id="contacto" titulo="Contacto" bajada="¿Tenés una duda antes de pedir? Escribinos.">
        <div className="row g-3">
          <div className="col-md-6">
            <div className="card-panel p-4 h-100">
              <p className="mb-2"><i className="bi bi-telephone me-2 text-marca" /><a href={`tel:${EMPRESA.telefono.replace(/\D/g, '')}`}>{EMPRESA.telefono}</a></p>
              <p className="mb-2"><i className="bi bi-envelope me-2 text-marca" /><a href={`mailto:${EMPRESA.correo}`}>{EMPRESA.correo}</a></p>
              <p className="mb-2"><i className="bi bi-instagram me-2 text-marca" />@{EMPRESA.instagram}</p>
              <p className="mb-3"><i className="bi bi-geo-alt me-2 text-marca" />{EMPRESA.direccion}</p>
              <a href={`https://wa.me/${EMPRESA.whatsapp}`} target="_blank" rel="noopener noreferrer" className="btn btn-whatsapp">
                <i className="bi bi-whatsapp me-2" />Escribinos por WhatsApp
              </a>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card-panel p-4 h-100">
              <h3 className="h6 fw-bold"><i className="bi bi-clock me-2 text-marca" />Horario de atención</h3>
              <p className="text-muted">{EMPRESA.horario}</p>
              <h3 className="h6 fw-bold"><i className="bi bi-map me-2 text-marca" />Dónde trabajamos</h3>
              <p className="text-muted mb-0">{EMPRESA.zona}</p>
            </div>
          </div>
        </div>
      </Seccion>
    </div>
  );
}
