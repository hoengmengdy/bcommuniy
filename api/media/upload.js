// Issues short-lived Vercel Blob client-upload tokens for chat photos, videos and voice messages.
// Files go straight from the browser to Blob storage, avoiding the 4.5 MB function body limit.
import { handleUpload } from '@vercel/blob/client'

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/heic', 'image/heif']
const VIDEO_TYPES = ['video/mp4', 'video/quicktime', 'video/webm', 'video/3gpp']
const AUDIO_TYPES = ['audio/webm', 'audio/ogg', 'audio/mp4', 'audio/mpeg', 'audio/aac', 'audio/x-m4a']
const MAX_AUDIO_BYTES = 10 * 1024 * 1024
const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const MAX_VIDEO_BYTES = 50 * 1024 * 1024

const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } })

export async function POST(request) {
  let body
  try {
    body = await request.json()
  } catch {
    return json({ error: { message: 'Invalid upload request.', status: 400 } }, 400)
  }
  try {
    const result = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async (pathname) => {
        // Only signed-in, active users may upload: reuse the Flask session check.
        const me = await fetch(new URL('/api/auth/me', request.url), {
          headers: { Authorization: request.headers.get('authorization') || '' },
        })
        if (!me.ok) throw new Error('Authentication required.')
        if (!/^chat\/[\w.-]{1,120}$/.test(pathname)) throw new Error('Invalid file name.')
        // Voice notes are named chat/voice-*, since .webm/.mp4 alone can't tell audio from video.
        const isAudio = pathname.startsWith('chat/voice-')
        const isVideo = !isAudio && /\.(mp4|mov|webm|3gp)$/i.test(pathname)
        return {
          allowedContentTypes: isAudio ? AUDIO_TYPES : isVideo ? VIDEO_TYPES : IMAGE_TYPES,
          maximumSizeInBytes: isAudio ? MAX_AUDIO_BYTES : isVideo ? MAX_VIDEO_BYTES : MAX_IMAGE_BYTES,
          addRandomSuffix: true,
        }
      },
    })
    return json(result)
  } catch (error) {
    const message = error?.message === 'Authentication required.' ? error.message : 'Upload was rejected.'
    return json({ error: { message, status: error?.message === 'Authentication required.' ? 401 : 400 } },
      error?.message === 'Authentication required.' ? 401 : 400)
  }
}
