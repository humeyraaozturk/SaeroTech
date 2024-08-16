// Cesium Viewer'ı tanımla ve modül olarak dışa aktar
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1NGJiYmYwZi04Nzk4LTQyMTUtODc1Zi1jMTdkMWViYTAyYzQiLCJpZCI6MjI4NTYyLCJpYXQiOjE3MjEwNzYzOTd9.T6Gb-UYec7ZAy7iTPRc6QsPbnZ-0M7sRxdb6am_gg88';

let currentFlightEntity = null; // Aktif uçuş verisi
let orangePoints = []; // Turuncu noktaları takip et
let flightPath = null; // Güzergah yolunu takip et

// Uçuş animasyonunu başlatan işlev
document.getElementById('startFlight').addEventListener('click', () => {
  if (currentFlightEntity) {
    // Önceki uçuşu ve noktaları temizle
    viewer.entities.remove(currentFlightEntity);
    if (flightPath) {
      viewer.entities.remove(flightPath);
      flightPath = null;
    }
    orangePoints.forEach(point => viewer.entities.remove(point));
    orangePoints = [];
    currentFlightEntity = null;
  }
  startFlightAnimation();
});

async function startFlightAnimation() {
  try {
    const flightData = await fetchCSVData('..//waypoints.csv');
    if (flightData) {
      const { latitudes, longitudes, heights } = parseCSVData(flightData);
      const positions = createPositionsArray(latitudes, longitudes, heights);

      // Uçuş süresi: Koordinat sayısına bağlı olarak dinamik olarak ayarlanabilir
      const flightDuration = 60; // Uçuş süresi (saniye)
      const initialTime = Cesium.JulianDate.fromDate(new Date());

      // Tüm koordinat noktalarını turuncu olarak ekle
      addOrangePoints(latitudes, longitudes, heights);

      // Pozisyonları zamanla değiştiren özellik
      const property = new Cesium.SampledPositionProperty();
      positions.forEach((pos, index) => {
        const time = Cesium.JulianDate.addSeconds(initialTime, index * (flightDuration / (positions.length - 1)), new Cesium.JulianDate());
        property.addSample(time, pos);
      });

      // İlk pozisyona ayarla
      viewer.entities.add({
        position: positions[0],
        point: {
          pixelSize: 0, // Gizli bir nokta ekleyerek uçağın ilk koordinatta olmasını sağlıyoruz
        },
      });

      // Güzergah yolunu ekle
      flightPath = viewer.entities.add({
        polyline: {
          positions: new Cesium.CallbackProperty(() => positions, false),
          width: 5,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: 0.1,
            color: Cesium.Color.YELLOW,
          }),
        },
      });

      // Uçak modeli ekle
      currentFlightEntity = viewer.entities.add({
        availability: new Cesium.TimeIntervalCollection([new Cesium.TimeInterval({
          start: initialTime,
          stop: Cesium.JulianDate.addSeconds(initialTime, flightDuration, new Cesium.JulianDate()),
        })]),
        position: property,
        model: {
          uri: 'Cesium_Air.glb', // Model dosyasının yolu
          minimumPixelSize: 64,
          maximumScale: 200,
        },
        orientation: new Cesium.VelocityOrientationProperty(property),
        path: {
          resolution: 1,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: 0.1,
            color: Cesium.Color.YELLOW,
          }),
          width: 10,
        },
      });

      // Zamanlayıcı ayarları
      viewer.clock.startTime = initialTime;
      viewer.clock.stopTime = Cesium.JulianDate.addSeconds(initialTime, flightDuration, new Cesium.JulianDate());
      viewer.clock.currentTime = viewer.clock.startTime;
      viewer.clock.clockRange = Cesium.ClockRange.CLAMPED; // Uçuş tamamlandığında durdur
      viewer.clock.multiplier = 1;

      viewer.trackedEntity = currentFlightEntity;
    } else {
      console.error('Uçuş verileri alınamadı.');
    }
  } catch (error) {
    console.error('Uçuş animasyonu başlatılırken hata oluştu:', error);
  }
}

async function fetchCSVData(filename) {
  try {
    const response = await fetch(filename);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.text();
    return data;
  } catch (error) {
    console.error('CSV dosyası alınırken hata oluştu:', error);
    return null;
  }
}

function parseCSVData(data) {
  const latitudes = [];
  const longitudes = [];
  const heights = [];
  const rows = data.split('\n').slice(1); // İlk satır başlıkları içerebilir

  rows.forEach(row => {
    const [latitude, longitude, height] = row.split(',').map(Number);
    if (!isNaN(latitude) && !isNaN(longitude) && !isNaN(height)) {
      latitudes.push(latitude);
      longitudes.push(longitude);
      heights.push(height);
    }
  });

  return { latitudes, longitudes, heights };
}

function createPositionsArray(latitudes, longitudes, heights) {
  const positions = [];
  for (let i = 0; i < latitudes.length; i++) {
    const position = Cesium.Cartesian3.fromDegrees(longitudes[i], latitudes[i], heights[i]);
    positions.push(position);
  }
  return positions;
}

// Turuncu noktaları ekleyen fonksiyon
function addOrangePoints(latitudes, longitudes, heights) {
  latitudes.forEach((lat, index) => {
    const lon = longitudes[index];
    const height = heights[index];
    const point = viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(lon, lat, height),
      point: {
        pixelSize: 10,
        color: Cesium.Color.ORANGE,
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2,
      },
    });
    orangePoints.push(point);
  });
}
