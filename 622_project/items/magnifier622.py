# items/magnifier622.py
# ============================================
# 放大鏡（Magnifier 622）
# A 在「第 1 回合」必用放大鏡，只查看當前膛（idx=0）是否為實彈：
#   - 若看到【實彈】 → 這一槍選擇射對方
#   - 若看到【空包】 → 這一槍選擇射自己（空包則保留回合）
# 之後雙方一律依理性策略（A 最大化、B 最小化 A 勝率）。
# 終局：彈光以生命判勝；同命則平手。
# 回傳：(winner, rounds, seed)
# ============================================

import random, time
from engine.type_out import type_out
from engine.base622 import V_base622


def simulate_magnifier_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng  = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 2 顆實彈
    idx = 0
    turn = 0                 # 0=A, 1=B
    lifeA, lifeB = 2, 2
    rounds = 0
    mag_used = False

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})", enable=anim)
        type_out("規則：6格、2發實彈，A/B 各 2 命，不旋轉。", enable=anim)
        type_out("A 有一次放大鏡：第 1 回合只查看當前膛位內容。", enable=anim)
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(live_positions)}", enable=anim)
        time.sleep(0.2)

    while True:
        # 剩餘實彈
        b = sum(1 for p in live_positions if p >= idx)
        if b == 0:
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("⚖️ 實彈退光 → 依生命判勝。", enable=anim)
                type_out(f"🏆 結果：{winner}", enable=anim)
            return winner, rounds, seed

        rounds += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx

        if show_text:
            type_out(f"\n--- 第 {rounds} 輪 ---", enable=anim)
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）", enable=anim)
            type_out(f"❤️ A命={lifeA} | B命={lifeB}", enable=anim)

        # =========================
        # A 第 1 回合：使用放大鏡
        # =========================
        if turn == 0 and not mag_used:
            mag_used = True
            saw_live = (idx in live_positions)
            if show_text:
                type_out(f"🪞 A 使用放大鏡 → 當前膛位為【{'實彈' if saw_live else '空包'}】", enable=anim)
            shoot_self = (not saw_live)   # 空包 → 自射以保留回合；實彈 → 射對方
            action = "self" if shoot_self else "opp"
        else:
            # 後續依理性策略（共用 base 的 V）
            _, action = V_base622(m, b, turn, lifeA, lifeB)
            shoot_self = action.endswith("self")

        # =========================
        # 執行射擊
        # =========================
        target = player if shoot_self else ("B" if player == "A" else "A")
        if show_text:
            t = "自己" if shoot_self else target
            type_out(f"🧠 {player} 決策 → 射{t}", enable=anim)
            type_out(f"💥 {player} 對 {t} 開槍！", enable=anim)

        was_live = (idx in live_positions)
        if was_live:
            live_positions.remove(idx)
            if shoot_self:
                # 自射命中
                if player == "A":
                    lifeA -= 1
                    if show_text: type_out("💀 【實彈】命中 A！", enable=anim)
                    if lifeA <= 0:
                        if show_text: type_out("☠️ A 命歸零 → B 勝。", enable=anim)
                        return "B", rounds, seed
                else:
                    lifeB -= 1
                    if show_text: type_out("💀 【實彈】命中 B！", enable=anim)
                    if lifeB <= 0:
                        if show_text: type_out("☠️ B 命歸零 → A 勝。", enable=anim)
                        return "A", rounds, seed
                # 自射命中 → 換人
                idx = (idx + 1) % chambers
                turn ^= 1
            else:
                # 射對方命中
                if player == "A":
                    lifeB -= 1
                    if show_text: type_out("💥 【實彈】命中 B！", enable=anim)
                    if lifeB <= 0:
                        if show_text: type_out("☠️ B 命歸零 → A 勝。", enable=anim)
                        return "A", rounds, seed
                else:
                    lifeA -= 1
                    if show_text: type_out("💥 【實彈】命中 A！", enable=anim)
                    if lifeA <= 0:
                        if show_text: type_out("☠️ A 命歸零 → B 勝。", enable=anim)
                        return "B", rounds, seed
                # 射對方 → 換人
                idx = (idx + 1) % chambers
                turn ^= 1
        else:
            if show_text:
                type_out("💨 空包。", enable=anim)
            # 空包：自射保留回合；射對方則換人
            idx = (idx + 1) % chambers
            if shoot_self:
                if show_text:
                    type_out(f"🔁 {player} 射自己空包 → 保留回合。", enable=anim)
                continue
            else:
                if show_text:
                    type_out(f"🔄 {player} 射對方空包 → 換人。", enable=anim)
                turn ^= 1
