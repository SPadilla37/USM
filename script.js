// Añade tu token de acceso de Mapbox
mapboxgl.accessToken = 'pk.eyJ1IjoiNG5nM2wiLCJhIjoiY205cTJtN284MWI4dDJqb2J0cWRjZWk2dSJ9.Bk-OJNIYS060ah6qOH3BXw';

// URL base del servidor
const API_BASE_URL = 'https://usm-839u.onrender.com';

// Opciones para las solicitudes fetch (sin incluir token automáticamente)
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

// Estado de autenticación
let authState = {
  authenticated: false,
  user_id: null,
  username: null
};

// Mostrar el diálogo de autenticación inmediatamente al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  // Comprobar si existe un token guardado en localStorage
  const token = localStorage.getItem('authToken');
  
  if (token) {
    // Si hay un token, verificar si es válido
    checkSession();
  } else {
    // Si no hay token, mostrar el diálogo de autenticación
    document.getElementById('auth-container').style.display = 'flex';
  }
});

// Función para mostrar/ocultar paneles de autenticación
function showTab(tab) {
  if (tab === 'login') {
    document.getElementById('login-tab').classList.add('active');
    document.getElementById('register-tab').classList.remove('active');
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
  } else {
    document.getElementById('login-tab').classList.remove('active');
    document.getElementById('register-tab').classList.add('active');
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
  }
}

// Función para mostrar el diálogo de autenticación
function showAuthDialog() {
  document.getElementById('auth-container').style.display = 'flex';
}

// Función para ocultar el diálogo de autenticación
function hideAuthDialog() {
  document.getElementById('auth-container').style.display = 'none';
  // Mostrar completamente el mapa cuando el usuario se autentica
  document.getElementById('map').style.opacity = '1';
}

// Iniciar sesión
function loginUser() {
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  
  if (!username || !password) {
    document.getElementById('login-error').textContent = 'Por favor, completa todos los campos';
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
      document.getElementById('login-error').textContent = data.error;
    } else {
      // Guardar el token en localStorage
      localStorage.setItem('authToken', data.token);
      
      // Actualizar el estado de autenticación
      authState.authenticated = true;
      authState.user_id = data.user_id;
      authState.username = data.username;
      
      updateAuthUI();
      hideAuthDialog();
      
      // Activar geolocalización después de iniciar sesión
      geolocateControl.trigger();
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
    document.getElementById('register-error').textContent = 'Por favor, completa todos los campos';
    return;
  }
  
  if (password !== confirmPassword) {
    document.getElementById('register-error').textContent = 'Las contraseñas no coinciden';
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
      
      // Actualizar el estado de autenticación
      authState.authenticated = true;
      authState.user_id = data.user_id;
      authState.username = data.username;
      
      updateAuthUI();
      hideAuthDialog();
      
      // Activar geolocalización después de registrarse
      geolocateControl.trigger();
    }
  })
  .catch(error => {
    document.getElementById('register-error').textContent = 'Error al conectar con el servidor';
    console.error('Error:', error);
  });
}

// Cerrar sesión
function logoutUser() {
  // Eliminar el token del localStorage
  localStorage.removeItem('authToken');
  
  // Actualizar el estado de autenticación
  authState.authenticated = false;
  authState.user_id = null;
  authState.username = null;
  
  // Actualizar la UI
  updateAuthUI();
  
  // Redirigir a la página de inicio
  window.location.href = 'index.html';
}

// Comprobar estado de sesión
function checkSession() {
  const options = getAuthFetchOptions('GET');
  
  fetch(`${API_BASE_URL}/check-session`, options)
  .then(response => response.json())
  .then(data => {
    authState.authenticated = data.authenticated;
    
    if (data.authenticated) {
      // Si está autenticado, actualizar el estado
      authState.user_id = data.user_id;
      authState.username = data.username;
      
      // Actualizar la UI y ocultar el diálogo de autenticación
      updateAuthUI();
      hideAuthDialog();
      
      // Activar geolocalización
      geolocateControl.trigger();
    } else {
      // Si el token no es válido, eliminar del localStorage
      localStorage.removeItem('authToken');
      
      // Actualizar la UI y mostrar el diálogo de autenticación
      updateAuthUI();
      showAuthDialog();
    }
  })
  .catch(error => {
    console.error('Error al comprobar sesión:', error);
    
    // En caso de error, mostrar el diálogo de autenticación
    showAuthDialog();
  });
}

// Actualizar UI basado en estado de autenticación
function updateAuthUI() {
  const profileSection = document.getElementById('profile-section');
  
  if (authState.authenticated) {
    profileSection.innerHTML = `
      <div class="profile-info">
        <strong>Usuario:</strong> ${authState.username}<br>
        <strong>ID:</strong> ${authState.user_id}
      </div>
    `;
  } else {
    profileSection.innerHTML = `
      <button class="auth-button" onclick="showAuthDialog()">Iniciar sesión / Registrarse</button>
    `;
  }
}

const map = new mapboxgl.Map({  
  container: 'map',
  style: 'mapbox://styles/mapbox/streets-v12',
  center: [0, 0], // Coordenadas iniciales (se actualizarán)
  zoom: 2 // Zoom inicial (se actualizará)
});  

// Añadir control de geolocalización al mapa
const geolocateControl = new mapboxgl.GeolocateControl({
  positionOptions: {
    enableHighAccuracy: true
  },
  trackUserLocation: true,
  showUserHeading: true,
  showAccuracyCircle: true
});

map.addControl(geolocateControl);

// Función para alternar la visibilidad del panel de información
function toggleInfoPanel() {
  const infoPanel = document.getElementById('info-panel');
  const isHidden = infoPanel.classList.toggle('hidden');
  localStorage.setItem('infoPanelHidden', isHidden); // Guardar el estado en localStorage
}

// Variable para almacenar el marcador actual
let currentMarker = null;
let trackingInterval = null;

// Activar automáticamente la geolocalización al cargar el mapa
map.on('load', () => {
  // Ya no activamos geolocalización aquí, sino después de autenticarse
  // La comprobación de sesión ya se hace en DOMContentLoaded
});

// Ocultar el mapa inicialmente hasta que el usuario se autentique
document.getElementById('map').style.opacity = '0.3';

// Actualizar el panel de información cuando se obtiene la ubicación
geolocateControl.on('geolocate', function(e) {
  const longitude = e.coords.longitude;
  const latitude = e.coords.latitude;

  // Eliminar el marcador actual si existe
  if (currentMarker) {
    currentMarker.remove();
  }

  // Agregar un marcador para la ubicación del usuario principal
  currentMarker = new mapboxgl.Marker({ color: 'blue' }) // Marcador azul
    .setLngLat([longitude, latitude])
    .addTo(map);

  // Obtener la dirección del usuario principal
  fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${longitude},${latitude}.json?access_token=${mapboxgl.accessToken}`)
    .then(response => response.json())
    .then(data => {
      const address = data.features[0]?.place_name || 'Dirección no disponible';
      const userId = authState.authenticated ? authState.user_id : 'anónimo';
      document.getElementById('location-info').innerHTML = 
        `<strong>Dirección:</strong> ${address}`;
    })
    .catch(err => console.error('Error al obtener la dirección:', err));

  // Actualizar la ubicación en el servidor usando token
  if (authState.authenticated) {
    const options = getAuthFetchOptions('POST', {
      userId: authState.user_id,
      latitude,
      longitude
    });
    
    fetch(`${API_BASE_URL}/update-location`, options)
      .then(response => response.json())
      .then(data => console.log(data))
      .catch(err => console.error('Error al actualizar la ubicación:', err));
  }
});

// Función para iniciar el seguimiento en tiempo real - usando token de autorización
function startRealTimeTracking() {
  const searchUserId = document.getElementById('search-user-id').value;
  if (!searchUserId) {
    document.getElementById('search-result').innerHTML = 'Por favor, introduce una ID válida.';
    return;
  }

  // Limpiar cualquier intervalo previo
  if (trackingInterval) {
    clearInterval(trackingInterval);
  }

  // Iniciar un intervalo para actualizar la ubicación cada 5 segundos
  trackingInterval = setInterval(() => {
    const options = getAuthFetchOptions('GET');
    
    fetch(`${API_BASE_URL}/get-location/${searchUserId}`, options)
      .then(response => {
        if (!response.ok) {
          throw new Error('Usuario no encontrado');
        }
        return response.json();
      })
      .then(location => {
        const { latitude, longitude } = location;

        // Centrar el mapa en la ubicación del usuario
        map.flyTo({
          center: [longitude, latitude],
          zoom: 14
        });

        // Eliminar el marcador actual si existe
        if (currentMarker) {
          currentMarker.remove();
        }

        // Agregar un nuevo marcador en la ubicación del usuario buscado
        currentMarker = new mapboxgl.Marker({ color: 'red' }) // Marcador rojo
          .setLngLat([longitude, latitude])
          .addTo(map);

        // Obtener la dirección del usuario buscado
        fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${longitude},${latitude}.json?access_token=${mapboxgl.accessToken}`)
          .then(response => response.json())
          .then(data => {
            const address = data.features[0]?.place_name || 'Dirección no disponible';
            document.getElementById('search-result').innerHTML = 
              `<strong>Ubicación del usuario ${searchUserId}:</strong><br>` +
              `<strong>Dirección:</strong> ${address}<br>` +
              `Latitud: ${latitude.toFixed(6)}<br>` +
              `Longitud: ${longitude.toFixed(6)}`;
          })
          .catch(err => console.error('Error al obtener la dirección:', err));
      })
      .catch(err => {
        console.error(err);
        document.getElementById('search-result').innerHTML = 
          `<strong>Error:</strong> No se pudo localizar al usuario.`;
      });
  }, 5000); // Actualizar cada 5 segundos
} 