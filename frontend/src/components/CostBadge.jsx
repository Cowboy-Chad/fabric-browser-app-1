export function parseMeta(result) {
  if (!result?.metadata_json) return {}
  try {
    return JSON.parse(result.metadata_json)
  } catch {
    return {}
  }
}

export function formatCost(cost) {
  if (cost == null) return null
  if (cost === 0) return 'Free'
  if (cost < 0.001) return '< $0.001'
  return `$${cost.toFixed(4)}`
}

const tooltipStyle = {
  visibility: 'hidden',
  opacity: 0,
  transition: 'opacity 0.15s',
  position: 'absolute',
  bottom: 'calc(100% + 8px)',
  left: '50%',
  transform: 'translateX(-50%)',
  background: '#1f2937',
  color: '#f3f4f6',
  padding: '12px 16px',
  borderRadius: '8px',
  fontSize: '15px',
  lineHeight: 1.6,
  whiteSpace: 'nowrap',
  zIndex: 50,
  boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
  pointerEvents: 'none',
}

export function CostBadge({ result }) {
  const meta = parseMeta(result)
  const cost = meta.cost_estimate
  const formatted = formatCost(cost)
  if (!formatted) return null

  const isFree = formatted === 'Free'

  const tooltipLines = []
  if (meta.model) tooltipLines.push(`Model: ${meta.model}`)
  if (meta.input_tokens != null && meta.output_tokens != null) {
    tooltipLines.push(`Tokens: ${meta.input_tokens} in / ${meta.output_tokens} out`)
  }
  if (meta.cost_estimate > 0) {
    tooltipLines.push(`Input: $${(meta.cost_input || 0).toFixed(6)}`)
    tooltipLines.push(`Output: $${(meta.cost_output || 0).toFixed(6)}`)
    tooltipLines.push(`Total: ${formatted}`)
  }

  const showTooltip = tooltipLines.length > 0

  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      <span
        className={`text-xs font-medium px-3 py-1.5 rounded-full cursor-default ${isFree ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'}`}
        onMouseEnter={(e) => { if (showTooltip) e.currentTarget.parentElement.querySelector('.cost-tooltip').style.visibility = 'visible'; e.currentTarget.parentElement.querySelector('.cost-tooltip').style.opacity = 1 }}
        onMouseLeave={(e) => { e.currentTarget.parentElement.querySelector('.cost-tooltip').style.visibility = 'hidden'; e.currentTarget.parentElement.querySelector('.cost-tooltip').style.opacity = 0 }}
      >
        {formatted}
      </span>
      {showTooltip && (
        <div className="cost-tooltip" style={tooltipStyle}>
          {tooltipLines.map((line, i) => <div key={i}>{line}</div>)}
        </div>
      )}
    </span>
  )
}