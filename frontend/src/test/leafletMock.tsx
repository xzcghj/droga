import type { ReactNode } from "react";

/** Lekka atrapa react-leaflet do testów w jsdom (Leaflet potrzebuje prawdziwego layoutu). */
export const leafletMock = {
  MapContainer: ({ children }: { children?: ReactNode }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Marker: ({ children }: { children?: ReactNode }) => <div data-testid="marker">{children}</div>,
  Polyline: () => <div data-testid="line" />,
  Tooltip: ({ children }: { children?: ReactNode }) => <>{children}</>,
  useMap: () => ({ fitBounds: () => undefined, setView: () => undefined }),
};
