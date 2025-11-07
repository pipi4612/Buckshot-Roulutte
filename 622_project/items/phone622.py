# items/phone622.py
# ============================================
# 手機（Phone 622）
# A 在第 1 回合使用手機，能看到「第 2~5 膛」中隨機一膛的資訊（實或空），
# B 不知道這項情報。
# 接著依理性策略進行整局（A 最大化、B 最小化 A 勝率）。
# 終局：彈光 → 比生命；同命 → 平手。
# ============================================

import random, time
from engine.type_out import type_out
from engine.base622 import V_base622

def simulate_phone_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng  = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))
    idx = 0
    turn = 0
    lifeA, lifeB = 2, 2
    rounds = 0
    phone_used = False
    info_pos = None
    info_live = None

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})", enable=anim)
        type_out("規則：6格、2顆實彈、A/B 各 2 命，不旋轉。", enable=anim)
        type_out("A 有一次手機，可查看第 2~5 膛其中一膛的內容。", enable=anim)
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(live_positions)}", enable=anim)
        time.sleep(0.3)

    while True:
        b = sum(1 for p in live_positions if p >= idx)
        if b == 0:
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("⚖️ 彈光 → 比生命判勝。", enable=anim)
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
        # A 第 1 回合使用手機
        # =========================
        if turn == 0 and not phone_used:
            phone_used = True
            info_pos = rng.choice([2, 3, 4, 5])
            info_live = (info_pos in live_positions)
            if show_text:
                type_out(f"📱 A 使用手機 → 看見第 {info_pos} 膛是【{'實彈' if info_live else '空包'}】", enable=anim)
                type_out("（此資訊僅 A 知曉）", enable=anim)
            # 若知道未來某膛為空 → 有助於後續決策（DP 本身不會反映，但可展示邏輯）
            # 為簡化，A 仍照理性策略行動
        else:
            _, action = V_base622(m, b, turn, lifeA, lifeB)
            shoot_self = action.endswith("self")

            target = player if shoot_self else ("B" if player == "A" else "A")
            if show_text:
                t = "自己" if shoot_self else target
                type_out(f"🧠 {player} 決策 → 射{t}", enable=anim)
                type_out(f"💥 {player} 對 {t} 開槍！", enable=anim)

            was_live = (idx in live_positions)
            if was_live:
                live_positions.remove(idx)
                if target == "A":
                    lifeA -= 1
                    if show_text: type_out("💀 命中 A！", enable=anim)
                    if lifeA <= 0:
                        if show_text: type_out("☠️ A 死亡 → B 勝。", enable=anim)
                        return "B", rounds, seed
                else:
                    lifeB -= 1
                    if show_text: type_out("💀 命中 B！", enable=anim)
                    if lifeB <= 0:
                        if show_text: type_out("☠️ B 死亡 → A 勝。", enable=anim)
                        return "A", rounds, seed
            else:
                if show_text: type_out("💨 空包。", enable=anim)

            idx = (idx + 1) % chambers
            if shoot_self and not was_live:
                if show_text: type_out(f"🔁 {player} 射自己空包 → 保留回合。", enable=anim)
                continue
            else:
                turn ^= 1
