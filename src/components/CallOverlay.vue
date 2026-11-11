<script setup>
import { computed, ref, watch } from 'vue'
import { useCallStore } from '@/stores/call'

const call = useCallStore()
const remoteVideo = ref(null)
const remoteAudio = ref(null)
const localVideo = ref(null)

const isVideo = computed(() => call.kind === 'video')
const showRemoteVideo = computed(() =>
  isVideo.value && call.phase === 'active' && call.remoteStream?.getVideoTracks().length > 0)
const ringing = computed(() => ['outgoing', 'incoming', 'connecting'].includes(call.phase))

// Attach streams to the elements whenever either changes.
watch([() => call.remoteStream, remoteVideo, remoteAudio], ([stream, video, audio]) => {
  if (video && video.srcObject !== stream) video.srcObject = stream || null
  if (audio && audio.srcObject !== stream) audio.srcObject = stream || null
}, { flush: 'post' })
watch([() => call.localStream, localVideo], ([stream, video]) => {
  if (video && video.srcObject !== stream) video.srcObject = stream || null
}, { flush: 'post' })
</script>

<template>
  <Teleport to="body">
    <Transition name="call-pop">
      <div v-if="call.phase !== 'idle'" class="call-screen" :class="{ 'has-video': showRemoteVideo }"
           role="dialog" aria-modal="true" :aria-label="call.statusText">
        <!-- Remote picture (video calls) -->
        <video v-show="showRemoteVideo" ref="remoteVideo" class="remote-video" autoplay playsinline></video>
        <!-- Remote sound (voice calls; a video call plays sound through the video element) -->
        <audio v-if="!isVideo" ref="remoteAudio" autoplay></audio>

        <!-- Who and status -->
        <div class="call-head" :class="{ compact: showRemoteVideo }">
          <div class="avatar-wrap" :class="{ ringing }">
            <span class="ring r1"></span><span class="ring r2"></span>
            <img :src="call.peer?.avatar" alt="" class="call-avatar" />
          </div>
          <h2 class="call-name">{{ call.peer?.name }}</h2>
          <p class="call-status">
            <span v-if="call.phase === 'active'" class="live-dot"></span>{{ call.statusText }}
          </p>
        </div>

        <!-- Own camera, small in the corner -->
        <video v-if="isVideo && call.localStream && call.phase !== 'ended'" ref="localVideo"
               class="local-video" :class="{ off: call.cameraOff }" autoplay playsinline muted></video>

        <!-- Controls -->
        <div class="call-controls">
          <template v-if="call.phase === 'incoming'">
            <button class="ctl decline" aria-label="Decline" @click="call.decline()">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor"><path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08a.956.956 0 0 1 0-1.36C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.72c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28a11.27 11.27 0 0 0-2.67-1.85.996.996 0 0 1-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/></svg>
            </button>
            <button class="ctl accept" aria-label="Accept" @click="call.accept()">
              <svg v-if="isVideo" viewBox="0 0 24 24" width="28" height="28" fill="currentColor"><path d="M17 10.5V7a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3.5l4 4v-11l-4 4z"/></svg>
              <svg v-else viewBox="0 0 24 24" width="28" height="28" fill="currentColor"><path d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1.02l-2.2 2.2z"/></svg>
            </button>
          </template>
          <template v-else-if="call.phase !== 'ended'">
            <button class="ctl" :class="{ on: call.muted }" :aria-pressed="call.muted" aria-label="Mute"
                    @click="call.toggleMute()">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/>
                <line v-if="call.muted" x1="3" y1="3" x2="21" y2="21"/>
              </svg>
            </button>
            <button v-if="isVideo" class="ctl" :class="{ on: call.cameraOff }" :aria-pressed="call.cameraOff"
                    aria-label="Camera" @click="call.toggleCamera()">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2"/>
                <line v-if="call.cameraOff" x1="2" y1="2" x2="22" y2="22"/>
              </svg>
            </button>
            <button class="ctl decline" aria-label="End call" @click="call.hangUp()">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor"><path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08a.956.956 0 0 1 0-1.36C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.72c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28a11.27 11.27 0 0 0-2.67-1.85.996.996 0 0 1-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/></svg>
            </button>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.call-screen {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: max(3.5rem, env(safe-area-inset-top)) 1.5rem max(2.5rem, env(safe-area-inset-bottom));
  color: #fff;
  background:
    radial-gradient(circle at 50% 30%, rgb(124 58 237 / 0.55), transparent 60%),
    linear-gradient(160deg, #1e1b4b 0%, #0f172a 60%, #11131c 100%);
  overflow: hidden;
}
.call-screen.has-video { background: #000; }

.remote-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.call-head {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  margin-top: 6vh;
  text-align: center;
  transition: transform 0.4s ease;
}
.call-head.compact {
  margin-top: 0;
  align-self: flex-start;
  flex-direction: row;
  gap: 0.75rem;
  padding: 0.5rem 0.9rem 0.5rem 0.5rem;
  border-radius: 999px;
  background: rgb(0 0 0 / 0.35);
  backdrop-filter: blur(8px);
}
.call-head.compact .call-avatar { width: 40px; height: 40px; border-width: 2px; }
.call-head.compact .call-name { font-size: 1rem; }
.call-head.compact .ring { display: none; }

.avatar-wrap { position: relative; display: grid; place-items: center; }
.call-avatar {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid rgb(255 255 255 / 0.85);
  background: #312e81;
}
.ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid rgb(196 181 253 / 0.7);
  opacity: 0;
}
.ringing .ring { animation: ripple 2s ease-out infinite; }
.ringing .r2 { animation-delay: 1s; }
@keyframes ripple {
  from { transform: scale(1); opacity: 0.8; }
  to { transform: scale(1.9); opacity: 0; }
}

.call-name { margin: 0.4rem 0 0; font-size: 1.6rem; font-weight: 700; color: #fff; }
.call-status { margin: 0; font-size: 1rem; color: rgb(255 255 255 / 0.8); font-variant-numeric: tabular-nums; }
.compact .call-status { font-size: 0.85rem; }
.live-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 0.4rem;
  border-radius: 50%;
  background: #22c55e;
  vertical-align: middle;
  animation: blink 1.4s ease-in-out infinite;
}
@keyframes blink { 50% { opacity: 0.35; } }

.local-video {
  position: absolute;
  top: max(1rem, env(safe-area-inset-top));
  right: 1rem;
  width: min(30vw, 180px);
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 16px;
  border: 2px solid rgb(255 255 255 / 0.6);
  box-shadow: 0 10px 30px rgb(0 0 0 / 0.45);
  transform: scaleX(-1); /* mirror, like a selfie */
  background: #000;
  z-index: 2;
}
.local-video.off { opacity: 0.25; }

.call-controls {
  position: relative;
  z-index: 2;
  display: flex;
  gap: 1.5rem;
  align-items: center;
}
.ctl {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  border: none;
  display: grid;
  place-items: center;
  color: #fff;
  background: rgb(255 255 255 / 0.18);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: transform 0.15s ease, background 0.2s ease;
}
.ctl:hover { background: rgb(255 255 255 / 0.28); }
.ctl.on { background: #fff; color: #1e1b4b; }
.ctl.decline { background: #ef4444; width: 68px; height: 68px; }
.ctl.decline:hover { background: #dc2626; }
.ctl.accept { background: #22c55e; width: 68px; height: 68px; animation: nudge 1.2s ease-in-out infinite; }
.ctl.accept:hover { background: #16a34a; }
@keyframes nudge {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.call-pop-enter-active, .call-pop-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.call-pop-enter-from, .call-pop-leave-to { opacity: 0; transform: scale(1.04); }

@media (prefers-reduced-motion: reduce) {
  .ringing .ring, .ctl.accept, .live-dot { animation: none; }
}
</style>
