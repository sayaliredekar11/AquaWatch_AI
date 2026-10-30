import { useState, useEffect, useRef } from 'react'
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Marker,
  Popup,
  useMap,
} from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getGisLocationsApi, searchPlacesApi } from '../services/api'
import {
  Droplets,
  AlertCircle,
  RefreshCw,
  MapPin,
  Calendar,
  Search,
  X,
  Loader2,
  Info,
  ArrowRight,
  RotateCcw,
  Compass,
  CheckCircle2,
} from 'lucide-react'

// Maharashtra geographic boundaries and center
const MAHARASHTRA_CENTER = [19.65, 75.6]
const DEFAULT_ZOOM = 7
const MIN_ZOOM = 6
const MAX_ZOOM = 18

// Bounding box for Maharashtra with padding to constrain panning
const MAHARASHTRA_MAX_BOUNDS = [
  [14.6, 71.0], // Southwest boundary
  [22.8, 82.0], // Northeast boundary
]

// Custom Leaflet DivIcon for searched locations (prominent amber/orange pulsing pin)
const searchPinIcon = L.divIcon({
  className: 'search-location-pin',
  html: `
    <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 38px; height: 38px; cursor: pointer;">
      <span style="position: absolute; width: 34px; height: 34px; border-radius: 9999px; background: rgba(234, 88, 12, 0.4); animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></span>
      <div style="position: relative; width: 30px; height: 30px; border-radius: 9999px; background: #ea580c; border: 2.5px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; color: white;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
      </div>
    </div>
  `,
  iconSize: [38, 38],
  iconAnchor: [19, 19],
  popupAnchor: [0, -20],
})

// Distance calculation using Haversine formula (km)
function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

// Helper to find the nearest monitoring station within a threshold distance (km)
function findNearbyMonitoringStation(targetLat, targetLon, stationList, maxDistanceKm = 15) {
  if (!stationList || stationList.length === 0) return null

  let closest = null
  let minDistance = Infinity

  for (const st of stationList) {
    if (st.latitude != null && st.longitude != null) {
      const dist = calculateDistanceKm(targetLat, targetLon, st.latitude, st.longitude)
      if (dist < minDistance && dist <= maxDistanceKm) {
        minDistance = dist
        closest = { ...st, distanceKm: dist }
      }
    }
  }

  return closest
}

// Controller to smoothly fly to searched coordinates or reset view
function MapViewController({ target, resetSignal, onMapReady }) {
  const map = useMap()

  useEffect(() => {
    if (map) {
      map.invalidateSize()
      if (onMapReady) {
        onMapReady(map)
      }
    }
  }, [map, onMapReady])

  useEffect(() => {
    if (target && target.lat != null && target.lon != null) {
      const zoom = target.zoom || 14
      try {
        map.stop()
        map.flyTo([target.lat, target.lon], zoom, {
          duration: 1.2,
          easeLinearity: 0.25,
        })
      } catch (err) {
        console.warn('flyTo interrupted/failed, using setView fallback:', err)
        map.setView([target.lat, target.lon], zoom)
      }
    }
  }, [target, map])

  useEffect(() => {
    if (resetSignal) {
      try {
        map.stop()
        map.flyTo(MAHARASHTRA_CENTER, DEFAULT_ZOOM, {
          duration: 1.0,
        })
      } catch (err) {
        map.setView(MAHARASHTRA_CENTER, DEFAULT_ZOOM)
      }
    }
  }, [resetSignal, map])

  return null
}

// Search marker with auto-opening popup
function SearchedLocationMarker({
  searchedLocation,
  matchedStation,
  onNavigateTrends,
  onClear,
}) {
  const markerRef = useRef(null)

  useEffect(() => {
    if (!markerRef.current) return
    const marker = markerRef.current
    marker.openPopup()
    const timer = setTimeout(() => {
      if (marker && marker.openPopup) {
        marker.openPopup()
      }
    }, 150)
    return () => clearTimeout(timer)
  }, [searchedLocation])

  if (!searchedLocation) return null

  return (
    <Marker
      ref={markerRef}
      position={[searchedLocation.lat, searchedLocation.lon]}
      icon={searchPinIcon}
      eventHandlers={{
        add: (e) => {
          setTimeout(() => {
            if (e.target && e.target.openPopup) {
              e.target.openPopup()
            }
          }, 100)
        },
      }}
    >
      <Popup className="custom-popup" autoPan={false}>
        <div className="space-y-2.5 p-1 text-slate-800 min-w-[240px] max-w-[290px]">
          {/* Header */}
          <div className="border-b border-slate-100 pb-2">
            <div className="flex items-center justify-between gap-1">
              <span className="inline-flex items-center gap-1 rounded bg-amber-50 border border-amber-200 px-1.5 py-0.5 text-[10px] font-bold text-amber-800 uppercase tracking-wide">
                <MapPin className="h-3 w-3" />
                Searched Place
              </span>
              <button
                type="button"
                onClick={onClear}
                className="text-[10px] text-slate-400 hover:text-slate-600 underline"
              >
                Dismiss
              </button>
            </div>
            <h4 className="font-bold text-sm text-slate-900 mt-1">
              {searchedLocation.name}
            </h4>
            <p className="text-[11px] text-slate-500 leading-snug mt-0.5 line-clamp-2">
              {searchedLocation.display_name}
            </p>
          </div>

          {/* Coordinates */}
          <div className="text-xs text-slate-600 flex items-center gap-1.5">
            <span className="font-mono text-[11px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">
              {searchedLocation.lat.toFixed(4)}°N, {searchedLocation.lon.toFixed(4)}°E
            </span>
            <span className="text-[10px] text-slate-500 capitalize">
              ({searchedLocation.type || 'Location'})
            </span>
          </div>

          {/* Connected AquaWatch Water Quality Section */}
          {matchedStation ? (
            <div className="rounded-lg bg-cyan-50/80 border border-cyan-200 p-2.5 space-y-2 text-xs">
              <div className="flex items-center justify-between gap-1">
                <div className="flex items-center gap-1 text-ocean font-bold text-[11px]">
                  <Droplets className="h-3.5 w-3.5 shrink-0" />
                  <span>AquaWatch Monitoring Station</span>
                </div>
                <span className="text-[10px] bg-white px-1.5 py-0.5 rounded border border-cyan-200 text-slate-600 font-medium">
                  {matchedStation.distanceKm < 1
                    ? `${(matchedStation.distanceKm * 1000).toFixed(0)}m away`
                    : `${matchedStation.distanceKm.toFixed(1)} km away`}
                </span>
              </div>
              <p className="font-semibold text-slate-900 text-xs">
                {matchedStation.name}
              </p>

              {matchedStation.latest_measurements && (
                <div className="rounded bg-white/90 p-1.5 border border-cyan-100 grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px]">
                  {matchedStation.latest_measurements.ph != null && (
                    <div>
                      <span className="text-slate-500">pH: </span>
                      <span className="font-semibold text-slate-800">
                        {matchedStation.latest_measurements.ph}
                      </span>
                    </div>
                  )}
                  {matchedStation.latest_measurements.dissolved_oxygen != null && (
                    <div>
                      <span className="text-slate-500">DO: </span>
                      <span className="font-semibold text-slate-800">
                        {matchedStation.latest_measurements.dissolved_oxygen} mg/L
                      </span>
                    </div>
                  )}
                  {matchedStation.latest_measurements.turbidity != null && (
                    <div>
                      <span className="text-slate-500">Turbidity: </span>
                      <span className="font-semibold text-slate-800">
                        {matchedStation.latest_measurements.turbidity} NTU
                      </span>
                    </div>
                  )}
                  {matchedStation.latest_measurements.tds != null && (
                    <div>
                      <span className="text-slate-500">TDS: </span>
                      <span className="font-semibold text-slate-800">
                        {matchedStation.latest_measurements.tds} mg/L
                      </span>
                    </div>
                  )}
                </div>
              )}

              <div className="text-[10px] text-slate-600">
                Status:{' '}
                <span className="font-semibold text-cyan-800">
                  {matchedStation.water_quality_status || 'Monitored'}
                </span>
              </div>

              <button
                type="button"
                onClick={() =>
                  onNavigateTrends(
                    matchedStation.location_id || matchedStation.water_body_id
                  )
                }
                className="w-full rounded bg-ocean py-1.5 text-center text-xs font-semibold text-white hover:bg-[#0c627a] transition-colors shadow-2xs flex items-center justify-center gap-1.5"
              >
                <span>View Water Quality Trends</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          ) : (
            <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5 space-y-1.5 text-xs text-slate-600">
              <div className="flex items-center gap-1.5 text-slate-700 font-semibold text-[11px]">
                <Info className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                <span>Water Quality Coverage</span>
              </div>
              <p className="text-[11px] leading-relaxed text-slate-700 font-semibold">
                No water-quality data available for this location yet.
              </p>
              <p className="text-[10px] text-slate-500 leading-normal">
                This location is currently not in the AquaWatch active sensor/laboratory monitoring network.
              </p>
            </div>
          )}
        </div>
      </Popup>
    </Marker>
  )
}

export default function WaterMap() {
  const navigate = useNavigate()
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState(null)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [searchedLocation, setSearchedLocation] = useState(null)
  const [outsideWarning, setOutsideWarning] = useState(null)
  const [selectedIndex, setSelectedIndex] = useState(-1)

  // Map view target controller & direct Leaflet instance ref
  const [viewTarget, setViewTarget] = useState(null)
  const [resetTrigger, setResetTrigger] = useState(0)
  const mapInstanceRef = useRef(null)

  const searchContainerRef = useRef(null)
  const debounceTimerRef = useRef(null)

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

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(event.target)
      ) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Select a search result and locate on map
  const handleSelectLocation = (place) => {
    setDropdownOpen(false)
    setOutsideWarning(null)
    setSelectedIndex(-1)

    const lat = parseFloat(place.lat)
    const lon = parseFloat(place.lon)

    if (isNaN(lat) || isNaN(lon)) {
      setOutsideWarning('Invalid coordinates for selected location.')
      return
    }

    // Strict validation: Must fall inside Maharashtra boundaries
    const isInsideMaharashtra =
      lat >= 15.5 && lat <= 22.2 && lon >= 72.5 && lon <= 81.0

    if (!isInsideMaharashtra) {
      setOutsideWarning(
        `The location "${place.name}" is outside Maharashtra. The map view is restricted to Maharashtra, India.`
      )
      return
    }

    // Determine appropriate street/local zoom level (13–15) based on location type
    let targetZoom = 14
    const type = (place.type || '').toLowerCase()
    if (type === 'city' || type === 'administrative' || type === 'county') {
      targetZoom = 13
    } else if (
      type === 'river' ||
      type === 'water' ||
      type === 'lake' ||
      type === 'reservoir' ||
      type === 'stream'
    ) {
      targetZoom = 14
    } else if (
      type === 'village' ||
      type === 'suburb' ||
      type === 'station' ||
      type === 'locality'
    ) {
      targetZoom = 15
    }

    const newLocation = {
      place_id: place.place_id,
      name: place.name,
      display_name: place.display_name,
      lat,
      lon,
      type: place.type,
      zoom: targetZoom,
      timestamp: Date.now(),
    }

    setSearchedLocation(newLocation)
    setViewTarget(newLocation)

    // Move map immediately if Leaflet instance is ready
    if (mapInstanceRef.current) {
      try {
        mapInstanceRef.current.stop()
        mapInstanceRef.current.flyTo([lat, lon], targetZoom, {
          duration: 1.2,
          easeLinearity: 0.25,
        })
      } catch (err) {
        mapInstanceRef.current.setView([lat, lon], targetZoom)
      }
    }
  }

  // Performs immediate search bypassing debounce and automatically selects top match
  const executeImmediateSearch = async (queryText) => {
    if (!queryText || queryText.trim().length < 2) return

    const cleanQ = queryText.trim().toLowerCase()
    setSearching(true)
    setSearchError(null)

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    try {
      // 1. Local monitoring station matches
      const localMatches = locations
        .filter((loc) => {
          const nameMatch = loc.name?.toLowerCase().includes(cleanQ)
          const locNameMatch = loc.location_name?.toLowerCase().includes(cleanQ)
          const typeMatch = loc.water_body_type?.toLowerCase().includes(cleanQ)
          return nameMatch || locNameMatch || typeMatch
        })
        .map((loc) => ({
          place_id: `station_${loc.location_id || loc.water_body_id}`,
          name: loc.name,
          display_name: `${loc.name}, ${loc.location_name}`,
          lat: loc.latitude,
          lon: loc.longitude,
          type: loc.water_body_type || 'station',
          is_station: true,
          station_data: loc,
          is_maharashtra: true,
        }))

      // 2. Geocoding API for places in Maharashtra
      const apiPlaces = await searchPlacesApi(queryText)

      const combined = [...localMatches]
      for (const p of apiPlaces) {
        const exists = combined.some(
          (item) =>
            calculateDistanceKm(item.lat, item.lon, p.lat, p.lon) < 0.5 ||
            item.name.toLowerCase() === p.name.toLowerCase()
        )
        if (!exists) {
          combined.push(p)
        }
      }

      setSearchResults(combined)

      if (combined.length > 0) {
        handleSelectLocation(combined[0])
      } else {
        setDropdownOpen(true)
        setSelectedIndex(-1)
      }
    } catch (err) {
      setSearchError('Search request failed. Please check your network connection.')
      setDropdownOpen(true)
    } finally {
      setSearching(false)
    }
  }

  // Debounced search effect for typing suggestions
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSearchResults([])
      setSearching(false)
      setSearchError(null)
      setSelectedIndex(-1)
      return
    }

    const cleanQ = searchQuery.trim().toLowerCase()
    setSearching(true)
    setSearchError(null)

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    debounceTimerRef.current = setTimeout(async () => {
      try {
        // 1. Check local monitoring stations matching the query
        const localMatches = locations
          .filter((loc) => {
            const nameMatch = loc.name?.toLowerCase().includes(cleanQ)
            const locNameMatch = loc.location_name?.toLowerCase().includes(cleanQ)
            const typeMatch = loc.water_body_type?.toLowerCase().includes(cleanQ)
            return nameMatch || locNameMatch || typeMatch
          })
          .map((loc) => ({
            place_id: `station_${loc.location_id || loc.water_body_id}`,
            name: loc.name,
            display_name: `${loc.name}, ${loc.location_name}`,
            lat: loc.latitude,
            lon: loc.longitude,
            type: loc.water_body_type || 'station',
            is_station: true,
            station_data: loc,
            is_maharashtra: true,
          }))

        // 2. Query geocoding API for places in Maharashtra
        const apiPlaces = await searchPlacesApi(searchQuery)

        // Combine local station matches + geocoding places, avoiding duplicates
        const combined = [...localMatches]
        for (const p of apiPlaces) {
          const exists = combined.some(
            (item) =>
              calculateDistanceKm(item.lat, item.lon, p.lat, p.lon) < 0.5 ||
              item.name.toLowerCase() === p.name.toLowerCase()
          )
          if (!exists) {
            combined.push(p)
          }
        }

        setSearchResults(combined)
        setSelectedIndex(combined.length > 0 ? 0 : -1)
        setDropdownOpen(true)
      } catch (err) {
        setSearchError('Search request failed. Please check your connection.')
      } finally {
        setSearching(false)
      }
    }, 450)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [searchQuery, locations])

  // Keyboard navigation for search input and dropdown
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!dropdownOpen) {
        setDropdownOpen(true)
      } else if (searchResults.length > 0) {
        setSelectedIndex((prev) =>
          prev < searchResults.length - 1 ? prev + 1 : 0
        )
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (!dropdownOpen) {
        setDropdownOpen(true)
      } else if (searchResults.length > 0) {
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : searchResults.length - 1
        )
      }
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (dropdownOpen && selectedIndex >= 0 && searchResults[selectedIndex]) {
        handleSelectLocation(searchResults[selectedIndex])
      } else if (dropdownOpen && searchResults.length > 0) {
        handleSelectLocation(searchResults[0])
      } else if (searchQuery.trim().length >= 2) {
        executeImmediateSearch(searchQuery.trim())
      }
    } else if (e.key === 'Escape') {
      setDropdownOpen(false)
    }
  }

  // Quick chip suggestion click
  const handleQuickSearch = (placeName) => {
    setSearchQuery(placeName)
    executeImmediateSearch(placeName)
  }

  // Clear current search
  const handleClearSearch = () => {
    setSearchQuery('')
    setSearchResults([])
    setDropdownOpen(false)
    setSearchedLocation(null)
    setOutsideWarning(null)
    setSelectedIndex(-1)
  }

  // Reset map view to Maharashtra
  const handleResetToMaharashtra = () => {
    setResetTrigger((prev) => prev + 1)
  }

  // Find nearby station for the currently searched location
  const matchedStation = searchedLocation
    ? findNearbyMonitoringStation(searchedLocation.lat, searchedLocation.lon, locations, 15)
    : null

  const handleNavigateTrends = (locationId) => {
    navigate(`/intelligence?location_id=${encodeURIComponent(locationId)}`)
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-ocean">
              GEOGRAPHIC INFORMATION SYSTEM
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-cyan-100/70 border border-cyan-200 px-2 py-0.5 text-[10px] font-bold text-ocean uppercase">
              <Compass className="h-3 w-3" />
              Maharashtra View
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-extrabold text-ink sm:text-3xl">
            Maharashtra Water Quality Map
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Interactive spatial monitoring across Maharashtra, India with localized place and water-body search.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleResetToMaharashtra}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
            title="Reset map view to entire Maharashtra state"
          >
            <RotateCcw className="h-3.5 w-3.5 text-slate-500" />
            <span>Center Maharashtra</span>
          </button>
          <button
            type="button"
            onClick={fetchLocations}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Markers</span>
          </button>
        </div>
      </div>

      {/* Location Search Bar Section */}
      <div
        ref={searchContainerRef}
        className="relative z-50 space-y-2"
        style={{ zIndex: 1050 }}
      >
        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
            <Search className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              if (!dropdownOpen && e.target.value.trim().length >= 2) {
                setDropdownOpen(true)
              }
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (searchResults.length > 0) setDropdownOpen(true)
            }}
            placeholder="Search a place in Maharashtra..."
            className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-24 text-sm text-slate-800 placeholder-slate-400 shadow-sm focus:border-ocean focus:outline-none focus:ring-2 focus:ring-ocean/20 transition-all"
            autoComplete="off"
            aria-autocomplete="list"
          />

          <div className="absolute inset-y-0 right-0 flex items-center pr-3 gap-1.5">
            {searching && <Loader2 className="h-4 w-4 animate-spin text-ocean" />}
            {searchQuery && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
                title="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <span className="hidden sm:inline-block text-[11px] font-semibold text-slate-400 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
              MH Only
            </span>
          </div>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-600">
          <span className="text-[11px] font-semibold text-slate-400 mr-1">Quick Search:</span>
          {[
            'Sangli',
            'Pune',
            'Nashik',
            'Kolhapur',
            'Mumbai',
            'Panchganga River, Kolhapur',
            'Krishna River, Sangli',
            'Venna Lake',
          ].map((place) => (
            <button
              key={place}
              type="button"
              onClick={() => handleQuickSearch(place)}
              className="rounded-full bg-slate-100 hover:bg-cyan-50 hover:text-ocean hover:border-cyan-200 border border-slate-200 px-2.5 py-0.5 text-[11px] font-medium transition-colors cursor-pointer"
            >
              {place}
            </button>
          ))}
        </div>

        {/* Search Results Dropdown */}
        {dropdownOpen && (
          <div
            className="absolute left-0 right-0 top-full mt-1 max-h-80 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl ring-1 ring-black/5 divide-y divide-slate-100"
            style={{ zIndex: 1100 }}
          >
            {searching && searchResults.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-ocean" />
                <span>Searching locations across Maharashtra...</span>
              </div>
            ) : searchError ? (
              <div className="p-3.5 text-xs text-rose-600 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{searchError}</span>
              </div>
            ) : searchResults.length === 0 && searchQuery.trim().length >= 2 ? (
              <div className="p-4 text-center text-xs text-slate-500 space-y-1">
                <p className="font-semibold text-slate-700">No places found in Maharashtra</p>
                <p className="text-[11px] text-slate-400">
                  Try searching a major city, river, lake, or district within Maharashtra state.
                </p>
              </div>
            ) : (
              searchResults.map((item, idx) => (
                <button
                  key={item.place_id}
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    handleSelectLocation(item)
                  }}
                  onClick={() => handleSelectLocation(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full px-4 py-2.5 text-left transition-colors flex items-start gap-3 group cursor-pointer ${
                    selectedIndex === idx
                      ? 'bg-cyan-50/90 border-l-4 border-ocean pl-3'
                      : 'hover:bg-cyan-50/60'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {item.is_station ? (
                      <div className="rounded-full bg-cyan-100 p-1 text-ocean">
                        <Droplets className="h-3.5 w-3.5" />
                      </div>
                    ) : (
                      <div className="rounded-full bg-slate-100 p-1 text-slate-500 group-hover:bg-amber-100 group-hover:text-amber-600 transition-colors">
                        <MapPin className="h-3.5 w-3.5" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900 truncate">
                        {item.name}
                      </span>
                      {item.is_station ? (
                        <span className="rounded bg-cyan-100 border border-cyan-200 px-1.5 py-0.2 text-[10px] font-bold text-ocean uppercase">
                          AquaWatch Station
                        </span>
                      ) : (
                        <span className="rounded bg-slate-100 px-1.5 py-0.2 text-[10px] font-medium text-slate-500 capitalize">
                          {item.type || 'place'}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">
                      {item.display_name}
                    </p>
                  </div>
                  <div className="text-[10px] font-mono text-slate-400 shrink-0 mt-0.5">
                    {item.lat.toFixed(2)}°, {item.lon.toFixed(2)}°
                  </div>
                </button>
              ))
            )}

            <div className="bg-slate-50 px-3 py-1.5 text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-100">
              <span>Restricted to Maharashtra, India &middot; Use &uarr;&darr; and Enter to navigate</span>
              <span>OpenStreetMap &copy; Nominatim</span>
            </div>
          </div>
        )}
      </div>

      {/* Outside Maharashtra Warning Banner */}
      {outsideWarning && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs text-amber-800 flex items-start justify-between gap-3 shadow-xs">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <p className="font-bold text-amber-900">Location Outside Maharashtra</p>
              <p className="text-amber-800 mt-0.5">{outsideWarning}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setOutsideWarning(null)}
            className="text-amber-700 hover:text-amber-900 font-bold"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Searched Location Active Indicator */}
      {searchedLocation && (
        <div className="rounded-xl border border-orange-200 bg-orange-50/70 p-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 text-xs">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-orange-500 shrink-0 animate-pulse" />
            <span className="font-bold text-slate-800">
              Pinplaced on: <span className="text-orange-700">{searchedLocation.name}</span>
            </span>
            <span className="text-slate-500 font-mono text-[11px]">
              ({searchedLocation.lat.toFixed(4)}°N, {searchedLocation.lon.toFixed(4)}°E)
            </span>
          </div>
          <div className="flex items-center gap-2">
            {matchedStation && (
              <span className="text-ocean font-semibold text-[11px] bg-cyan-100/80 px-2 py-0.5 rounded border border-cyan-200">
                Matches Station: {matchedStation.name}
              </span>
            )}
            <button
              type="button"
              onClick={() => setSearchedLocation(null)}
              className="text-xs text-slate-600 hover:text-slate-900 underline font-medium"
            >
              Clear Pin
            </button>
          </div>
        </div>
      )}

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

      {/* Map Container - Centered on Maharashtra, bounded to Maharashtra */}
      <div className="relative h-[580px] overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm">
        {loading && (
          <div className="absolute inset-0 z-1000 flex flex-col items-center justify-center bg-white/70 backdrop-blur-xs">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-ocean border-t-transparent" />
            <p className="mt-2 text-xs font-medium text-slate-600">
              Loading Maharashtra monitoring stations...
            </p>
          </div>
        )}

        <MapContainer
          center={MAHARASHTRA_CENTER}
          zoom={DEFAULT_ZOOM}
          minZoom={MIN_ZOOM}
          maxZoom={MAX_ZOOM}
          maxBounds={MAHARASHTRA_MAX_BOUNDS}
          maxBoundsViscosity={0.8}
          className="h-full w-full"
        >
          {/* Smooth view controller */}
          <MapViewController
            target={viewTarget}
            resetSignal={resetTrigger}
            onMapReady={(map) => {
              mapInstanceRef.current = map
            }}
          />

          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Searched location marker */}
          <SearchedLocationMarker
            searchedLocation={searchedLocation}
            matchedStation={matchedStation}
            onNavigateTrends={handleNavigateTrends}
            onClear={() => setSearchedLocation(null)}
          />

          {/* Preserved AquaWatch water quality monitoring markers */}
          {locations.map((loc) => {
            const hasCoords = loc.latitude !== null && loc.longitude !== null
            if (!hasCoords) return null

            return (
              <CircleMarker
                key={loc.location_id || loc.water_body_id}
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
                  <div className="space-y-2 p-1 text-slate-800 min-w-[230px]">
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
                          {loc.latitude.toFixed(4)}°N, {loc.longitude.toFixed(4)}°E
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
                      <p className="font-semibold">Status: {loc.water_quality_status || 'UNKNOWN'}</p>
                      {loc.status_reason && (
                        <p className="text-[10px] text-cyan-700 mt-0.5">{loc.status_reason}</p>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        handleNavigateTrends(loc.location_id || loc.water_body_id)
                      }
                      className="w-full mt-2 rounded bg-ocean py-1.5 text-center text-xs font-semibold text-white hover:bg-[#0c627a] transition-colors shadow-2xs flex items-center justify-center gap-1.5"
                    >
                      <span>View Water Quality Trends</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>

      {/* Bottom station summary counts */}
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
