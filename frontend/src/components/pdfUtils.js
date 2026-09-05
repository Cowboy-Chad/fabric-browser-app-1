import { jsPDF } from 'jspdf'

const LINK_REGEX = /\[([^\]]+)\]\(([^)]+)\)/g
const BRACKET_REGEX = /\[([^\]]+)\]/g

export function generatePdfBlob(text) {
  const doc = new jsPDF()
  doc.setFont('Courier')
  doc.setFontSize(10)
  const margin = 20
  const pageWidth = doc.internal.pageSize.getWidth() - margin * 2
  const pageHeight = doc.internal.pageSize.getHeight()
  let y = margin
  const lh = 6

  const rawLines = (text || '').split('\n')
  for (const rawLine of rawLines) {
    LINK_REGEX.lastIndex = 0
    const hasLink = LINK_REGEX.test(rawLine)
    LINK_REGEX.lastIndex = 0

    if (!hasLink) {
      const wrapped = doc.splitTextToSize(rawLine, pageWidth)
      for (const wl of wrapped) {
        if (y + lh > pageHeight - margin) { doc.addPage(); y = margin }
        doc.text(wl, margin, y)
        y += lh
      }
      continue
    }

    let display = ''
    let lastIdx = 0
    let m
    const urls = []
    while ((m = LINK_REGEX.exec(rawLine)) !== null) {
      display += rawLine.slice(lastIdx, m.index)
      const linkLabel = m[1].replace(/ /g, '\u00A0')
      display += `[${linkLabel}]`
      urls.push(m[2])
      lastIdx = m.index + m[0].length
    }
    display += rawLine.slice(lastIdx)

    const displayWrapped = doc.splitTextToSize(display, pageWidth)
    for (const dw of displayWrapped) {
      if (y + lh > pageHeight - margin) { doc.addPage(); y = margin }
      const restored = dw.replace(/\u00A0/g, ' ')
      doc.text(restored, margin, y)

      BRACKET_REGEX.lastIndex = 0
      let bm
      let ui = 0
      while ((bm = BRACKET_REGEX.exec(restored)) !== null && ui < urls.length) {
        const before = restored.slice(0, bm.index)
        const xOff = doc.getTextWidth(before)
        doc.link(margin + xOff, y - 4, doc.getTextWidth(bm[1]), 5, { url: urls[ui++] })
      }

      y += lh
    }

    for (const url of urls) {
      if (y + lh > pageHeight - margin) { doc.addPage(); y = margin }
      doc.setTextColor(0, 102, 204)
      doc.textWithLink(url, margin, y, { url })
      doc.setTextColor(0, 0, 0)
      y += lh
    }
  }

  return doc.output('blob')
}