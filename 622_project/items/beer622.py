# items/beer622.py
# ============================================
# 啤酒（Beer 622）
# A 有一次啤酒：在 A 的第一個行動「退掉當前膛位（idx）」，
# 然後 idx 往下一膛，回合仍由 A 繼續（= 不換手）。
# 之後雙方依理性策略（A 最大化、B 最小化 A 勝率）。
# 終局：若剩餘實彈數 b==0，直接以生命多寡判勝；同命 → 平手。
# 回傳：(winner, rounds, seed)
# ============================================

import random, time
from functools import lru_cache
from engine.type_out import type_out

# -----------------------------
# 動態規劃（沿用你提供的 622 啤酒版邏輯）
# -----------------------------
@lru_cache(None)
def V_beer622(m, b, turn, lifeA, lifeB):
    # 子彈用盡 → 依生命判勝/平手
    if b <= 0:
        if lifeA == 1 and lifeB == 1:
            return 0.5, "draw"
        elif lifeA > lifeB:
            return 1.0, "terminal"
        elif lifeB > lifeA:
            return 0.0, "terminal"
        else:
            return 0.5, "draw"

    # 生命歸零保險
    if lifeA <= 0 and lifeB <= 0:
        return 0.5, "draw"
    if lifeA <= 0:
        return 0.0, "terminal"
    if lifeB <= 0:
        return 1.0, "terminal"

    # 最後一格特例
    if m == 1:
        if turn == 0:  # A 行動
            new_lifeB = lifeB - 1
            if new_lifeB <= 0 and lifeA <= 0:
                return 0.5, "opp"
            elif new_lifeB <= 0:
                return 1.0, "opp"
            else:
                return V_beer622(0, 0, 1, lifeA, new_lifeB)[0], "opp"
        else:          # B 行動
            new_lifeA = lifeA - 1
            if new_lifeA <= 0 and lifeB <= 0:
                return 0.5, "B-opp"
            elif new_lifeA <= 0:
                return 0.0, "B-opp"
            else:
                return V_beer622(0, 0, 0, new_lifeA, lifeB)[0], "B-opp"

    p = b / m

    if turn == 0:  # A 最大化
        # 射自己
        V_same, _ = V_beer622(m - 1, b, 0, lifeA, lifeB)
        hit_self = V_beer622(m - 1, b - 1, 1, lifeA - 1, lifeB)[0] if lifeA > 1 else 0.0
        EV_self = (1 - p) * V_same + p * hit_self

        # 射對方
        hit_opp = V_beer622(m - 1, b - 1, 1, lifeA, lifeB - 1)[0] if lifeB > 1 else 1.0
        EV_opp = (1 - p) * V_beer622(m - 1, b, 1, lifeA, lifeB)[0] + p * hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

    else:           # B 最小化
        # 射自己
        V_same, _ = V_beer622(m - 1, b, 1, lifeA, lifeB)
        hit_Bself = V_beer622(m - 1, b - 1, 0, lifeA, lifeB - 1)[0] if lifeB > 1 else 0.5
        EV_Bself = (1 - p) * V_same + p * hit_Bself

        # 射對方
        hit_Bopp = V_beer622(m - 1, b - 1, 0, lifeA - 1, lifeB)[0] if lifeA > 1 else 0.0
        EV_Bopp = (1 - p) * V_beer622(m - 1, b, 0, lifeA, lifeB)[0] + p * hit_Bopp

        return (EV_Bself, "B-self") if EV_Bself <= EV_Bopp else (EV_Bopp, "B-opp")


# -----------------------------
# 🎮 單局模擬（啤酒 622）
# -----------------------------
def simulate_beer_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))
    idx = 0
    turn = 0  # 0=A, 1=B
    beer_used = False
    lifeA, lifeB = 2, 2
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）", enable=anim)
        type_out("規則：6格彈匣，2顆實彈，A、B 各有 2 條命，不旋轉。", enable=anim)
        type_out("A 有一次啤酒，可退掉當前膛位。理性策略（max/min）。", enable=anim)
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}", enable=anim)
        time.sleep(0.2)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        # 終局：彈光
        if b == 0:
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("⚖️ 實彈退光 → 依生命判勝。", enable=anim)
                type_out(f"🏆 結果：{winner}", enable=anim)
            return winner, round_count, seed

        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---", enable=anim)
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）", enable=anim)
            type_out(f"❤️ A命={lifeA} | B命={lifeB}", enable=anim)

        # -------------------------
        # 啤酒（A 第一個可行動的時機使用一次）
        # -------------------------
        if turn == 0 and not beer_used:
            beer_used = True
            if show_text:
                type_out(f"🍺 A 使用啤酒 → 退掉第 {idx} 格子彈。", enable=anim)
            if idx in live_positions:
                live_positions.remove(idx)
                if show_text:
                    type_out("   👉 這格是【實彈】，被退掉！", enable=anim)
            else:
                if show_text:
                    type_out("   👉 這格是空包彈，被退掉。", enable=anim)
            # 退膛後往下一膛，仍為 A 行動
            idx = (idx + 1) % chambers
            continue

        # -------------------------
        # 理性決策
        # -------------------------
        _, action = V_beer622(m, b, turn, lifeA, lifeB)
        shoot_self = action.endswith("self")
        target = player if shoot_self else ("B" if player == "A" else "A")

        if show_text:
            type_out(f"🧠 {player} 決策：{action}", enable=anim)
            type_out(f"💥 {player} 對 {target} 開槍！", enable=anim)
            time.sleep(0.05)

        # -------------------------
        # 槍擊結果
        # -------------------------
        was_live = (idx in live_positions)
        if was_live:
            live_positions.remove(idx)
            if target == "A":
                lifeA -= 1
                if lifeA <= 0:
                    if show_text:
                        type_out("☠️ A 命歸零，B 勝。", enable=anim)
                    return "B", round_count, seed
            else:
                lifeB -= 1
                if lifeB <= 0:
                    if show_text:
                        type_out("☠️ B 命歸零，A 勝。", enable=anim)
                    return "A", round_count, seed
        else:
            if show_text:
                type_out("💨 空包彈。", enable=anim)

        # -------------------------
        # 換膛 / 換手
        # -------------------------
        idx = (idx + 1) % chambers
        if shoot_self:
            if was_live:
                # 自射命中 → 換手
                turn ^= 1
            else:
                # 自射空包 → 保留回合
                if show_text:
                    type_out(f"🔁 {player} 射自己空包 → 保留回合。", enable=anim)
                continue
        else:
            # 射對方 → 一律換手
            turn ^= 1
