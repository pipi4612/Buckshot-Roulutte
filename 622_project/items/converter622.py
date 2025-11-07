# items/converter622.py
# ============================================
# 轉換器（Converter 622）
# A 第1回合必用：翻轉第0膛（實→空、空→實），
# 然後立刻射擊對方，再進入理性對局。
# ============================================

import random, time
from functools import lru_cache
from engine.type_out import type_out
from engine.base622 import V_base622


# ============================================================
# 🎮 單局模擬
# ============================================================
def simulate_converter_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 2發實彈
    idx, turn, lifeA, lifeB, rounds = 0, 0, 2, 2, 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})", enable=anim)
        type_out("規則：6格2實彈，A/B各2命，不旋轉。", enable=anim)
        type_out("A 有一次轉換器（第1回合必用）。", enable=anim)
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}", enable=anim)
        time.sleep(0.3)

    # -------------------------
    # 第1回合：A 使用轉換器
    # -------------------------
    if show_text:
        type_out(f"🔁 A 使用轉換器 → 翻轉第 {idx} 膛", enable=anim)

    if idx in live_positions:
        live_positions.remove(idx)
        if show_text:
            type_out("   👉 原本是【實彈】→ 翻成【空包彈】（-1 顆實彈）", enable=anim)
    else:
        live_positions.add(idx)
        if show_text:
            type_out("   👉 原本是【空包彈】→ 翻成【實彈】（+1 顆實彈）", enable=anim)

    # 翻轉後立即射 B
    was_live = idx in live_positions
    if show_text:
        type_out("💥 A 對 B 開槍！", enable=anim)
    if was_live:
        live_positions.remove(idx)
        lifeB -= 1
        if show_text:
            type_out(f"💀 命中！B 生命剩 {lifeB}", enable=anim)
        if lifeB <= 0:
            if show_text:
                type_out("🏆 B 死亡，A 勝！", enable=anim)
            return "A", 1, seed
    else:
        if show_text:
            type_out("💨 空包彈。未命中。", enable=anim)

    # -------------------------
    # 進入理性對局
    # -------------------------
    idx = (idx + 1) % chambers
    turn = 1  # 換 B
    rounds = 1

    while True:
        rounds += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = sum(1 for p in live_positions if p >= idx)

        if b == 0:
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("🏁 彈光 → 比生命判勝。", enable=anim)
                type_out(f"🏆 勝者：{winner}", enable=anim)
            return winner, rounds, seed

        _, action = V_base622(m, b, turn, lifeA, lifeB)
        shoot_self = action.endswith("self")
        target = "A" if (turn == 1 and not shoot_self) else "B" if (turn == 0 and not shoot_self) else player

        if show_text:
            t = "自己" if shoot_self else target
            type_out(f"🧠 {player} 決策→射{t}", enable=anim)

        was_live = idx in live_positions
        if was_live:
            live_positions.remove(idx)
            if target == "A":
                lifeA -= 1
                if show_text:
                    type_out("💥 實彈命中 A！", enable=anim)
                if lifeA <= 0:
                    if show_text:
                        type_out("☠️ A 死亡，B 勝。", enable=anim)
                    return "B", rounds, seed
            else:
                lifeB -= 1
                if show_text:
                    type_out("💥 實彈命中 B！", enable=anim)
                if lifeB <= 0:
                    if show_text:
                        type_out("☠️ B 死亡，A 勝。", enable=anim)
                    return "A", rounds, seed
        else:
            if show_text:
                type_out("💨 空包。", enable=anim)

        idx = (idx + 1) % chambers
        if shoot_self:
            if not was_live:
                if show_text:
                    type_out(f"🔁 {player} 射自己空包 → 保留回合。", enable=anim)
                continue
        turn ^= 1
