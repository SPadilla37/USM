// URL base del servidor
const API_BASE_URL = 'https://usm-839u.onrender.com';

// Función para obtener las opciones de fetch con el token de autorización
function getAuthFetchOptions(method = 'GET', body = null) {
  const token = localStorage.getItem('authToken');
  const options = {
    method: method,
    headers: { 
      'Content-Type': 'application/json'
    }
  };
  
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }
  
  if (body) {
    options.body = JSON.stringify(body);
  }
  
  return options;
}

// Verificar si ya hay sesión al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  // Si ya hay un token y no estamos en una página que explícitamente no requiere redirección
  // (ej. mapa.html ya es el destino, o las nuevas páginas de login/registro móvil)
  const nonRedirectPages = [
    '/mapa.html',
    '/login_mobile.html',
    '/login_password_mobile.html',
    '/verificacion_usuario.html',
    '/confirmacion_usuario.html',
    '/registro_mobile.html'
  ];
  
  if (localStorage.getItem('authToken') && !nonRedirectPages.some(page => window.location.pathname.endsWith(page))) {
    // Solo redirigir si no estamos ya en una de las páginas del flujo de autenticación o en el mapa.
    // Esto evita bucles de redirección si el token existe pero el usuario navega a login_mobile.html
    if (window.location.pathname !== '/mapa.html') { // Evita recargar mapa.html si ya estamos ahí
        window.location.href = 'mapa.html';
    }
  }
});