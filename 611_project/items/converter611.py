# items/converter611.py
import time, random
from engine.type_out import type_out

def simulate_converter_611(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)
    chambers = 6
    live_pos = rng.randrange(chambers)  # 0..5

    if show_text:
        type_out(f"🎲 轉換器611 開始（seed={seed}）", enable=anim)
        type_out("規則：A 第一回合使用轉換器 ⇒ 不敗；P(平手)=1/6，其餘 A必勝。", enable=anim)
        if show_bullets:
            type_out(f"💣 實彈位置：[{live_pos}]", enable=anim)

    # 依規則直接終局（不需要後續輪轉）
    if live_pos == 0:
        if show_text:
            type_out("🔁 第0膛遇實彈 → 轉換器處理 ⇒ 平手。", enable=anim)
            type_out("⚖️ 結果：平手\n", enable=anim)
        return "Draw", 1, seed
    else:
        if show_text:
            type_out("✅ 第0膛非實彈 → 轉換器策略 ⇒ A保證不敗且此局必勝。", enable=anim)
            type_out("🏆 勝者：A\n", enable=anim)
        return "A", 1, seed
