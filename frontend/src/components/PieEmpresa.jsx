import { Link } from 'react-router-dom';
import { EMPRESA } from '../data/empresa';

// Pie de la página de inicio con los datos de la empresa
export function PieEmpresa() {
  return (
    <footer className="pie-empresa mt-auto">
      <div className="container py-4">
        <div className="row g-4">
          <div className="col-md-5">
            <p className="fw-bold fs-5 mb-1">{EMPRESA.nombre}</p>
            <p className="small mb-0">{EMPRESA.eslogan}. {EMPRESA.anios} años conectando destinos con seguridad y profesionalismo.</p>
          </div>
          <div className="col-6 col-md-3">
            <p className="fw-semibold mb-2">La empresa</p>
            <ul className="list-unstyled small mb-0">
              <li><Link to="/#servicios">Servicios</Link></li>
              <li><Link to="/#camiones">Camiones</Link></li>
              <li><Link to="/#como-funciona">Cómo funciona</Link></li>
              <li><Link to="/#contacto">Contacto</Link></li>
            </ul>
          </div>
          <div className="col-6 col-md-4">
            <p className="fw-semibold mb-2">Contacto</p>
            <ul className="list-unstyled small mb-0">
              <li><a href={`https://wa.me/${EMPRESA.whatsapp}`} target="_blank" rel="noopener noreferrer"><i className="bi bi-whatsapp me-1" />{EMPRESA.telefono}</a></li>
              <li><a href={`mailto:${EMPRESA.correo}`}><i className="bi bi-envelope me-1" />{EMPRESA.correo}</a></li>
              <li><a href={`https://www.instagram.com/${EMPRESA.instagram}`} target="_blank" rel="noopener noreferrer"><i className="bi bi-instagram me-1" />@{EMPRESA.instagram}</a></li>
              <li><a href={`https://www.facebook.com/${EMPRESA.facebook}`} target="_blank" rel="noopener noreferrer"><i className="bi bi-facebook me-1" />{EMPRESA.facebook}</a></li>
            </ul>
          </div>
        </div>
        <p className="small border-top pt-3 mt-4 mb-0">© {new Date().getFullYear()} {EMPRESA.nombre}. Todos los derechos reservados.</p>
      </div>
    </footer>
  );
}
