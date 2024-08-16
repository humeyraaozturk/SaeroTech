// Sayfa ilk açıldığında New York'a uç
viewer.scene.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(30.3272086,40.7437668 , 750),
    orientation: {
      heading: Cesium.Math.toRadians(20),
      pitch: Cesium.Math.toRadians(-20),
    },
    duration: 0,
});

// Bulut koleksiyonu oluştur
const clouds = new Cesium.BillboardCollection();
viewer.scene.primitives.add(clouds);

let currentBillboards = [];

// Renkler için fonksiyon
function getColor(colorName) {
  switch (colorName) {
    case "Green": return Cesium.Color.GREEN;
    case "Yellow": return Cesium.Color.YELLOW;
    case "Orange": return Cesium.Color.ORANGE;
    case "Red": return Cesium.Color.RED;
    case "DarkRed": return Cesium.Color.DARKRED;
    case "Black": return Cesium.Color.BLACK;
    case "Purple": return Cesium.Color.PURPLE;
    case "Brown": return Cesium.Color.BROWN;
    default: return Cesium.Color.BLACK;
  }
}

// Her gaz butonu için tıklama olayını dinle
document.querySelectorAll('.gas-button').forEach(button => {
  button.addEventListener('click', () => {
    const gasName = button.textContent.trim();
    const filename = button.getAttribute('data-filename');

    removeCurrentBillboards();

    console.log(gasName);
    console.log(filename);
    readCSV(filename, (headers, values) => {
      addCloudsForGas(gasName, values);
    });
  });
});

// CSV dosyasını okuma fonksiyonu
function readCSV(filename, callback) {
  fetch(filename)
    .then(response => response.text())
    .then(data => {
      data = data.replace(/ /g, '');
      Papa.parse(data, {
        header: true,  // Başlık satırını kullanarak sütun isimlerini al
        dynamicTyping: true,
        complete: function (results) {
          const headers = results.meta.fields;
          const rows = results.data;

          // Sütunları ayrı ayrı dizi olarak oluştur
          const columns = headers.reduce((acc, header) => {
            acc[header] = rows.map(row => row[header]);
            return acc;
          }, {});

          callback(headers, columns);
        }
      });
    })
    .catch(error => console.error('Error fetching the CSV file:', error));
}

// Gaz yoğunluğuna göre renk alma fonksiyonu
function getColorByGasDensity(gas, density) {
  switch (gas) {
    case "C2H5OH":
      if (density >= 0 && density < 10) return getColor("Green");
      if (density >= 10 && density < 50) return getColor("Yellow");
      if (density >= 50 && density < 100) return getColor("Orange");
      if (density >= 100 && density < 500) return getColor("Red");
      if (density >= 500 && density < 1000) return getColor("DarkRed");
      if (density >= 1000) return getColor("Black");
      return getColor("Black"); // Varsayılan renk
    case "CH4":
      if (density >= 0 && density < 5) return getColor("Green");
      if (density >= 5) return getColor("Red");
      return getColor("Black"); // Varsayılan renk
    case "CO":
      if (density >= 0 && density < 0.01) return getColor("Green");
      if (density >= 0.01 && density < 0.05) return getColor("Yellow");
      if (density >= 0.05) return getColor("Red");
      return getColor("Black"); // Varsayılan renk
    case "H2":
      if (density >= 0 && density < 10) return getColor("Green");
      if (density >= 10) return getColor("Red");
      return getColor("Black"); // Varsayılan renk
    case "NO2":
      if (density >= 0 && density < 0.3) return getColor("Red");
      if (density >= 0.3 && density < 0.5) return getColor("Yellow");
      if (density >= 0.5) return getColor("Red");
      return getColor("Black"); // Varsayılan renk
    case "NH3":
      if (density >= 0 && density < 10) return getColor("Green");
      if (density >= 10 && density < 25) return getColor("Yellow");
      if (density >= 25 && density < 50) return getColor("Orange");
      if (density >= 50) return getColor("Red");
      return getColor("Black"); // Varsayılan renk
    case "H2S":
      if (density >= 0 && density < 0.01) return getColor("Green");
      if (density >= 0.01 && density < 0.05) return getColor("Yellow");
      if (density >= 0.05) return getColor("Red");
      return getColor("Black"); // Varsayılan renk
    case "SO2":
      if (density >= 0 && density < 0.05) return getColor("Green");
      if (density >= 0.05 && density < 0.2) return getColor("Yellow");
      if (density >= 0.2) return getColor("Red");
      return getColor("Black"); // Varsayılan renk
    case "pm2.5":
      if (density >= 0 && density < 0.05) return getColor("Green");
      if (density >= 0.05 && density < 0.1) return getColor("Yellow");
      if (density >= 0.1 && density < 0.25) return getColor("Red");
      if (density >= 0.25 && density < 0.5) return getColor("Purple");
      if (density >= 0.5) return getColor("Brown");
      return getColor("Black"); // Varsayılan renk
    default:
      return getColor("Black"); // Diğer gazlar için varsayılan renk
  }
}

// Bulutları kaldıran fonksiyon
function removeCurrentBillboards() {
  currentBillboards.forEach(billboard => {
    clouds.remove(billboard);
  });
  currentBillboards = []; // Diziyi temizle
}

// Her gaz için bulutları eklemek için fonksiyon
function addCloudsForGas(gasName, values) {
  const { Latitude, Longitude, density } = values;

  Latitude.forEach((lat, index) => {
    const lon = Longitude[index];
    const dens = density[index];
    const color = getColorByGasDensity(gasName, dens);
    const billboard = clouds.add({
      position: Cesium.Cartesian3.fromDegrees(lon, lat, dens * 100),
      image: createColorTexture(color),
      sizeInMeters: true,
      pixelSize: dens * 2 // Bulut boyutunu artırmak için
    });
    currentBillboards.push(billboard);
  });
  
  function createColorTexture(color) {
    var canvas = document.createElement('canvas');
    canvas.width = 128;  // Daha büyük bir canvas boyutu
    canvas.height = 128;
    var context = canvas.getContext('2d');
    
    // Bulut şeklini oluşturmak için yumuşak bir daire çiz
    var radius = 64; // Canvas boyutunun yarısı
    var gradient = context.createRadialGradient(radius, radius, 0, radius, radius, radius);
    gradient.addColorStop(0, 'rgba(' + Math.floor(color.red * 255) + ',' + Math.floor(color.green * 255) + ',' + Math.floor(color.blue * 255) + ', 0.8)');
    gradient.addColorStop(1, 'rgba(' + Math.floor(color.red * 255) + ',' + Math.floor(color.green * 255) + ',' + Math.floor(color.blue * 255) + ', 0)');
    
    context.fillStyle = gradient;
    context.beginPath();
    context.arc(radius, radius, radius, 0, Math.PI * 2, false);
    context.closePath();
    context.fill();
    
    return canvas;
  }
}
