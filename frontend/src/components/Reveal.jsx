import { useState, useEffect, useRef } from 'react'

/**
 * Reusable Reveal component that smoothly transitions elements into view
 * as they enter the browser viewport using standard IntersectionObserver.
 *
 * Fully respects `prefers-reduced-motion: reduce`.
 */
export default function Reveal({
  children,
  delay = 0,
  direction = 'up',
  className = '',
  as: Component = 'div',
  threshold = 0.1,
  rootMargin = '0px 0px -40px 0px',
}) {
  const [isVisible, setIsVisible] = useState(false)
  const domRef = useRef(null)

  useEffect(() => {
    // If user prefers reduced motion, show immediately without animation
    if (
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      setIsVisible(true)
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          if (domRef.current) {
            observer.unobserve(domRef.current)
          }
        }
      },
      { threshold, rootMargin }
    )

    const currentElem = domRef.current
    if (currentElem) {
      observer.observe(currentElem)
    }

    return () => {
      if (currentElem) {
        observer.unobserve(currentElem)
      }
    }
  }, [threshold, rootMargin])

  // Get initial transform offset based on direction
  const getInitialTransform = () => {
    switch (direction) {
      case 'up':
        return 'translate-y-6'
      case 'down':
        return '-translate-y-6'
      case 'left':
        return 'translate-x-6'
      case 'right':
        return '-translate-x-6'
      case 'none':
      default:
        return 'translate-y-0'
    }
  }

  const transformClass = isVisible ? 'opacity-100 translate-y-0 translate-x-0' : `opacity-0 ${getInitialTransform()}`

  return (
    <Component
      ref={domRef}
      style={{ transitionDelay: `${delay}ms` }}
      className={`transition-all duration-700 cubic-bezier(0.16, 1, 0.3, 1) ${transformClass} ${className}`}
    >
      {children}
    </Component>
  )
}
