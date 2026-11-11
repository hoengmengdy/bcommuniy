// Voice and video calls with WebRTC.
// Audio/video go straight between the two browsers. The Flask API only passes the
// offer to the person being called and the answer back (see backend/routes/calls.py),
// and both sides poll it, the same way chat does.
import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'
import { api } from '@/services/api'
import { useUiStore } from '@/stores/ui'
import { useSettingsStore } from '@/stores/settings'

const INCOMING_POLL_MS = 2500
const CALL_POLL_MS = 1500
const ICE_GATHER_MS = 2500

// Free public STUN servers find each side's public address. Two people behind strict
// networks (some mobile data / office Wi-Fi) also need a TURN relay: set the VITE_TURN_* env vars.
function iceServers() {
  const servers = [{ urls: ['stun:stun.l.google.com:19302', 'stun:stun1.l.google.com:19302'] }]
  const turn = import.meta.env.VITE_TURN_URL
  if (turn) {
    servers.push({
      urls: turn.split(',').map(s => s.trim()),
      username: import.meta.env.VITE_TURN_USERNAME,
      credential: import.meta.env.VITE_TURN_CREDENTIAL,
    })
  }
  return servers
}

const TEXT = {
  km: {
    calling: 'កំពុងហៅ…', incomingAudio: 'ការហៅជាសំឡេង', incomingVideo: 'ការហៅជាវីដេអូ',
    connecting: 'កំពុងភ្ជាប់…', ended: 'ការហៅបានបញ្ចប់', declined: 'មិនទទួល', missed: 'គ្មានអ្នកទទួល',
    busy: 'កំពុងជាប់ការហៅផ្សេង', failed: 'ការភ្ជាប់បរាជ័យ', noMedia: 'សូមអនុញ្ញាតឲ្យប្រើមីក្រូហ្វូន/កាមេរ៉ា',
    unsupported: 'កម្មវិធីរុករកនេះមិនគាំទ្រការហៅទេ',
  },
  en: {
    calling: 'Calling…', incomingAudio: 'Voice call', incomingVideo: 'Video call',
    connecting: 'Connecting…', ended: 'Call ended', declined: 'Call declined', missed: 'No answer',
    busy: 'On another call', failed: 'Connection failed', noMedia: 'Please allow microphone/camera access',
    unsupported: 'This browser does not support calls',
  },
}

function waitForIce(pc) {
  if (pc.iceGatheringState === 'complete') return Promise.resolve()
  return new Promise(resolve => {
    const done = () => { clearTimeout(timer); pc.removeEventListener('icegatheringstatechange', check); resolve() }
    const check = () => pc.iceGatheringState === 'complete' && done()
    // Enough candidates are usually found well before gathering formally completes.
    const timer = setTimeout(done, ICE_GATHER_MS)
    pc.addEventListener('icegatheringstatechange', check)
  })
}

export const useCallStore = defineStore('call', () => {
  const ui = useUiStore()
  const settings = useSettingsStore()
  const t = key => (TEXT[settings.lang] || TEXT.km)[key]

  // idle | outgoing | incoming | connecting | active | ended
  const phase = ref('idle')
  const call = ref(null)          // the server's call object
  const peer = ref(null)          // { name, avatar } of the other person
  const kind = ref('audio')
  const endReason = ref('')
  const localStream = shallowRef(null)
  const remoteStream = shallowRef(null)
  const muted = ref(false)
  const cameraOff = ref(false)
  const startedAt = ref(0)
  const now = ref(Date.now())

  let pc = null
  let pollTimer = null
  let dropTimer = null
  let incomingTimer = null
  let answerApplied = false
  let tone = null
  let ignoredCallId = null

  const inCall = computed(() => phase.value !== 'idle')
  const duration = computed(() => {
    if (phase.value !== 'active' || !startedAt.value) return ''
    const s = Math.max(0, Math.floor((now.value - startedAt.value) / 1000))
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
  })
  const statusText = computed(() => ({
    outgoing: t('calling'),
    incoming: kind.value === 'video' ? t('incomingVideo') : t('incomingAudio'),
    connecting: t('connecting'),
    active: duration.value,
    ended: endReason.value || t('ended'),
  }[phase.value] || ''))

  // ---------- ringing sounds ----------
  // Incoming: the spoken Khmer "មានគេហៅមក" (same voice as the chat alert) followed by a ring,
  // repeating until answered. Outgoing: a soft ringback tone. Beeps are made with Web Audio.
  const callVoice = typeof Audio !== 'undefined' ? new Audio('/audio/incoming-call-km.mp3') : null
  if (callVoice) callVoice.preload = 'auto'

  function playTone(pattern) {
    stopTone()
    const incoming = pattern === 'incoming'
    let ctx = null
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)()
      // Browsers start audio "suspended" until the page has been used; ask to wake it.
      ctx.resume?.().catch(() => {})
    } catch {
      // No Web Audio: the voice clip and the call screen still work.
    }
    const beep = () => {
      if (!ctx) return
      const gain = ctx.createGain()
      gain.gain.value = incoming ? 0.25 : 0.08
      gain.connect(ctx.destination)
      const notes = incoming ? [[880, 0], [660, 0.25], [880, 0.5], [660, 0.75]] : [[440, 0], [480, 0]]
      for (const [freq, start] of notes) {
        const osc = ctx.createOscillator()
        osc.frequency.value = freq
        osc.connect(gain)
        osc.start(ctx.currentTime + start)
        osc.stop(ctx.currentTime + start + (incoming ? 0.2 : 1.2))
      }
    }
    const ring = () => {
      if (incoming) {
        navigator.vibrate?.([400, 200, 400, 200, 400])
        if (callVoice) {
          callVoice.currentTime = 0
          callVoice.play().catch(() => {}) // blocked until the page has been tapped once
        }
        tone && (tone.beepTimer = setTimeout(beep, 2100)) // ring right after the voice
      } else {
        beep()
      }
    }
    tone = { ctx, timer: null, beepTimer: null }
    ring()
    tone.timer = setInterval(ring, 4000)
  }
  function stopTone() {
    if (!tone) return
    clearInterval(tone.timer)
    clearTimeout(tone.beepTimer)
    tone.ctx?.close().catch(() => {})
    tone = null
    callVoice?.pause()
    navigator.vibrate?.(0)
  }

  // ---------- media + peer connection ----------
  async function getMedia(video) {
    if (!navigator.mediaDevices?.getUserMedia || !window.RTCPeerConnection) throw new Error(t('unsupported'))
    try {
      return await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
        video: video ? { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } } : false,
      })
    } catch {
      throw new Error(t('noMedia'))
    }
  }

  function createPeer(stream) {
    pc = new RTCPeerConnection({ iceServers: iceServers() })
    stream.getTracks().forEach(track => pc.addTrack(track, stream))
    const remote = new MediaStream()
    remoteStream.value = remote
    pc.ontrack = event => {
      event.streams[0]?.getTracks().forEach(track => remote.getTracks().includes(track) || remote.addTrack(track))
      if (!event.streams[0] && !remote.getTracks().includes(event.track)) remote.addTrack(event.track)
      remoteStream.value = new MediaStream(remote.getTracks()) // new object so the <video> re-binds
    }
    pc.onconnectionstatechange = () => {
      if (!pc) return
      const state = pc.connectionState
      clearTimeout(dropTimer)
      if (state === 'connected' && phase.value !== 'active') {
        stopTone()
        phase.value = 'active'
        startedAt.value = Date.now()
      } else if (state === 'failed') {
        hangUp(t('failed'))
      } else if (state === 'disconnected') {
        // The other person closed the page or lost signal; give the network a moment to recover.
        dropTimer = setTimeout(() => pc?.connectionState !== 'connected' && hangUp(), 8000)
      }
    }
  }

  // ---------- polling ----------
  function startCallPolling() {
    clearInterval(pollTimer)
    pollTimer = setInterval(pollCall, CALL_POLL_MS)
  }

  async function pollCall() {
    if (!call.value) return
    try {
      const { data } = await api(`/calls/${call.value.id}`)
      if (!call.value || data.id !== call.value.id) return
      call.value = data
      if (['ended', 'declined', 'missed'].includes(data.status)) {
        finish({ ended: t('ended'), declined: t('declined'), missed: t('missed') }[data.status])
        return
      }
      if (data.status === 'active' && data.answer && !answerApplied && pc) {
        answerApplied = true
        phase.value = 'connecting'
        stopTone()
        await pc.setRemoteDescription({ type: 'answer', sdp: data.answer })
      }
    } catch {
      // A missed poll is fine; the next one retries.
    }
  }

  async function pollIncoming() {
    // Keep checking while the tab is in the background, so a call rings there too.
    if (phase.value !== 'idle') return
    try {
      const { data } = await api('/calls/incoming')
      if (!data || phase.value !== 'idle' || data.id === ignoredCallId) return
      call.value = data
      kind.value = data.kind
      peer.value = data.caller
      phase.value = 'incoming'
      playTone('incoming')
      startCallPolling() // notices if the caller hangs up before we answer
    } catch {
      // Signed out or offline.
    }
  }

  function watchIncoming() {
    clearInterval(incomingTimer)
    incomingTimer = setInterval(pollIncoming, INCOMING_POLL_MS)
    pollIncoming()
  }
  function stopWatchingIncoming() {
    clearInterval(incomingTimer)
    incomingTimer = null
  }

  // ---------- actions ----------
  async function startCall(conversation, callKind = 'audio') {
    if (phase.value !== 'idle') return
    kind.value = callKind
    peer.value = { name: conversation.name, avatar: conversation.avatar }
    phase.value = 'outgoing'
    try {
      localStream.value = await getMedia(callKind === 'video')
      createPeer(localStream.value)
      await pc.setLocalDescription(await pc.createOffer())
      await waitForIce(pc)
      if (phase.value !== 'outgoing') return cleanup() // hung up while preparing
      const { data } = await api('/calls', {
        method: 'POST',
        body: { conversationId: conversation.id, kind: callKind, offer: pc.localDescription.sdp },
      })
      call.value = data
      playTone('ringback')
      startCallPolling()
    } catch (error) {
      ui.addToast(error.status === 409 ? t('busy') : error.message, 'error')
      cleanup()
    }
  }

  async function accept() {
    if (phase.value !== 'incoming' || !call.value) return
    stopTone()
    phase.value = 'connecting'
    try {
      localStream.value = await getMedia(kind.value === 'video')
      createPeer(localStream.value)
      await pc.setRemoteDescription({ type: 'offer', sdp: call.value.offer })
      await pc.setLocalDescription(await pc.createAnswer())
      await waitForIce(pc)
      const { data } = await api(`/calls/${call.value.id}/answer`, {
        method: 'POST', body: { answer: pc.localDescription.sdp },
      })
      call.value = data
    } catch (error) {
      ui.addToast(error.message, 'error')
      await hangUp()
    }
  }

  async function decline() {
    if (!call.value) return cleanup()
    ignoredCallId = call.value.id
    const id = call.value.id
    cleanup()
    try { await api(`/calls/${id}/end`, { method: 'POST' }) } catch { /* the server times the call out anyway */ }
  }

  async function hangUp(reason) {
    const id = call.value?.id
    finish(reason || t('ended'))
    if (id) {
      try { await api(`/calls/${id}/end`, { method: 'POST' }) } catch { /* ignore */ }
    }
  }

  function toggleMute() {
    muted.value = !muted.value
    localStream.value?.getAudioTracks().forEach(track => { track.enabled = !muted.value })
  }
  function toggleCamera() {
    cameraOff.value = !cameraOff.value
    localStream.value?.getVideoTracks().forEach(track => { track.enabled = !cameraOff.value })
  }

  // Show "Call ended" briefly, then close the call screen.
  function finish(reason) {
    if (phase.value === 'idle') return
    if (call.value) ignoredCallId = call.value.id
    releaseMedia()
    endReason.value = reason
    phase.value = 'ended'
    setTimeout(() => { if (phase.value === 'ended') cleanup() }, 1600)
  }

  function releaseMedia() {
    stopTone()
    clearInterval(pollTimer)
    clearTimeout(dropTimer)
    pollTimer = null
    localStream.value?.getTracks().forEach(track => track.stop())
    if (pc) {
      pc.ontrack = pc.onconnectionstatechange = null
      pc.close()
      pc = null
    }
  }

  function cleanup() {
    releaseMedia()
    phase.value = 'idle'
    call.value = null
    peer.value = null
    localStream.value = null
    remoteStream.value = null
    muted.value = false
    cameraOff.value = false
    startedAt.value = 0
    answerApplied = false
    endReason.value = ''
  }

  setInterval(() => { if (phase.value === 'active') now.value = Date.now() }, 1000)

  return {
    phase, call, peer, kind, localStream, remoteStream, muted, cameraOff, inCall, statusText, duration,
    startCall, accept, decline, hangUp, toggleMute, toggleCamera, watchIncoming, stopWatchingIncoming,
  }
})
