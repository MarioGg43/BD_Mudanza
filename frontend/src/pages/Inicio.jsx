import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Carousel, Modal } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';
import { useInfoPublica } from '../hooks/useInfoPublica';
import { DIAPOSITIVAS, EMPRESA, ESPECIALIDADES, RAZONES, TRABAJOS } from '../data/empresa';
import { iconoServicio } from '../utils/servicios';

const PASOS = [
  { icono: 'bi-person-plus', titulo: 'Creá tu cuenta', texto: 'Con tu DNI y tu correo, en un minuto.' },
  { icono: 'bi-clipboard-check', titulo: 'Cargá tu pedido', texto: 'La fecha, las direcciones, qué hay que llevar y el camión que necesitás.' },
  { icono: 'bi-geo-alt', titulo: 'Seguí tu mudanza', texto: 'Te avisamos cuando se confirma y ves en qué estado está.' },
];

const whatsapp = `https://wa.me/${EMPRESA.whatsapp}`;
const afuera = { target: '_blank', rel: 'noopener noreferrer' };

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
      <div className="text-center mb-4">
        <h2 className="h3 fw-bold mb-1">{titulo}</h2>
        {bajada && <p className="text-muted mb-0">{bajada}</p>}
      </div>
      {children}
    </section>
  );
}

export function Inicio() {
  const { usuario, puede, inicio } = useAuth();
  const { info, error } = useInfoPublica();
  const [foto, setFoto] = useState(null); // la foto de «Nuestros trabajos» que se ve en grande
  useIrAlAncla(Boolean(info || error)); // «Camiones» aparece cuando llegan los datos

  // el personal y el administrador no piden mudanzas: los botones los llevan a su pantalla
  const esPersonal = usuario && !puede('PED_REGISTRAR');
  const pedir = esPersonal ? { to: inicio, texto: 'Ir a mi panel' } : { to: '/pedidos/nuevo', texto: 'Pedir mi mudanza' };
  const pedibles = info ? [...info.principales, ...info.adicionales] : [];

  return (
    <div>
      {/* ---------- portada: las tres fotos de la empresa, una tras otra ---------- */}
      <Carousel fade interval={6000} className="portada mb-5" aria-label="Portada">
        {DIAPOSITIVAS.map((d) => (
          <Carousel.Item key={d.imagen}>
            <div className="portada-foto" style={{ backgroundImage: `url(${d.imagen})` }} role="img" aria-label={d.titulo} />
            <div className="portada-texto">
              <span className="etiqueta-blanca mb-3"><i className="bi bi-truck" />{EMPRESA.eslogan} · {EMPRESA.anios} años</span>
              <h1 className="display-5 fw-bold mb-3">{d.titulo}</h1>
              <p className="fs-5 mb-4">{d.texto}</p>
              <div className="d-flex flex-wrap gap-2">
                <Link to={pedir.to} className="btn btn-primary btn-lg"><i className="bi bi-box-seam me-2" />{pedir.texto}</Link>
                <a href={whatsapp} {...afuera} className="btn btn-outline-light btn-lg"><i className="bi bi-whatsapp me-2" />Consultanos</a>
              </div>
            </div>
          </Carousel.Item>
        ))}
      </Carousel>

      {/* ---------- servicios ---------- */}
      <Seccion id="servicios" titulo="Servicios" bajada={EMPRESA.bajada}>
        <div className="row row-cols-1 row-cols-md-3 g-4">
          {ESPECIALIDADES.map((s) => (
            <div key={s.titulo} className="col">
              <article className="card-panel h-100 overflow-hidden">
                <img src={s.imagen} alt={s.titulo} className="foto-servicio" loading="lazy" />
                <div className="p-4">
                  <h3 className="h5 fw-bold">{s.titulo}</h3>
                  <p className="text-muted mb-3">{s.texto}</p>
                  <Link to={pedir.to} className="btn btn-sm btn-outline-primary">{esPersonal ? pedir.texto : 'Solicitar presupuesto'}</Link>
                </div>
              </article>
            </div>
          ))}
        </div>
        {pedibles.length > 0 && (
          <div className="text-center mt-4">
            <p className="fw-semibold mb-2">Lo que podés pedir online</p>
            <div className="d-flex flex-wrap justify-content-center gap-2">
              {pedibles.map((s) => (
                <span key={s.id} className="chip-adicional"><i className={`bi ${iconoServicio(s.nombre)} me-1 text-marca`} />{s.nombre}</span>
              ))}
            </div>
          </div>
        )}
      </Seccion>

      {/* ---------- por qué elegirnos ---------- */}
      <section id="por-que" className="seccion-inicio">
        <div className="row g-4 align-items-center">
          <div className="col-lg-5">
            <img src={EMPRESA.imagenes.porQue} alt="El equipo de Mudanzas Salta trabajando" className="img-fluid foto-redondeada" loading="lazy" />
          </div>
          <div className="col-lg-7">
            <h2 className="h3 fw-bold mb-3">¿Por qué elegir Mudanzas Salta?</h2>
            <div className="row row-cols-1 row-cols-sm-2 g-3">
              {RAZONES.map((r) => (
                <div key={r.titulo} className="col">
                  <div className="d-flex gap-3">
                    <span className="icono-marca flex-shrink-0"><i className={`bi ${r.icono} fs-5`} /></span>
                    <div><h3 className="h6 fw-bold mb-1">{r.titulo}</h3><p className="small text-muted mb-0">{r.texto}</p></div>
                  </div>
                </div>
              ))}
            </div>
            <p className="fw-semibold mt-4 mb-2">Destinos frecuentes</p>
            <div className="d-flex flex-wrap gap-2">
              {EMPRESA.destinos.map((d) => <span key={d} className="chip-adicional"><i className="bi bi-geo-alt me-1 text-marca" />{d}</span>)}
            </div>
          </div>
        </div>
      </section>

      {/* ---------- formas de pago ---------- */}
      <section className="seccion-inicio text-center">
        <img src={EMPRESA.imagenes.pagos} alt="Aceptamos todas las tarjetas, Mercado Pago, hasta 12 cuotas, Pago Fácil, Link, Rapipago y Provincia Net"
             className="img-fluid" style={{ maxWidth: 420 }} loading="lazy" />
        <p className="fw-semibold mt-2 mb-0">{EMPRESA.pagos}</p>
      </section>

      {/* ---------- cómo funciona el sistema ---------- */}
      <Seccion id="como-funciona" titulo="Pedí tu mudanza online" bajada="Sin llamar ni esperar: cargás el pedido y seguís su estado.">
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

      {/* ---------- reseñas ---------- */}
      <section className="banda-resenas seccion-inicio" style={{ backgroundImage: `url(${EMPRESA.imagenes.resenas})` }}>
        <div className="banda-resenas-texto text-center p-4 p-md-5">
          <h2 className="h2 fw-bold mb-2">La experiencia de nuestros clientes habla por nosotros</h2>
          <p className="mb-4">Cientos de personas ya confiaron en nuestro servicio. Leé sus opiniones reales y descubrí por qué somos la mejor opción para tu mudanza.</p>
          <a href={EMPRESA.resenas} {...afuera} className="btn btn-light btn-lg"><i className="bi bi-google me-2" />Ver reseñas en Google</a>
        </div>
      </section>

      {/* ---------- nuestros trabajos ---------- */}
      <Seccion id="trabajos" titulo="Nuestros trabajos" bajada="Algunos de los trabajos que realizamos a diario.">
        <div className="row row-cols-2 row-cols-md-3 g-2 g-md-3">
          {TRABAJOS.map((src, n) => (
            <div key={src} className="col">
              <button type="button" className="foto-trabajo" onClick={() => setFoto(n)} aria-label={`Ver el trabajo ${n + 1} en grande`}>
                <img src={src} alt={`Trabajo ${n + 1} de Mudanzas Salta`} loading="lazy" />
              </button>
            </div>
          ))}
        </div>
      </Seccion>

      {/* ---------- llamado a la acción ---------- */}
      <section className="heroe-marca p-4 p-md-5 text-center mb-5">
        <h2 className="h2 fw-bold mb-2">¿Te mudás? Empezá ahora</h2>
        <p className="texto-suave mb-4">Cargá tu pedido en pocos minutos y la empresa te lo confirma.</p>
        <Link to={esPersonal ? inicio : usuario ? '/pedidos/nuevo' : '/registro'} className="btn btn-light btn-lg">
          {esPersonal ? 'Ir a mi panel' : usuario ? 'Pedir mudanza' : 'Crear mi cuenta gratis'}
        </Link>
      </section>

      {/* ---------- contacto con el mapa ---------- */}
      <Seccion id="contacto" titulo="Contáctenos" bajada="Consultanos lo que necesites y te respondemos de inmediato.">
        <div className="row g-3">
          <div className="col-lg-5">
            <div className="card-panel p-4 h-100">
              <p className="mb-2"><i className="bi bi-whatsapp me-2 text-marca" /><a href={whatsapp} {...afuera}>{EMPRESA.telefono}</a></p>
              <p className="mb-2"><i className="bi bi-envelope me-2 text-marca" /><a href={`mailto:${EMPRESA.correo}`}>{EMPRESA.correo}</a></p>
              <p className="mb-2"><i className="bi bi-instagram me-2 text-marca" /><a href={`https://www.instagram.com/${EMPRESA.instagram}`} {...afuera}>@{EMPRESA.instagram}</a></p>
              <p className="mb-2"><i className="bi bi-facebook me-2 text-marca" /><a href={`https://www.facebook.com/${EMPRESA.facebook}`} {...afuera}>{EMPRESA.facebook}</a></p>
              <p className="mb-3"><i className="bi bi-geo-alt me-2 text-marca" />{EMPRESA.direccion}</p>
              <a href={whatsapp} {...afuera} className="btn btn-whatsapp mb-3"><i className="bi bi-whatsapp me-2" />Escribinos por WhatsApp</a>
              <p className="small text-muted mb-0"><b>Dónde trabajamos:</b> {EMPRESA.zona} Destinos frecuentes: {EMPRESA.destinos.join(', ')}.</p>
            </div>
          </div>
          <div className="col-lg-7">
            <iframe title={`Mapa: ${EMPRESA.direccion}`} src={EMPRESA.mapa} className="mapa-empresa" loading="lazy"
                    referrerPolicy="no-referrer-when-downgrade" allowFullScreen />
          </div>
        </div>
      </Seccion>

      {/* la foto de un trabajo en grande, con anterior / siguiente */}
      <Modal show={foto !== null} onHide={() => setFoto(null)} centered size="lg" contentClassName="bg-dark border-0">
        {foto !== null && (
          <div className="position-relative">
            <img src={TRABAJOS[foto]} alt={`Trabajo ${foto + 1} de Mudanzas Salta`} className="w-100 rounded" />
            <button type="button" className="btn btn-light btn-sm visor-boton visor-anterior" aria-label="Foto anterior"
                    onClick={() => setFoto((foto + TRABAJOS.length - 1) % TRABAJOS.length)}><i className="bi bi-chevron-left" /></button>
            <button type="button" className="btn btn-light btn-sm visor-boton visor-siguiente" aria-label="Foto siguiente"
                    onClick={() => setFoto((foto + 1) % TRABAJOS.length)}><i className="bi bi-chevron-right" /></button>
            <button type="button" className="btn-close btn-close-white visor-cerrar" aria-label="Cerrar" onClick={() => setFoto(null)} />
          </div>
        )}
      </Modal>
    </div>
  );
}
