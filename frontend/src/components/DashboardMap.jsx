import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { ENDPOINTS } from "../utils/api/endpoints.js";
import { IntensityLegendModal } from "../components/IntensityLegendModal.jsx";
import {IntensitySwitchPanel} from "../components/IntensitySwitchPanel.jsx"
import { useState } from "react";

export function DashboardMap() {
  const [legendMode, setLegendMode] = useState("current");

  useEffect(() => {
    // Initialize map
    const map = L.map("map").setView([12.5, 121.0], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(
      map
    );

    // Fetch and display danger zones
    fetch(ENDPOINTS.DANGER_ZONES_GEOJSON)
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

  return (
    <div className="relative flex justify-center my-2 mx-4 border-8 border-white rounded-lg shadow-lg overflow-visible">
      <div id="map" style={{ height: "500px", width: "100%" }}></div>
      {/* Legend at bottom left */}
      <div className="absolute left-4 bottom-4 z-[9999]">
        <IntensityLegendModal mode={legendMode} />
      </div>
      {/* Switch button at top right */}
      <div className="absolute right-4 top-4 z-[9999]">
        <IntensitySwitchPanel mode={legendMode} setMode={setLegendMode} />
      </div>
    </div>
  );
}
