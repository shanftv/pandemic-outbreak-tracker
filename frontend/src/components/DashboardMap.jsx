import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export function DashboardMap() {
  useEffect(() => {
    // Initialize map
    const map = L.map("map").setView([12.5, 121.0], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(
      map
    );

    // Fetch and display danger zones
    fetch("http://localhost:8000/api/v1/danger-zones/geojson")
      .then((response) => response.json())
      .then((data) => {
        L.geoJSON(data, {
          pointToLayer: (feature, latlng) => {
            return L.circle(latlng, {
              radius: feature.properties.radius,
              fillColor: feature.properties.color,
              fillOpacity: 0.6,
              color: "#ffffff",
              weight: 2,
            });
          },
          onEachFeature: (feature, layer) => {
            const props = feature.properties;
            layer.bindPopup(`
                            <h3>${props.name}</h3>
                            <p>Risk Score: ${props.riskScore}</p>
                            <p>Danger Level: ${props.dangerLevel}</p>
                            <p>Predicted (7d): ${props.predictedCases7d} cases</p>
                        `);
          },
        }).addTo(map);
      });

    // Cleanup on unmount
    return () => {
      map.remove();
    };
  }, []);

  return <div id="map" style={{ height: "500px", width: "100%" }}></div>;
}
