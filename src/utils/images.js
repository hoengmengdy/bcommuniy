// Phone photos are often 3-12 MB; Vercel functions reject request bodies over 4.5 MB,
// so photos are shrunk in the browser before they are uploaded or embedded.

async function decode(file) {
  if (globalThis.createImageBitmap) {
    try { return await createImageBitmap(file, { imageOrientation: 'from-image' }) }
    catch { /* fall back to <img>, which also handles formats some bitmaps reject */ }
  }
  const url = URL.createObjectURL(file)
  try {
    const img = new Image()
    img.src = url
    await img.decode()
    return img
  } finally {
    URL.revokeObjectURL(url)
  }
}

// Returns a JPEG Blob whose longest side is at most maxSide pixels.
export async function shrinkImage(file, { maxSide = 1600, quality = 0.85 } = {}) {
  const source = await decode(file)
  const width = source.naturalWidth || source.width
  const height = source.naturalHeight || source.height
  const scale = Math.min(1, maxSide / Math.max(width, height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(width * scale))
  canvas.height = Math.max(1, Math.round(height * scale))
  const context = canvas.getContext('2d')
  // JPEG has no transparency; paint white so transparent PNGs don't turn black.
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvas.width, canvas.height)
  context.drawImage(source, 0, 0, canvas.width, canvas.height)
  source.close?.()
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality))
  if (!blob) throw new Error('Unable to read this photo. Please choose another one.')
  return blob
}

export function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error('Unable to read this photo. Please choose it again.'))
    reader.readAsDataURL(blob)
  })
}
