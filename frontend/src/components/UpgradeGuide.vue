<template>
  <div>
    <!-- 开通会员 浮动按钮 -->
    <button v-if="showFab" class="upgrade-fab" @click="open">
      <svg class="upgrade-fab-icon" viewBox="0 0 24 24" fill="none">
        <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" stroke-width="1.8"/>
        <path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <span>开通会员</span>
    </button>

    <!-- 二维码升级弹窗 -->
    <Transition name="upgrade-fade">
      <div v-if="showModal" class="upgrade-overlay" @click.self="close">
        <div class="upgrade-modal">
          <button class="upgrade-close" @click="close" aria-label="关闭">
            <svg viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          </button>
          <div class="upgrade-head">
            <span class="upgrade-head-eyebrow">AI 竞界 · 付费会员</span>
            <h3 class="upgrade-head-title">开通会员，解锁全部 AI 分析</h3>
          </div>
          <div class="upgrade-qr-wrap">
            <img class="upgrade-qr" src="/img/erweima.jpg" alt="扫码开通会员" />
            <div class="upgrade-qr-glow"></div>
          </div>
          <p class="upgrade-scan-tip">微信扫码 · 添加开通付费会员</p>
          <ul class="upgrade-benefits">
            <li><span class="ub-check">✓</span>解锁全部单场 AI 预测</li>
            <li><span class="ub-check">✓</span>置信度完整数据</li>
            <li><span class="ub-check">✓</span>解锁全部重心/精选核心/会员专属场次</li>
          </ul>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  // 是否显示右下角浮动按钮（一般非会员显示）
  showFab: { type: Boolean, default: false }
})

const showModal = ref(false)
function open() { showModal.value = true }
function close() { showModal.value = false }

// 供父组件调用（卡片锁态点击、查看更多、自动弹窗等）
defineExpose({ open, close })
</script>

<style scoped>
/* ===== 开通会员 浮动按钮 ===== */
.upgrade-fab {
  position: fixed;
  right: 20px;
  bottom: calc(56px + env(safe-area-inset-bottom, 0px) + 16px);
  z-index: 200;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #6366F1, #7C3AED);
  color: #fff; font-size: 14px; font-weight: 700;
  border-radius: 28px; border: none; cursor: pointer;
  box-shadow: 0 6px 20px rgba(99,102,241,0.35);
  animation: fab-in 0.4s ease-out 0.6s both;
}
.upgrade-fab:hover { box-shadow: 0 8px 28px rgba(99,102,241,0.45); transform: translateY(-1px); }
.upgrade-fab:active { transform: translateY(0); }
.upgrade-fab-icon { width: 18px; height: 18px; }
@media (min-width: 768px) {
  .upgrade-fab { bottom: 32px; right: 32px; }
}
@keyframes fab-in {
  from { opacity: 0; transform: translateY(20px) scale(0.9); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ===== 二维码升级弹窗 ===== */
.upgrade-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(15,23,42,0.55);
  backdrop-filter: blur(3px);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.upgrade-modal {
  position: relative;
  width: 100%; max-width: 340px;
  background: #fff;
  border-radius: 22px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(15,23,42,0.25);
  animation: modal-pop 0.42s cubic-bezier(0.22,0.61,0.36,1) both;
}
@keyframes modal-pop {
  from { opacity: 0; transform: translateY(24px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.upgrade-close {
  position: absolute; top: 12px; right: 12px; z-index: 2;
  width: 30px; height: 30px; padding: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.2); border: none; border-radius: 50%;
  color: #fff; cursor: pointer; transition: background 0.15s;
}
.upgrade-close:hover { background: rgba(255,255,255,0.35); }
.upgrade-close svg { width: 15px; height: 15px; }

.upgrade-head {
  padding: 26px 24px 20px;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  text-align: center;
}
.upgrade-head-eyebrow {
  font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
  color: rgba(255,255,255,0.75); text-transform: uppercase;
}
.upgrade-head-title {
  margin-top: 8px; font-size: 18px; font-weight: 800; color: #fff; line-height: 1.4;
}

.upgrade-qr-wrap {
  position: relative;
  width: 180px; height: 180px;
  margin: 24px auto 12px;
}
.upgrade-qr {
  position: relative; z-index: 1;
  width: 180px; height: 180px;
  border-radius: 14px;
  border: 1px solid var(--border);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  object-fit: cover; background: #fff;
}
.upgrade-qr-glow {
  position: absolute; inset: -12px;
  background: radial-gradient(circle, rgba(99,102,241,0.14), transparent 70%);
  z-index: 0;
}
.upgrade-scan-tip {
  text-align: center; font-size: 14px; font-weight: 600;
  color: var(--text); margin-bottom: 20px;
}
.upgrade-benefits {
  list-style: none; margin: 0; padding: 0 28px 28px;
  display: flex; flex-direction: column; gap: 12px;
}
.upgrade-benefits li {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: var(--text-secondary);
}
.ub-check {
  flex-shrink: 0;
  width: 20px; height: 20px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--primary-light); color: var(--primary);
  font-size: 12px; font-weight: 800;
}

.upgrade-fade-enter-active, .upgrade-fade-leave-active { transition: opacity 0.25s ease; }
.upgrade-fade-enter-from, .upgrade-fade-leave-to { opacity: 0; }
</style>
