/**
 * AquaWatch AI - Centralized Backend API Client
 *
 * Configurable via Vite environment variable: VITE_API_BASE_URL (defaults to http://localhost:8000)
 * Manages Bearer JWT injection, response parsing, and error extraction.
 */

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
).replace(/\/+$/, '')

export const TOKEN_KEY = 'aquawatch_access_token'
export const USER_KEY = 'aquawatch_user'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token)
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * Core HTTP request handler
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = { ...(options.headers || {}) }

  const token = getToken()
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // Handle JSON bodies automatically if not form/url-encoded
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams) &&
    typeof options.body !== 'string'
  ) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(options.body)
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`
    try {
      const errJson = await response.json()
      if (errJson?.detail) {
        if (typeof errJson.detail === 'string') {
          errorDetail = errJson.detail
        } else if (Array.isArray(errJson.detail)) {
          errorDetail = errJson.detail
            .map((item) => item.msg || `${item.loc?.join('.')}: invalid value`)
            .join('; ')
        }
      }
    } catch (_) {
      // Non-JSON error body fallback
    }

    const error = new Error(errorDetail)
    error.status = response.status
    throw error
  }

  if (response.status === 204) {
    return null
  }

  return await response.json()
}

// ==========================================================
// Authentication APIs
// ==========================================================

export async function loginApi(email, password) {
  // OAuth2PasswordRequestForm requires application/x-www-form-urlencoded
  const params = new URLSearchParams()
  params.append('username', email.trim().toLowerCase())
  params.append('password', password)

  const tokenData = await request('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params,
  })

  return tokenData
}

export async function registerApi(name, email, password, invitation_token) {
  return await request('/auth/register', {
    method: 'POST',
    body: {
      name: name.trim(),
      email: email.trim().toLowerCase(),
      password,
      invitation_token: invitation_token ? invitation_token.trim() : '',
    },
  })
}

export async function validateInvitationApi(token) {
  return await request(`/auth/invitations/validate?token=${encodeURIComponent(token.trim())}`, {
    method: 'GET',
  })
}

export async function createInvitationApi(data = {}) {
  return await request('/auth/invitations', {
    method: 'POST',
    body: data,
  })
}

export async function getProfileApi() {
  return await request('/auth/me', {
    method: 'GET',
  })
}

// ==========================================================
// GIS & Location APIs
// ==========================================================

export async function getGisLocationsApi() {
  return await request('/gis/locations', {
    method: 'GET',
  })
}

export async function getGisLocationDetailApi(id) {
  return await request(`/gis/locations/${encodeURIComponent(id)}`, {
    method: 'GET',
  })
}

export async function getLocationHistoryApi(locationId, params = {}) {
  const query = new URLSearchParams()
  if (params.start_date) query.append('start_date', params.start_date)
  if (params.end_date) query.append('end_date', params.end_date)
  if (params.limit) query.append('limit', params.limit)
  const qs = query.toString() ? `?${query.toString()}` : ''
  return await request(`/gis/locations/${encodeURIComponent(locationId)}/history${qs}`, {
    method: 'GET',
  })
}

// ==========================================================
// Dashboard & Analytics APIs
// ==========================================================

export async function getDashboardSummaryApi() {
  return await request('/dashboard/summary', {
    method: 'GET',
  })
}

export async function getOfficialDashboardSummaryApi() {
  return await request('/dashboard/official-summary', {
    method: 'GET',
  })
}

export async function getWaterQualityOverviewApi(params = {}) {
  const query = new URLSearchParams()
  if (params.water_body_id) query.append('water_body_id', params.water_body_id)
  if (params.start_date) query.append('start_date', params.start_date)
  if (params.end_date) query.append('end_date', params.end_date)
  const qs = query.toString() ? `?${query.toString()}` : ''
  return await request(`/dashboard/water-quality-overview${qs}`, {
    method: 'GET',
  })
}

export async function getRecentMeasurementsApi(limit = 10) {
  return await request(`/dashboard/recent-measurements?limit=${limit}`, {
    method: 'GET',
  })
}

// ==========================================================
// Water Bodies CRUD APIs
// ==========================================================

export async function getWaterBodiesApi(skip = 0, limit = 50) {
  return await request(`/water-bodies?skip=${skip}&limit=${limit}`, {
    method: 'GET',
  })
}

export async function createWaterBodyApi(data) {
  return await request('/water-bodies', {
    method: 'POST',
    body: data,
  })
}

// ==========================================================
// Water Quality Measurement APIs
// ==========================================================

export async function getWaterQualityRecordsApi(params = {}) {
  const query = new URLSearchParams()
  if (params.skip !== undefined) query.append('skip', params.skip)
  if (params.limit !== undefined) query.append('limit', params.limit)
  if (params.water_body_id) query.append('water_body_id', params.water_body_id)
  if (params.start_date) query.append('start_date', params.start_date)
  if (params.end_date) query.append('end_date', params.end_date)
  const qs = query.toString() ? `?${query.toString()}` : ''
  return await request(`/water-quality${qs}`, {
    method: 'GET',
  })
}

export async function createWaterQualityRecordApi(data) {
  return await request('/water-quality', {
    method: 'POST',
    body: data,
  })
}

export async function testWaterQualityApi(testPayload) {
  return await request('/water-quality/test', {
    method: 'POST',
    body: testPayload,
  })
}

export async function getDemoSamplesApi() {
  return await request('/water-quality/demo-samples', {
    method: 'GET',
  })
}

// ==========================================================
// Machine Learning Prediction APIs
// ==========================================================

export async function predictWaterQualityApi(inputFeatures) {
  return await request('/predictions/predict', {
    method: 'POST',
    body: inputFeatures,
  })
}

export async function predictFromRecordApi(recordId) {
  return await request(`/predictions/record/${recordId}`, {
    method: 'GET',
  })
}
