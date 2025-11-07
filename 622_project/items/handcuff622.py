# items/handcuff622.py
# ============================================
# 手銬（Handcuff 622）
# A 起手立即使用手銬：B 的第 1 回合被「跳過」，
# → 等效為 A 於開局連續行動兩次（本實作採固定對 B 開槍兩次）。
# 之後恢復理性策略（使用 V_base622）。
# 雙命模型下可能平手；終局以「彈光比生命，同命平手」裁決。
# ============================================

import random, time
from engine.type_out import type_out
from engine.base622 import V_base622


def simulate_handcuff_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng  = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 兩顆實彈
    idx = 0                    # 當前膛位（0~5）
    turn = 0                   # 0=A, 1=B
    lifeA, lifeB = 2, 2        # 各 2 命
    rounds = 0                 # 後續正常回合計數（手銬兩槍不列入此回合數）
    cuff_used = False

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})", enable=anim)
        type_out("規則：6格、2實彈、A/B 各 2 命，不旋轉。", enable=anim)
        type_out("A 有一次手銬：使 B 的第 1 回合『跳過』→ A 開局連續兩次行動。", enable=anim)
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(live_positions)}", enable=anim)
        time.sleep(0.3)

    # =========================
    # 第 1 階段：A 使用手銬 → 連續兩次行動（固定射 B）
    # =========================
    cuff_used = True
    if show_text:
        type_out("🔗 A 使用手銬 → B 的第 1 回合被跳過。", enable=anim)
        type_out("🔫 手銬回合：A 連續兩槍（固定射 B）。", enable=anim)

    for i in range(2):
        if show_text:
            type_out(f"💥 手銬第 {i+1} 槍 → A 射 B", enable=anim)

        was_live = (idx in live_positions)
        if was_live:
            live_positions.remove(idx)
            lifeB -= 1
            if show_text:
                type_out("💀 命中 B（實彈）！B 扣 1 命。", enable=anim)
            if lifeB <= 0:
                if show_text:
                    type_out("☠️ B 死亡 → A 勝！", enable=anim)
                return "A", i + 1, seed  # i+1 表示在第幾槍結束遊戲
        else:
            if show_text:
                type_out("💨 空包彈。", enable=anim)

        # 轉到下一膛
        idx = (idx + 1) % chambers

    # 手銬兩槍結束且無人死亡 → 換 B 正常開始
    turn = 1
    if show_text:
        type_out("🔄 手銬回合結束 → 從 B 開始恢復理性對局。", enable=anim)
        time.sleep(0.2)

    # =========================
    # 第 2 階段：正常理性對局（使用 V_base622）
    # =========================
    while True:
        rounds += 1
        player = "A" if turn == 0 else "B"

        # m: 從當前膛到尾剩餘格數；b: 其中實彈數
        m = chambers - idx
        b = sum(1 for p in live_positions if p >= idx)

        # 實彈用盡 → 比生命
        if b == 0:
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("⚖️ 實彈用盡 → 依生命判勝。", enable=anim)
                type_out(f"🏆 結果：{winner}", enable=anim)
            return winner, rounds, seed

        # 用 DP 要動作
        _, action = V_base622(m, b, turn, lifeA, lifeB)
        shoot_self = action.endswith("self")
        target = player if shoot_self else ("B" if player == "A" else "A")

        if show_text:
            t = "自己" if shoot_self else target
            type_out(f"--- 第 {rounds} 輪 ---", enable=anim)
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）", enable=anim)
            type_out(f"❤️ A命={lifeA} | B命={lifeB}", enable=anim)
            type_out(f"🧠 {player} 決策 → 射{t}", enable=anim)

        was_live = (idx in live_positions)
        if was_live:
            live_positions.remove(idx)
            if target == "A":
                lifeA -= 1
                if show_text: type_out("💥 命中 A！", enable=anim)
                if lifeA <= 0:
                    if show_text: type_out("☠️ A 死亡 → B 勝。", enable=anim)
                    return "B", rounds, seed
            else:
                lifeB -= 1
                if show_text: type_out("💥 命中 B！", enable=anim)
                if lifeB <= 0:
                    if show_text: type_out("☠️ B 死亡 → A 勝。", enable=anim)
                    return "A", rounds, seed
        else:
            if show_text: type_out("💨 空包。", enable=anim)

        # 移到下一膛
        idx = (idx + 1) % chambers

        # 自射空包 → 保留回合；否則換手
        if shoot_self and not was_live:
            if show_text: type_out(f"🔁 {player} 射自己是空包 → 保留回合。", enable=anim)
            continue
        else:
            turn ^= 1
