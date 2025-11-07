# items/saw622.py
# ============================================
# 手鋸（Saw 622）
# A 第 1 回合必用手鋸（短槍管）：該槍若命中 → 對方 -2 命（直接死亡）。
# 之後雙方依理性策略（A 最大化、B 最小化 A 勝率）。
# 與你提供的 622 手鋸版本一致：首回合強制、命中扣 2 命、自射空包保留回合。
# 回傳：(winner, rounds, seed)
# ============================================

import random, time
from engine.type_out import type_out
from engine.base622 import V_base622


def simulate_saw_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng  = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 2 顆實彈
    idx = 0
    turn = 0          # 0=A, 1=B
    lifeA, lifeB = 2, 2
    round_count = 0
    first_round_done = False

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）", enable=anim)
        type_out("規則：6格彈匣，2顆實彈，A、B 各 2 命，不旋轉。", enable=anim)
        type_out("A 有一次手鋸（短槍管）：第一回合必用，命中傷害 = 2。", enable=anim)
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}", enable=anim)
        time.sleep(0.2)

    while True:
        # 若「剩餘實彈數」為 0 → 直接比命
        b = sum(1 for p in live_positions if p >= idx)
        if b == 0:
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("⚖️ 實彈退光 → 依生命判勝。", enable=anim)
                type_out(f"🏆 結果：{winner}", enable=anim)
            return winner, round_count, seed

        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx

        if show_text:
            type_out(f"\n--- 第 {round_count} 輪 ---", enable=anim)
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）", enable=anim)
            type_out(f"❤️ A命={lifeA} | B命={lifeB}", enable=anim)

        # =========================
        # 第 1 回合：A 強制使用手鋸
        # =========================
        if not first_round_done and turn == 0:
            first_round_done = True
            use_saw = True
            shoot_self = False  # 首回合一定射對方
            action = "saw-opp"
            if show_text:
                type_out("🪚 A 使用手鋸（短槍管）：此槍命中則 B -2 命！", enable=anim)
                type_out(f"🧠 A 決策：{action}", enable=anim)
        else:
            # 後續一律以理性策略（使用 base622 的 V）
            use_saw = False
            _, action = V_base622(m, b, turn, lifeA, lifeB)
            shoot_self = action.endswith("self")
            if show_text:
                t = "自己" if shoot_self else ("B" if player == "A" else "A")
                type_out(f"🧠 {player} 決策：{action}（射{t}）", enable=anim)

        # =========================
        # 槍擊
        # =========================
        target = player if shoot_self else ("B" if player == "A" else "A")
        if show_text:
            type_out(f"💥 {player} 對 {target} 開槍！", enable=anim)

        was_live = (idx in live_positions)
        if was_live:
            live_positions.remove(idx)
            if target == "A":
                lifeA -= 1
                if show_text:
                    type_out("💀 【實彈】命中 A！", enable=anim)
                if lifeA <= 0:
                    if show_text:
                        type_out("☠️ A 命歸零 → B 勝。", enable=anim)
                    return "B", round_count, seed
            else:
                # 命中 B：若為首回合手鋸 → -2 命，否則 -1 命
                dmg = 2 if use_saw else 1
                lifeB -= dmg
                if show_text:
                    if use_saw:
                        type_out("💥 手鋸重擊！【實彈】命中 B，傷害 -2。", enable=anim)
                    else:
                        type_out("💥 【實彈】命中 B！", enable=anim)
                if lifeB <= 0:
                    if show_text:
                        type_out("☠️ B 命歸零 → A 勝。", enable=anim)
                    return "A", round_count, seed
        else:
            if show_text:
                type_out("💨 空包彈。", enable=anim)

        # =========================
        # 換膛 & 換人規則
        # =========================
        idx = (idx + 1) % chambers
        if shoot_self:
            # 自射空包 → 保留回合；自射實彈 → 換人
            if not was_live:
                if show_text:
                    type_out(f"🔁 {player} 射自己空包 → 保留回合。", enable=anim)
                continue
            else:
                turn ^= 1
        else:
            # 射對方 → 不論命中與否，一律換人
            turn ^= 1
