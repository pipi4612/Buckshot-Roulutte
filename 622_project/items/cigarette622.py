# items/cigarette622.py
# ============================================
# 香菸（Cigarette 622）
# A 擁有一次香菸（+1 命），僅在：
#   「被 B 射中後」且「輪到 A」且「A 命=1」時自動觸發回血到 2。
# 其他行為依理性策略（A 最大化、B 最小化 A 勝率）。
# 與你提供的版本一致：含 last_hit_by 與「空包階段」處理，idx 線性走到 6 結束。
# 回傳：(winner, rounds, seed)
# ============================================

import random, time
from functools import lru_cache
from engine.type_out import type_out


# ===============================
# 理性策略表（含雙命＋平手＋香菸觸發條件＋空包階段）
# 狀態: V(m, b, turn, lifeA, lifeB, cigA, last_hit_by)
#   m: 剩餘格數 (1..6)
#   b: 剩餘實彈數 (0..2)
#   turn: 0=A, 1=B
#   lifeA, lifeB ∈ {0,1,2}
#   cigA ∈ {0,1}  （A 是否仍有香菸可用）
#   last_hit_by ∈ {-1, 0, 1} （上一發「打到 A」的來源：-1=無/未打中A，0=A，1=B）
# 回傳: (A勝率, 最佳動作字串)
# ===============================
@lru_cache(None)
def V_cig622(m, b, turn, lifeA, lifeB, cigA, last_hit_by):
    # --- 有人沒命 → 立刻終局 ---
    if lifeA <= 0 and lifeB <= 0:
        return 0.5, "draw"
    if lifeA <= 0:
        return 0.0, "terminal"
    if lifeB <= 0:
        return 1.0, "terminal"

    # --- 沒剩膛位 m=0 → 比命或平手 ---
    if m <= 0:
        if lifeA == 1 and lifeB == 1:
            return 0.5, "draw"
        elif lifeA > lifeB:
            return 1.0, "terminal"
        elif lifeB > lifeA:
            return 0.0, "terminal"
        else:
            return 0.5, "draw"

    # --- 只剩空包彈 b=0：處理「空包階段」的理性行為 ---
    if b <= 0:
        # 若輪到 A，且符合香菸條件（被B打過、命=1、尚有香菸），A 會立即回血
        if turn == 0 and cigA == 1 and lifeA == 1 and last_hit_by == 1:
            lifeA = 2
            cigA = 0
        # B 會吃空保留回合到 m=0；空包階段後直接比命
        if lifeA == 1 and lifeB == 1:
            return 0.5, "draw"
        elif lifeA > lifeB:
            return 1.0, "terminal"
        elif lifeB > lifeA:
            return 0.0, "terminal"
        else:
            return 0.5, "draw"

    # --- A 回合起手：只有「被B打過且命=1且有香菸」才會自動觸發 ---
    if turn == 0 and cigA == 1 and lifeA == 1 and last_hit_by == 1:
        lifeA = 2
        cigA = 0  # 用掉香菸

    # --- m==1 特例（最後一格一定開）---
    if m == 1:
        if turn == 0:  # A 對 B
            new_lifeB = lifeB - 1
            if new_lifeB <= 0 and lifeA <= 0:
                return 0.5, "opp"
            elif new_lifeB <= 0:
                return 1.0, "opp"
            else:
                # 開完最後一格 → m=0, b-1 ；last_hit_by 與 A 無關
                return V_cig622(0, b - 1, 1, lifeA, new_lifeB, cigA, -1)[0], "opp"
        else:  # B 對 A
            new_lifeA = lifeA - 1
            if new_lifeA <= 0 and lifeB <= 0:
                return 0.5, "B-opp"
            elif new_lifeA <= 0:
                return 0.0, "B-opp"
            else:
                # 被 B 打到 → 記錄 last_hit_by = 1；進到 A 的回合，但 m=0 → 立即比命（A無機會再開）
                return V_cig622(0, b - 1, 0, new_lifeA, lifeB, cigA, 1)[0], "B-opp"

    # --- 一般情況 ---
    p = b / m  # 命中實彈機率

    if turn == 0:
        # A 射自己：空包留回合；實彈自己 -1 命（last_hit_by=0）
        stay_same = V_cig622(m - 1, b, 0, lifeA, lifeB, cigA, -1)[0]
        hit_self = V_cig622(m - 1, b - 1, 1, lifeA - 1, lifeB, cigA, 0)[0] if lifeA > 1 else 0.0
        EV_self = (1 - p) * stay_same + p * hit_self

        # A 射對方：空包換 B；實彈 B -1 命
        miss_opp = V_cig622(m - 1, b, 1, lifeA, lifeB, cigA, -1)[0]
        hit_opp = V_cig622(m - 1, b - 1, 1, lifeA, lifeB - 1, cigA, -1)[0] if lifeB > 1 else 1.0
        EV_opp = (1 - p) * miss_opp + p * hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

    else:
        # B 射自己：空包留回合；實彈自己 -1 命
        stay_same = V_cig622(m - 1, b, 1, lifeA, lifeB, cigA, -1)[0]
        hit_Bself = V_cig622(m - 1, b - 1, 0, lifeA, lifeB - 1, cigA, -1)[0] if lifeB > 1 else 1.0
        EV_Bself = (1 - p) * stay_same + p * hit_Bself

        # B 射 A：空包換 A；實彈 A -1 命（last_hit_by=1）
        miss_Bopp = V_cig622(m - 1, b, 0, lifeA, lifeB, cigA, -1)[0]
        hit_Bopp = V_cig622(m - 1, b - 1, 0, lifeA - 1, lifeB, cigA, 1)[0] if lifeA > 1 else 0.0
        EV_Bopp = (1 - p) * miss_Bopp + p * hit_Bopp

        return (EV_Bself, "B-self") if EV_Bself < EV_Bopp else (EV_Bopp, "B-opp")


# ===============================
# 🎮 單局遊戲（6,2,2 + 香菸）
# - idx 線性遞增（不取模），走到 6 結束。
# - 含空包階段與香菸觸發規則。
# ===============================
def simulate_cigarette_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 兩顆實彈
    idx = 0                 # 線性走到 6 結束
    turn = 0                # 0=A, 1=B
    lifeA, lifeB = 2, 2
    cig_used = False
    last_hit_by = -1
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）", enable=anim)
        type_out("規則：6格彈匣，2顆實彈，A、B 各有 2 條命，不旋轉。", enable=anim)
        type_out("A 有一次香菸（+1命），只能在『被B射中後』且輪到自己、命=1 時自動使用。理性策略（max/min）。", enable=anim)
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}", enable=anim)
        time.sleep(0.2)

    while True:
        # 終止：膛位走完
        if idx >= chambers:
            if lifeA == 1 and lifeB == 1:
                return "Draw", round_count, seed
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            return winner, round_count, seed

        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        # --- 空包階段（b==0）的即時處理 ---
        if b == 0:
            # A 起手且符合香菸條件 → 先回血
            if turn == 0 and (not cig_used) and lifeA == 1 and last_hit_by == 1:
                cig_used = True
                lifeA += 1
            # 直接比命
            if lifeA == 1 and lifeB == 1:
                return "Draw", round_count, seed
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            return winner, round_count, seed

        # --- A 回合起手：香菸觸發條件 ---
        if turn == 0 and (not cig_used) and lifeA == 1 and last_hit_by == 1:
            cig_used = True
            lifeA += 1
            if show_text:
                type_out("🚬 A 使用香菸 → 回復 1 命（A命=2）。", enable=anim)

        # --- 理性決策 ---
        _, action = V_cig622(m, b, turn, lifeA, lifeB, 0 if cig_used else 1, last_hit_by)
        shoot_self = action.endswith("self")
        target = player if shoot_self else ("B" if player == "A" else "A")

        if show_text:
            type_out(f"🧠 {player} 決策：{action}", enable=anim)
            type_out(f"💥 {player} 對 {target} 開槍！", enable=anim)
            time.sleep(0.05)

        # --- 槍擊結果 ---
        was_live = idx in live_positions
        if was_live:
            live_positions.remove(idx)
            if target == "A":
                lifeA -= 1
                last_hit_by = 1  # 被 B 擊中
                if lifeA <= 0:
                    if show_text:
                        type_out("☠️ A 命歸零，B 勝。", enable=anim)
                    return "B", round_count, seed
            else:
                lifeB -= 1
                last_hit_by = -1  # 與 A 無關
                if lifeB <= 0:
                    if show_text:
                        type_out("☠️ B 命歸零，A 勝。", enable=anim)
                    return "A", round_count, seed
        else:
            if show_text:
                type_out("💨 空包彈。", enable=anim)
            last_hit_by = -1  # 沒打中 A

        # --- 換膛與回合處理（不取模；走到 6 結束）---
        idx += 1
        if shoot_self:
            if was_live:
                if show_text:
                    type_out(f"💥 {player} 射自己是【實彈】 → 回合結束。", enable=anim)
                # 自射命中 → 換人
                turn ^= 1
            else:
                if show_text:
                    type_out(f"🔁 {player} 射自己是空包彈 → 保留回合。", enable=anim)
                # 自射空包 → 不換人
                continue
        else:
            # 射對方 → 一律換人
            turn ^= 1
            if show_text:
                type_out(f"🔄 換 {('B' if turn==1 else 'A')} 行動。", enable=anim)
