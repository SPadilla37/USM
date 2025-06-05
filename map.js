// Añade tu token de acceso de Mapbox
mapboxgl.accessToken = 'pk.eyJ1IjoiNG5nM2wiLCJhIjoiY205cTJtN284MWI4dDJqb2J0cWRjZWk2dSJ9.Bk-OJNIYS060ah6qOH3BXw';

// URL base del servidor
const API_BASE_URL = 'https://usm-839u.onrender.com';

// Estado de autenticación
const authState = {
  authenticated: false,
  user_id: null,
  username: null
};

// Inicialización al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  const token = localStorage.getItem('authToken');
  
  if (!token) {
    // Si no hay token, redirigir a login
    window.location.href = 'login.html';
    return;
  }
  
  // Cargar datos de usuario desde localStorage
  authState.authenticated = true;
  authState.user_id = localStorage.getItem('user_id');
  authState.username = localStorage.getItem('username');
  
  // Actualizar UI
  updateAuthUI();
  
  // Comprobar validez del token
  checkSession();

  // Activar geolocalización inmediatamente
  setTimeout(() => {
    try {
      geolocateControl.trigger();
    } catch (error) {
      console.error('Error al activar la geolocalización:', error);
    }
  }, 1000);

  // Verificar el estado de los permisos de geolocalización
  if ("permissions" in navigator) {
    navigator.permissions.query({ name: 'geolocation' }).then(function(result) {
      console.log('Estado de permisos de geolocalización:', result.state);
      if (result.state === 'denied') {
        alert('Por favor habilita los permisos de ubicación en tu navegador para usar esta función.');
      }
    });
  }
});

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

// Cerrar sesión
function logoutUser() {
  // Eliminar tokens del localStorage
  localStorage.removeItem('authToken');
  localStorage.removeItem('user_id');
  localStorage.removeItem('username');
  
  // Redirigir a página de inicio
  window.location.href = 'index.html';
}

// Comprobar estado de sesión
function checkSession() {
  const options = getAuthFetchOptions('GET');
  
  fetch(`${API_BASE_URL}/check-session`, options)
  .then(response => response.json())
  .then(data => {
    if (!data.authenticated) {
      // Si el token no es válido, eliminar del localStorage y redirigir
      localStorage.removeItem('authToken');
      localStorage.removeItem('user_id');
      localStorage.removeItem('username');
      window.location.href = 'index.html';
    } else {
      // Activar geolocalización
      geolocateControl.trigger();
    }
  })
  .catch(error => {
    console.error('Error al comprobar sesión:', error);
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
  }
}

// Inicializar mapa
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

// Manejar errores de geolocalización
geolocateControl.on('error', (e) => {
  console.error('Error de geolocalización:', e.error);
  if (e.error.code === 1) {
    alert('Error: Permisos de ubicación denegados. Por favor habilita el acceso a tu ubicación en la configuración del navegador.');
  } else if (e.error.code === 2) {
    alert('Error: No se pudo determinar tu ubicación. Asegúrate de tener el GPS activado.');
  } else if (e.error.code === 3) {
    alert('Error: Tiempo de espera agotado al intentar obtener la ubicación.');
  }
});

// Activar geolocalización cuando el mapa esté listo
map.on('load', () => {
  console.log('Mapa cargado, intentando activar geolocalización...');
  geolocateControl.trigger(); // Intentar activar geolocalización cuando el mapa cargue
});

// Función para alternar la visibilidad del panel de información
function toggleInfoPanel() {
  const infoPanel = document.getElementById('info-panel');
  const isHidden = infoPanel.classList.toggle('hidden');
  localStorage.setItem('infoPanelHidden', isHidden); // Guardar el estado en localStorage
}

// Variable para almacenar el marcador actual
let currentMarker = null;
let trackingInterval = null;

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
      document.getElementById('location-info').innerHTML = 
        `<strong>Dirección:</strong> ${address}`;
    })
    .catch(err => console.error('Error al obtener la dirección:', err));

  // Actualizar la ubicación en el servidor usando token
  const options = getAuthFetchOptions('POST', {
    userId: authState.user_id,
    latitude,
    longitude
  });
  
  fetch(`${API_BASE_URL}/update-location`, options)
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(err => console.error('Error al actualizar la ubicación:', err));
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