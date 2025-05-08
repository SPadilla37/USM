// URL base del servidor
const API_BASE_URL = 'https://usm-839u.onrender.com';

// Opciones para las solicitudes fetch
const fetchOptions = {
  headers: { 
    'Content-Type': 'application/json'
  }
};

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

// Iniciar sesión
function loginUser() {
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  
  if (!username || !password) {
    document.getElementById('login-error').textContent = 'Credenciales inválidas';
    return;
  }
  
  fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      document.getElementById('login-error').textContent = 'Credenciales inválidas';
    } else {
      // Guardar el token en localStorage
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('username', data.username);
      
      // Redirigir al mapa
      window.location.href = 'mapa.html';
    }
  })
  .catch(error => {
    document.getElementById('login-error').textContent = 'Error al conectar con el servidor';
    console.error('Error:', error);
  });
}

// Registrar usuario
function registerUser() {
  const username = document.getElementById('register-username').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;
  const confirmPassword = document.getElementById('register-confirm-password').value;
  
  if (!username || !email || !password || !confirmPassword) {
    document.getElementById('register-error').textContent = 'Credenciales inválidas';
    return;
  }
  
  // Validar formato de correo electrónico
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    document.getElementById('register-error').textContent = 'Credenciales inválidas';
    return;
  }
  
  if (password !== confirmPassword) {
    document.getElementById('register-error').textContent = 'Credenciales inválidas';
    return;
  }
  
  fetch(`${API_BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      document.getElementById('register-error').textContent = data.error;
    } else {
      // Guardar el token en localStorage
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('username', data.username);
      
      // Redirigir al mapa
      window.location.href = 'mapa.html';
    }
  })
  .catch(error => {
    document.getElementById('register-error').textContent = 'Error al conectar con el servidor';
    console.error('Error:', error);
  });
}

// Verificar si ya hay sesión al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  // Si ya hay un token, redirigir al mapa
  if (localStorage.getItem('authToken')) {
    window.location.href = 'mapa.html';
  }
}); 