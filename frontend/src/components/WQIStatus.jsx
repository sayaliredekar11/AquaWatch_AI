import { CATEGORIES } from '../data/mockData'

export default function WQIStatus({ category }) {
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${CATEGORIES[category]?.bg}`}>{category}</span>
}
