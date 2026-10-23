import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import { getGisLocationsApi } from '../services/api'
import { Droplets, AlertCircle, RefreshCw, MapPin, Calendar, Activity } from 'lucide-react'

// Helper component to center map when locations are loaded
function ChangeView({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, zoom)
    }
  }, [center, zoom, map])
  return null
}

export default function WaterMap() {
  const navigate = useNavigate()
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchLocations = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getGisLocationsApi()
      setLocations(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message || 'Failed to load monitoring locations from backend.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLocations()
  }, [])

  const defaultCenter =
    locations.length > 0 && locations[0].latitude && locations[0].longitude
      ? [locations[0].latitude, locations[0].longitude]
      : [20.5937, 78.9629] // India default center

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-ocean">
            GEOGRAPHIC INFORMATION SYSTEM
          </span>
          <h1 className="mt-1 text-2xl font-extrabold text-ink sm:text-3xl">
            Water Quality Map
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Real-time monitoring stations and latest validated measurements from PostgreSQL.
          </p>
        </div>
        <button
          type="button"
          onClick={fetchLocations}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Map</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-rose-600" />
          <div className="flex-1">
            <p className="font-semibold">Unable to fetch map markers</p>
            <p className="text-xs mt-0.5">{error}</p>
          </div>
          <button
            onClick={fetchLocations}
            className="text-xs font-bold underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Map Container */}
      <div className="relative h-[560px] overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm">
        {loading && (
          <div className="absolute inset-0 z-1000 flex flex-col items-center justify-center bg-white/70 backdrop-blur-xs">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-ocean border-t-transparent" />
            <p className="mt-2 text-xs font-medium text-slate-600">Loading monitoring stations...</p>
          </div>
        )}

        <MapContainer
          center={defaultCenter}
          zoom={locations.length > 0 ? 9 : 5}
          className="h-full w-full"
        >
          <ChangeView center={defaultCenter} zoom={locations.length > 0 ? 9 : 5} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {locations.map((loc) => {
            const hasCoords = loc.latitude !== null && loc.longitude !== null
            if (!hasCoords) return null

            return (
              <CircleMarker
                key={loc.water_body_id}
                center={[loc.latitude, loc.longitude]}
                radius={10}
                pathOptions={{
                  color: '#ffffff',
                  weight: 2,
                  fillColor: '#0e7490',
                  fillOpacity: 0.9,
                }}
              >
                <Popup className="custom-popup">
                  <div className="space-y-2 p-1 text-slate-800 min-w-[220px]">
                    <div className="border-b border-slate-100 pb-1.5">
                      <div className="flex items-center justify-between gap-1.5">
                        <p className="font-bold text-sm text-slate-900">{loc.name}</p>
                        {loc.is_demo && (
                          <span className="rounded bg-amber-100 border border-amber-300 px-1.5 py-0.5 text-[10px] font-bold text-amber-800 uppercase tracking-wide shrink-0">
                            DEMO
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 capitalize">
                        {loc.water_body_type} &middot; {loc.location_name}
                      </p>
                    </div>

                    <div className="text-xs space-y-1">
                      <p className="flex items-center gap-1.5 text-slate-600">
                        <MapPin className="h-3 w-3 text-slate-400" />
                        <span>
                          {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}
                        </span>
                      </p>
                      <p className="flex items-center gap-1.5 text-slate-600">
                        <Calendar className="h-3 w-3 text-slate-400" />
                        <span>
                          {loc.latest_measured_at
                            ? new Date(loc.latest_measured_at).toLocaleDateString('en-GB', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric',
                              })
                            : 'No measurements logged yet'}
                        </span>
                      </p>
                    </div>

                    {loc.latest_measurements && (
                      <div className="rounded-lg bg-slate-50 p-2 border border-slate-100">
                        <p className="font-semibold text-[11px] text-slate-700 uppercase tracking-wider mb-1">
                          Latest Measurements
                        </p>
                        <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-xs">
                          {loc.latest_measurements.ph !== null && (
                            <div>
                              <span className="text-slate-500">pH: </span>
                              <span className="font-semibold">{loc.latest_measurements.ph}</span>
                            </div>
                          )}
                          {loc.latest_measurements.dissolved_oxygen !== null && (
                            <div>
                              <span className="text-slate-500">DO: </span>
                              <span className="font-semibold">{loc.latest_measurements.dissolved_oxygen} mg/L</span>
                            </div>
                          )}
                          {loc.latest_measurements.bod !== null && (
                            <div>
                              <span className="text-slate-500">BOD: </span>
                              <span className="font-semibold">{loc.latest_measurements.bod} mg/L</span>
                            </div>
                          )}
                          {loc.latest_measurements.turbidity !== null && (
                            <div>
                              <span className="text-slate-500">Turbidity: </span>
                              <span className="font-semibold">{loc.latest_measurements.turbidity} NTU</span>
                            </div>
                          )}
                          {loc.latest_measurements.tds !== null && (
                            <div>
                              <span className="text-slate-500">TDS: </span>
                              <span className="font-semibold">{loc.latest_measurements.tds} mg/L</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="text-[11px] rounded bg-cyan-50 border border-cyan-100 p-1.5 text-cyan-900">
                      <p className="font-semibold">Status: {loc.water_quality_status}</p>
                      {loc.status_reason && (
                        <p className="text-[10px] text-cyan-700 mt-0.5">{loc.status_reason}</p>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        navigate(
                          `/intelligence?location_id=${encodeURIComponent(
                            loc.location_id || loc.water_body_id
                          )}`
                        )
                      }
                      className="w-full mt-2 rounded bg-ocean py-1.5 text-center text-xs font-semibold text-white hover:bg-[#0c627a] transition-colors shadow-2xs"
                    >
                      View Water Quality Trends
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>

      {/* Station summary counts */}
      {!loading && locations.length === 0 && !error && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center space-y-2">
          <Droplets className="h-8 w-8 text-slate-400 mx-auto" />
          <h3 className="font-bold text-slate-800">No Monitored Stations Yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Water bodies added with valid coordinates by Laboratory Authorities will appear as interactive map markers.
          </p>
        </div>
      )}
    </div>
  )
}
