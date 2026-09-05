import React from 'react'

const LINK_REGEX = /\[([^\]]+)\]\(([^)]+)\)/g

export function renderLinks(text) {
  if (!text) return ''
  const parts = []
  let lastIndex = 0
  let match
  while ((match = LINK_REGEX.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    parts.push(
      React.createElement('a', {
        key: match.index,
        href: match[2],
        target: '_blank',
        rel: 'noopener noreferrer',
        className: 'text-emerald-600 dark:text-emerald-400 underline hover:text-emerald-700',
        children: match[1],
      })
    )
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }
  return parts.length ? parts : text
}

export default function FormattedOutput({ text, className = '' }) {
  const rendered = renderLinks(text)
  if (typeof rendered === 'string') {
    return <pre className={`whitespace-pre-wrap font-mono text-sm ${className}`}>{rendered}</pre>
  }
  return (
    <div className={`whitespace-pre-wrap font-mono text-sm ${className}`}>
      {rendered}
    </div>
  )
}