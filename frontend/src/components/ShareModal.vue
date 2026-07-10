<template>
  <div v-if="show" class="share-overlay" @click.self="close">
    <div class="share-modal">
      <div class="share-close" @click="close">✕</div>

      <!-- 分享卡片 -->
      <div ref="cardRef" class="share-card" :class="'sport-'+data.predictionType">
        <!-- 顶部品牌条 -->
        <div class="sc-top-bar"></div>

        <!-- 头部 -->
        <div class="sc-header">
          <img class="sc-logo" src="/logo.png" alt="AI竞界" crossorigin="anonymous" />
          <div class="sc-brand">
            <span class="sc-brand-name">AI竞界</span>
            <span class="sc-brand-sub">专业赛事智能分析</span>
          </div>
          <span class="sc-sport-pill">{{ sportLabel }}</span>
        </div>

        <!-- 主体：对阵 -->
        <div class="sc-body">
          <div class="sc-versus">
            <div class="sc-team-col">
              <span class="sc-team-name">{{ data.homeTeam || '--' }}</span>
              <span class="sc-team-label">主队</span>
            </div>
            <div class="sc-vs-col">
              <span class="sc-vs">VS</span>
            </div>
            <div class="sc-team-col">
              <span class="sc-team-name">{{ data.awayTeam || '--' }}</span>
              <span class="sc-team-label">客队</span>
            </div>
          </div>

          <!-- AI 预测 -->
          <div v-if="data.prediction" class="sc-pred-row">
            <span class="sc-pred-label">AI 预测</span>
            <span class="sc-pred-value">{{ data.prediction }}</span>
          </div>

          <!-- 结果章 -->
          <div v-if="data.resultLabel" class="sc-stamp-row">
            <span class="sc-stamp" :class="'sc-'+data.resultStatus">{{ data.resultLabel }}</span>
            <span v-if="data.date" class="sc-date">{{ data.date }}</span>
          </div>
          <div v-else-if="data.date" class="sc-date-only">{{ data.date }}</div>
        </div>

        <!-- 底部：二维码 -->
        <div class="sc-footer">
          <div class="sc-qr-card">
            <img class="sc-qr-img" src="/img/erweima.jpg" alt="扫码查看" crossorigin="anonymous" />
          </div>
          <div class="sc-footer-right">
            <span class="sc-footer-title">扫码查看更多AI预测</span>
            <span class="sc-footer-url">sportlens.online</span>
          </div>
        </div>
      </div>

      <!-- 操作 -->
      <div class="share-actions">
        <button class="sa-btn sa-save" :disabled="saving" @click="saveImage">
          {{ saving ? '生成中...' : '保存图片' }}
        </button>
        <button class="sa-btn sa-copy" @click="copyLink">复制链接</button>
      </div>
      <p v-if="saveMsg" class="share-msg">{{ saveMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  show: Boolean,
  data: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['close'])

const cardRef = ref(null)
const saving = ref(false)
const saveMsg = ref('')

const sportLabel = computed(() => props.data.predictionType === 'football' ? '足球' : '篮球')

function close() { saveMsg.value = ''; emit('close') }

function loadImg(src) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
}

async function saveImage() {
  saving.value = true; saveMsg.value = ''
  try {
    const el = cardRef.value
    const r = el.getBoundingClientRect()
    const W = 750 // 固定输出宽度，保证高清
    const s = W / r.width
    const H = r.height * s

    const canvas = document.createElement('canvas')
    canvas.width = W; canvas.height = H
    const ctx = canvas.getContext('2d')
    ctx.scale(s, s)

    // 背景
    ctx.fillStyle = '#FFFFFF'
    roundR(ctx, 0, 0, r.width, r.height, 16)
    ctx.fill()

    // 顶部渐变条
    const g1 = ctx.createLinearGradient(0, 0, r.width, 0)
    g1.addColorStop(0, '#6366F1'); g1.addColorStop(1, '#8B5CF6')
    ctx.fillStyle = g1
    ctx.fillRect(0, 0, r.width, 5)

    // Logo + 品牌
    try {
      const logo = await loadImg('/logo.png')
      ctx.save()
      ctx.beginPath(); ctx.arc(30, 42, 18, 0, Math.PI * 2); ctx.clip()
      ctx.drawImage(logo, 12, 24, 36, 36)
      ctx.restore()
    } catch {}
    ctx.fillStyle = '#0F172A'; ctx.font = 'bold 17px -apple-system,PingFang SC,sans-serif'
    ctx.fillText('AI竞界', 54, 38)
    ctx.fillStyle = '#94A3B8'; ctx.font = '12px -apple-system,PingFang SC,sans-serif'
    ctx.fillText('专业赛事智能分析', 54, 54)

    // 运动标签（右上角）
    const isFoot = props.data.predictionType !== 'basketball'
    const pillW = 44; const pillX = r.width - pillW - 26
    ctx.fillStyle = isFoot ? '#E0F7FA' : '#FFF3E0'
    roundR(ctx, pillX, 26, pillW, 24, 12)
    ctx.fill()
    ctx.fillStyle = isFoot ? '#0288D1' : '#E65100'
    ctx.font = 'bold 12px -apple-system,PingFang SC,sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(sportLabel.value, pillX + pillW / 2, 42)
    ctx.textAlign = 'start'

    // 分隔线
    ctx.strokeStyle = '#E2E8F0'; ctx.lineWidth = 0.5
    ctx.beginPath(); ctx.moveTo(20, 68); ctx.lineTo(r.width - 20, 68); ctx.stroke()

    // 对阵 — 中央大字
    const vsY = 128
    ctx.textAlign = 'center'
    ctx.fillStyle = '#0F172A'; ctx.font = 'bold 26px -apple-system,PingFang SC,sans-serif'
    ctx.fillText(props.data.homeTeam || '--', r.width / 2 - 84, vsY)
    ctx.fillStyle = '#94A3B8'; ctx.font = 'bold 14px -apple-system,PingFang SC,sans-serif'
    ctx.fillText('VS', r.width / 2, vsY)
    ctx.fillStyle = '#0F172A'; ctx.font = 'bold 26px -apple-system,PingFang SC,sans-serif'
    ctx.fillText(props.data.awayTeam || '--', r.width / 2 + 84, vsY)

    // 主客标签
    ctx.fillStyle = '#94A3B8'; ctx.font = '11px -apple-system,PingFang SC,sans-serif'
    ctx.fillText('主队', r.width / 2 - 84, vsY + 20)
    ctx.fillText('客队', r.width / 2 + 84, vsY + 20)
    ctx.textAlign = 'start'

    // AI 预测
    let cy = vsY + 48
    if (props.data.prediction) {
      ctx.textAlign = 'center'
      ctx.fillStyle = '#64748B'; ctx.font = '12px -apple-system,PingFang SC,sans-serif'
      ctx.fillText('AI 预测', r.width / 2, cy)
      cy += 22
      ctx.fillStyle = '#B45309'; ctx.font = 'bold 16px -apple-system,PingFang SC,sans-serif'
      const pw = ctx.measureText(props.data.prediction).width
      ctx.fillStyle = '#FFFBEB'
      roundR(ctx, (r.width - pw - 32) / 2, cy - 14, pw + 32, 34, 8)
      ctx.fill()
      ctx.strokeStyle = '#FDE68A'; ctx.lineWidth = 1
      roundR(ctx, (r.width - pw - 32) / 2, cy - 14, pw + 32, 34, 8)
      ctx.stroke()
      ctx.fillStyle = '#B45309'
      ctx.fillText(props.data.prediction, r.width / 2, cy + 8)
      ctx.textAlign = 'start'
      cy += 40
    }

    // 结果章
    if (props.data.resultLabel) {
      ctx.textAlign = 'center'
      const st = props.data.resultStatus
      const g2 = ctx.createLinearGradient(0, cy - 12, 0, cy + 20)
      if (st === 'hit') { g2.addColorStop(0, '#10B981'); g2.addColorStop(1, '#059669') }
      else if (st === 'push') { g2.addColorStop(0, '#8B5CF6'); g2.addColorStop(1, '#7C3AED') }
      else { g2.addColorStop(0, '#94A3B8'); g2.addColorStop(1, '#64748B') }
      ctx.fillStyle = g2
      const lw = ctx.measureText(props.data.resultLabel).width
      roundR(ctx, (r.width - lw - 40) / 2, cy - 12, lw + 40, 32, 16)
      ctx.fill()
      // 虚线内框
      ctx.strokeStyle = 'rgba(255,255,255,0.3)'; ctx.lineWidth = 1.5
      ctx.setLineDash([3, 2])
      roundR(ctx, (r.width - lw - 40) / 2 + 4, cy - 8, lw + 32, 24, 12)
      ctx.stroke()
      ctx.setLineDash([])
      ctx.fillStyle = '#fff'; ctx.font = 'bold 15px -apple-system,PingFang SC,sans-serif'
      ctx.fillText(props.data.resultLabel, r.width / 2, cy + 10)
      ctx.textAlign = 'start'
      cy += 38
    }

    // 日期
    if (props.data.date) {
      ctx.textAlign = 'center'
      ctx.fillStyle = '#94A3B8'; ctx.font = '12px -apple-system,PingFang SC,sans-serif'
      ctx.fillText(props.data.date, r.width / 2, cy + 6)
      ctx.textAlign = 'start'
      cy += 28
    }

    // 底部分隔 — 固定位置，保证不同内容卡片高度一致
    const footY = r.height - 90
    ctx.strokeStyle = '#E2E8F0'; ctx.lineWidth = 0.5
    ctx.setLineDash([])
    ctx.beginPath(); ctx.moveTo(20, footY); ctx.lineTo(r.width - 20, footY); ctx.stroke()

    // 二维码卡片
    const qrSize = 64; const qrX = 20; const qrY = footY + 14
    ctx.fillStyle = '#F8FAFC'
    roundR(ctx, qrX - 4, qrY - 4, qrSize + 8, qrSize + 8, 10)
    ctx.fill()
    ctx.strokeStyle = '#E2E8F0'; ctx.lineWidth = 1
    roundR(ctx, qrX - 4, qrY - 4, qrSize + 8, qrSize + 8, 10)
    ctx.stroke()
    try {
      const qr = await loadImg('/img/erweima.jpg')
      ctx.drawImage(qr, qrX, qrY, qrSize, qrSize)
    } catch {}

    ctx.fillStyle = '#0F172A'; ctx.font = 'bold 15px -apple-system,PingFang SC,sans-serif'
    ctx.fillText('扫码查看更多AI预测', qrX + qrSize + 14, qrY + 28)
    ctx.fillStyle = '#94A3B8'; ctx.font = '12px -apple-system,PingFang SC,sans-serif'
    ctx.fillText('sportlens.online', qrX + qrSize + 14, qrY + 48)

    // 导出
    canvas.toBlob(blob => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'AI竞界-战绩分享.png'; a.click()
      URL.revokeObjectURL(url)
      saveMsg.value = '图片已保存'
    }, 'image/png')
  } catch (e) {
    saveMsg.value = '生成失败，请截图分享'
  } finally {
    saving.value = false
  }
}

function roundR(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y)
  ctx.arcTo(x + w, y, x + w, y + r, r)
  ctx.lineTo(x + w, y + h - r); ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
  ctx.lineTo(x + r, y + h); ctx.arcTo(x, y + h, x, y + h - r, r)
  ctx.lineTo(x, y + r); ctx.arcTo(x, y, x + r, y, r)
  ctx.closePath()
}

function copyLink() {
  const url = window.location.origin
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(url).then(() => { saveMsg.value = '链接已复制' })
  } else {
    const ta = document.createElement('textarea')
    ta.value = url; ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta); ta.select()
    try { document.execCommand('copy'); saveMsg.value = '链接已复制' } catch { saveMsg.value = url }
    document.body.removeChild(ta)
  }
}
</script>

<style scoped>
.share-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(15,23,42,0.55); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.share-modal {
  background: #fff; border-radius: 20px; padding: 20px 20px 18px;
  max-width: 380px; width: 100%; box-shadow: 0 24px 64px rgba(0,0,0,0.25);
  position: relative; animation: sp-pop 0.3s cubic-bezier(0.22,0.61,0.36,1);
}
@keyframes sp-pop {
  from { opacity: 0; transform: translateY(24px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.share-close {
  position: absolute; top: 10px; right: 12px; z-index: 3;
  width: 30px; height: 30px; border-radius: 50%;
  background: rgba(0,0,0,0.06); display: flex; align-items: center;
  justify-content: center; font-size: 15px; color: #94A3B8; cursor: pointer;
}

/* ===== 卡片 ===== */
.share-card {
  background: #fff; border-radius: 16px; overflow: hidden;
  border: 1px solid #E8ECF2; position: relative; user-select: none;
}

.sc-top-bar {
  height: 5px; background: linear-gradient(90deg, #6366F1, #8B5CF6);
}

.sc-header {
  display: flex; align-items: center; gap: 10px;
  padding: 18px 20px 10px;
}
.sc-logo { width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0; }
.sc-brand { flex: 1; min-width: 0; }
.sc-brand-name { font-size: 16px; font-weight: 800; color: #0F172A; display: block; }
.sc-brand-sub { font-size: 11px; color: #94A3B8; }
.sc-sport-pill {
  flex-shrink: 0; padding: 4px 14px; border-radius: 12px;
  font-size: 12px; font-weight: 700;
}
.sport-football .sc-sport-pill { background: #E0F7FA; color: #0288D1; }
.sport-basketball .sc-sport-pill { background: #FFF3E0; color: #E65100; }

/* 主体 */
.sc-body {
  display: flex; flex-direction: column; align-items: center;
  padding: 16px 24px 10px; border-top: 1px solid #F1F5F9; gap: 8px;
  min-height: 148px; justify-content: center;
}

.sc-versus { display: flex; align-items: center; gap: 0; width: 100%; }
.sc-team-col {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.sc-team-name { font-size: 22px; font-weight: 800; color: #0F172A; line-height: 1.3; }
.sc-team-label { font-size: 11px; color: #94A3B8; }
.sc-vs-col {
  width: 48px; display: flex; align-items: center; justify-content: center;
}
.sc-vs {
  font-size: 14px; font-weight: 800; color: #CBD5E1;
  background: #F8FAFC; padding: 4px 10px; border-radius: 8px;
}

.sc-pred-row {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  margin-top: 8px;
}
.sc-pred-label { font-size: 11px; color: #94A3B8; }
.sc-pred-value {
  font-size: 15px; font-weight: 700; color: #B45309;
  background: #FFFBEB; border: 1px solid #FDE68A;
  padding: 5px 20px; border-radius: 8px;
}

.sc-stamp-row { display: flex; align-items: center; gap: 14px; margin-top: 4px; }
.sc-stamp {
  padding: 6px 20px; border-radius: 20px; font-size: 15px; font-weight: 800;
  color: #fff; position: relative;
}
.sc-stamp::after {
  content: ''; position: absolute; inset: 3px; border-radius: 18px;
  border: 1.5px dashed rgba(255,255,255,0.3); pointer-events: none;
}
.sc-hit { background: linear-gradient(135deg,#10B981,#059669); box-shadow: 0 3px 12px rgba(5,150,105,0.3); }
.sc-push { background: linear-gradient(135deg,#8B5CF6,#7C3AED); box-shadow: 0 3px 12px rgba(124,58,237,0.3); }
.sc-miss { background: #E2E8F0; color: #94A3B8; box-shadow: none; }
.sc-miss::after { border-color: rgba(0,0,0,0.08); }
.sc-date { font-size: 13px; color: #94A3B8; }
.sc-date-only { font-size: 13px; color: #94A3B8; margin-top: 4px; }

/* 底部 */
.sc-footer {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 20px 18px; border-top: 1px solid #F1F5F9;
}
.sc-qr-card {
  flex-shrink: 0; padding: 5px; background: #F8FAFC;
  border: 1px solid #E2E8F0; border-radius: 10px;
}
.sc-qr-img { width: 64px; height: 64px; display: block; border-radius: 6px; }
.sc-footer-right { display: flex; flex-direction: column; gap: 2px; }
.sc-footer-title { font-size: 15px; font-weight: 700; color: #0F172A; }
.sc-footer-url { font-size: 12px; color: #94A3B8; }

/* 操作 */
.share-actions { display: flex; gap: 10px; margin-top: 16px; }
.sa-btn {
  flex: 1; height: 46px; border-radius: 12px; font-size: 15px; font-weight: 700;
  border: none; cursor: pointer; transition: all 0.15s;
}
.sa-btn:active { transform: scale(0.97); }
.sa-save { background: linear-gradient(135deg,#6366F1,#7C3AED); color: #fff; box-shadow: 0 4px 16px rgba(99,102,241,0.3); }
.sa-save:disabled { opacity: 0.5; }
.sa-copy { background: #F1F5F9; color: #475569; }
.share-msg { text-align: center; margin-top: 10px; font-size: 13px; color: #10B981; font-weight: 600; }

@media (max-width: 767px) {
  .share-modal { padding: 16px 14px; border-radius: 16px; max-width: 340px; }
  .sc-team-name { font-size: 20px; }
}
</style>
