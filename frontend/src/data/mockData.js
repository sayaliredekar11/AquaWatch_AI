// All values below are MOCK data for the prototype.
export const CATEGORIES = {
  Good: { color: '#16a34a', bg: 'bg-green-100 text-green-800' },
  Moderate: { color: '#eab308', bg: 'bg-yellow-100 text-yellow-800' },
  Poor: { color: '#f97316', bg: 'bg-orange-100 text-orange-800' },
  'Very Poor': { color: '#dc2626', bg: 'bg-red-100 text-red-800' },
}

export const locations = [
  { id: 'sangli', name: 'Sangli', lat: 16.8524, lng: 74.5815, wqi: 82.6, category: 'Good', lastTested: '23 Sep 2026', trend: '+8.4%' },
  { id: 'miraj', name: 'Miraj', lat: 16.8219, lng: 74.6457, wqi: 61.2, category: 'Moderate', lastTested: '20 Sep 2026', trend: '-2.1%' },
  { id: 'kolhapur', name: 'Kolhapur', lat: 16.705, lng: 74.2433, wqi: 44.8, category: 'Poor', lastTested: '18 Sep 2026', trend: '-5.6%' },
  { id: 'pune', name: 'Pune', lat: 18.5204, lng: 73.8567, wqi: 28.3, category: 'Very Poor', lastTested: '15 Sep 2026', trend: '-9.2%' },
]

export const parameters = [
  { key: 'ph', label: 'pH', value: 7.4, unit: '' },
  { key: 'do', label: 'DO', value: 7.1, unit: 'mg/L' },
  { key: 'bod', label: 'BOD', value: 2.8, unit: 'mg/L' },
  { key: 'cod', label: 'COD', value: 12, unit: 'mg/L' },
  { key: 'tds', label: 'TDS', value: 310, unit: 'mg/L' },
  { key: 'turbidity', label: 'Turbidity', value: 6.2, unit: 'NTU' },
  { key: 'temperature', label: 'Temperature', value: 26.5, unit: '°C' },
  { key: 'nitrate', label: 'Nitrate', value: 4.1, unit: 'mg/L' },
  { key: 'phosphate', label: 'Phosphate', value: 0.3, unit: 'mg/L' },
]

export const months = ['Jan', 'Mar', 'May', 'Jul', 'Sep']
export const history = {
  wqi: [71, 75, 78, 76, 82.6],
  ph: [7.2, 7.3, 7.5, 7.4, 7.4],
  do: [6.2, 6.5, 6.8, 6.6, 7.1],
  bod: [3.9, 3.5, 3.1, 3.3, 2.8],
  cod: [18, 16, 14, 15, 12],
  tds: [360, 340, 330, 335, 310],
  turbidity: [4.1, 4.5, 4.8, 5.0, 6.2],
  temperature: [22, 25, 29, 28, 26.5],
}

export const featureImportance = [
  { name: 'DO', value: 32 },
  { name: 'BOD', value: 27 },
  { name: 'Turbidity', value: 21 },
  { name: 'pH', value: 10 },
  { name: 'TDS', value: 10 },
]

export const previousVsCurrent = [
  { label: 'WQI', previous: 76, current: 82.6 },
  { label: 'DO (mg/L)', previous: 6.6, current: 7.1 },
  { label: 'BOD (mg/L)', previous: 3.3, current: 2.8 },
  { label: 'Turbidity (NTU)', previous: 5.0, current: 6.2 },
]

export const testingHistory = [
  { date: '23 Sep 2026', sampleId: 'KR-SGL-0923', wqi: 82.6, category: 'Good', status: 'Verified' },
  { date: '15 Jul 2026', sampleId: 'KR-SGL-0715', wqi: 76, category: 'Good', status: 'Verified' },
  { date: '12 May 2026', sampleId: 'KR-SGL-0512', wqi: 78, category: 'Good', status: 'Verified' },
  { date: '09 Mar 2026', sampleId: 'KR-SGL-0309', wqi: 75, category: 'Good', status: 'Verified' },
  { date: '10 Jan 2026', sampleId: 'KR-SGL-0110', wqi: 71, category: 'Moderate', status: 'Flagged' },
]

export const recentDashboardTests = [
  { sampleId: 'AQ-1024', location: 'Sangli', date: '23 Sep', wqi: 82.6, category: 'GOOD', dataQuality: 'Good', status: 'Confirmed' },
  { sampleId: 'AQ-1023', location: 'Miraj', date: '21 Sep', wqi: 68.4, category: 'MODERATE', dataQuality: 'Requires Review', status: 'Confirmed' },
  { sampleId: 'AQ-1022', location: 'Kolhapur', date: '19 Sep', wqi: 54.0, category: 'POOR', dataQuality: 'Good', status: 'Confirmed' },
  { sampleId: 'AQ-1021', location: 'Pune', date: '18 Sep', wqi: 35.8, category: 'VERY POOR', dataQuality: 'Good', status: 'Confirmed' },
]

