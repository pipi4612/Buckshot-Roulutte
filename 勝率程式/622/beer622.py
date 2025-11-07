import random
import time
import sys
from functools import lru_cache

# ===============================
# ⚙️ 研究口徑切換：平手的價值
#   - 0.0 → 把平手當「0 分」（最大化 A 純勝率）✅ 與理論 1/3 對齊
#   - 0.5 → 把平手當「半分」（期望得分口徑，策略會偏向保平）
# ===============================
DRAW_VALUE = 0.0

# ===============================
# 🖋️ 文字輸出（模擬動畫）
# ===============================
def type_out(text, delay=0.03, newline=True):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        sys.stdout.write("\n")
        sys.stdout.flush()

# ===============================
# 🔢 動態規劃：A 的勝率（理性 max/min，含雙命與平手）
# 狀態 V(m, b, turn, lifeA, lifeB)
#   m: 剩餘膛位數
#   b: 剩餘實彈數
#   turn: 0=A, 1=B
#   lifeA, lifeB: A/B 剩餘生命
# 回傳 (A勝率, 最佳動作字串)
# ===============================
@lru_cache(None)
def V(m, b, turn, lifeA, lifeB):
    """回傳 (A勝率, 最佳動作)；turn: 0=A, 1=B"""
    # --- 終局：生命裁決 ---
    # （極少見）雙雙同回合歸零：按 DRAW_VALUE
    if lifeA <= 0 and lifeB <= 0:
        return DRAW_VALUE, "draw"
    if lifeA <= 0:
        return 0.0, "terminal"
    if lifeB <= 0:
        return 1.0, "terminal"

    # --- 終局：無彈可射（或 m<=0 容錯）---
    #   與模擬相符：比生命多寡；同命視為平手（價值= DRAW_VALUE）
    if b <= 0 or m <= 0:
        if lifeA > lifeB:
            return 1.0, "terminal"
        elif lifeB > lifeA:
            return 0.0, "terminal"
        else:
            return DRAW_VALUE, "draw"

    # --- 一般狀態 ---
    p = b / m  # 當前膛為實彈機率

    if turn == 0:
        # =======================
        # A 回合：最大化 A 勝率
        # =======================
        # 命中自己：若 A 僅 1 命 → 即敗，A 勝率=0
        hit_self = V(m - 1, b - 1, 1, lifeA - 1, lifeB)[0] if lifeA > 1 else 0.0
        # 命中對方：若 B 僅 1 命 → 即勝，A 勝率=1
        hit_opp  = V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0] if lifeB > 1 else 1.0

        if b == m:
            # p==1，不會打空
            EV_self = hit_self
            EV_opp  = hit_opp
        else:
            # 打空：自射→保留回合；射對方→換 B
            V_same_self_prob, _ = V(m - 1, b, 0, lifeA, lifeB)  # 自射打空，A 繼續
            V_next_opp_prob, _  = V(m - 1, b, 1, lifeA, lifeB)  # 射對方打空，換 B
            EV_self = (1 - p) * V_same_self_prob + p * hit_self
            EV_opp  = (1 - p) * V_next_opp_prob  + p * hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

    else:
        # =======================
        # B 回合：最小化 A 勝率
        # =======================
        # B 射自己命中：若 B 僅 1 命 → B 死，A 直接勝，A 勝率=1.0
        hit_Bself = V(m - 1, b - 1, 0, lifeA, lifeB - 1)[0] if lifeB > 1 else 1.0
        # B 射對方命中：若 A 僅 1 命 → A 死，A 勝率=0.0
        hit_Bopp  = V(m - 1, b - 1, 0, lifeA - 1, lifeB)[0] if lifeA > 1 else 0.0

        if b == m:
            # p==1，不會打空
            EV_Bself = hit_Bself
            EV_Bopp  = hit_Bopp
        else:
            # 打空：自射→保留回合；射對方→換 A
            V_same_B_prob, _ = V(m - 1, b, 1, lifeA, lifeB)  # B 自射打空，B 繼續
            V_next_A_prob, _ = V(m - 1, b, 0, lifeA, lifeB)  # B 射對方打空，換 A
            EV_Bself = (1 - p) * V_same_B_prob + p * hit_Bself
            EV_Bopp  = (1 - p) * V_next_A_prob + p * hit_Bopp

        return (EV_Bself, "B-self") if EV_Bself < EV_Bopp else (EV_Bopp, "B-opp")

# ===============================
# 🎮 單局模擬（6,2,2 + 啤酒一次，A 首回合使用，且不計輪）
# ===============================
def simulate_one_game(show_text=True, show_bullets=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))
    idx = 0
    turn = 0  # 0=A, 1=B
    beer_used = False
    lifeA, lifeB = 2, 2
    round_count = 0  # 只在實際「開槍」時才 +1

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）")
        type_out("規則：6格彈匣，2顆實彈，A、B 各有 2 條命，不旋轉。")
        type_out("A 有一次啤酒，可退掉當前膛位。理性策略（max/min）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}")
        time.sleep(0.6)

    while True:
        # 當前剩餘格數／實彈數（只看 >= idx 的未經過膛）
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        # --- 終局：無彈 ---
        if b == 0:
            if show_text:
                type_out("⚖️ 實彈退光。")
                if lifeA > lifeB:
                    type_out("🏆 勝者：A（生命多於B）")
                elif lifeB > lifeA:
                    type_out("🏆 勝者：B（生命多於A）")
                else:
                    type_out("🤝 雙方生命相同 → 平手。")
            if lifeA == lifeB:
                return "Draw", round_count
            return ("A" if lifeA > lifeB else "B"), round_count

        player = "A" if turn == 0 else "B"

        # --- 啤酒（A 限定，且不算一輪；A 保留回合）---
        if turn == 0 and not beer_used:
            beer_used = True
            if show_text:
                type_out(f"🍺 A 使用啤酒 → 退掉第 {idx} 格子彈。")
            if idx in live_positions:
                live_positions.remove(idx)
                if show_text:
                    type_out("   👉 這格是【實彈】，被退掉！")
            else:
                if show_text:
                    type_out("   👉 這格是空包彈，被退掉。")
            idx = (idx + 1) % chambers
            # A 保留回合
            continue

        # 重新計算（因為可能剛退過一格）
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        # --- 理性決策（與 DRAW_VALUE 一致的口徑）---
        A_win_prob, action = V(m, b, turn, lifeA, lifeB)
        shoot_self = action.endswith("self")
        target = player if shoot_self else ("B" if player == "A" else "A")

        # 只在「開槍」時計一輪
        round_count += 1
        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")
            type_out(f"❤️ A命={lifeA} | B命={lifeB}")
            type_out(f"🧠 {player} 決策：{action}")
            type_out(f"💥 {player} 對 {target} 開槍！")
            time.sleep(0.15)

        # --- 槍擊結果 ---
        was_live = idx in live_positions
        if was_live:
            live_positions.remove(idx)
            if show_text:
                type_out(f"💀 【實彈】命中 {target}！")
            if target == "A":
                lifeA -= 1
                if lifeA <= 0:
                    if show_text:
                        type_out("☠️ A 命歸零，B 勝。\n")
                    return "B", round_count
            else:
                lifeB -= 1
                if lifeB <= 0:
                    if show_text:
                        type_out("☠️ B 命歸零，A 勝。\n")
                    return "A", round_count
        else:
            if show_text:
                type_out("💨 空包彈。")

        # --- 換膛／換人 ---
        idx = (idx + 1) % chambers
        if shoot_self:
            if was_live:
                # 自射中彈 → 回合結束，換對方
                turn ^= 1
                if show_text:
                    type_out(f"💥 {player} 射自己是【實彈】 → 結束回合。\n")
            else:
                # 自射打空 → 保留回合（不換人）
                if show_text:
                    type_out(f"🔁 {player} 射自己是空包彈 → 保留回合。\n")
                continue
        else:
            # 射對方 → 不論中空都換人（命中已提前結束）
            turn ^= 1
            if show_text:
                type_out(f"🔄 換 {('B' if turn==1 else 'A')} 行動。\n")

# ===============================
# 🧮 蒙地卡羅模擬
# ===============================
def monte_carlo(trials=500000):
    A_win = B_win = Draw = 0
    total_rounds = 0
    for _ in range(trials):
        result, rounds = simulate_one_game(show_text=False)
        if result == "A":
            A_win += 1
        elif result == "B":
            B_win += 1
        else:
            Draw += 1
        total_rounds += rounds
    return A_win/trials, B_win/trials, Draw/trials, total_rounds/trials

# ===============================
# 🚀 主程式
# ===============================
if __name__ == "__main__":
    type_out(f"(設定) DRAW_VALUE = {DRAW_VALUE}\n", 0.02)
    simulate_one_game(show_text=True, show_bullets=True)

    type_out("\n📈 開始蒙地卡羅模擬（500,000 局）...\n", 0.02)
    start = time.time()
    A_rate, B_rate, D_rate, avg_rounds = monte_carlo(500000)
    end = time.time()

    type_out(f"✅ 模擬完成，用時 {end - start:.2f} 秒")
    type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
    type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
    type_out(f"🔸 平手率：{D_rate*100:.2f}%")
    type_out(f"🔸 平均輪數：約 {avg_rounds:.2f} 輪\n")

    # 兩種口徑並列輸出
    P_eff_A = A_rate / (1 - D_rate) if D_rate < 1 else 0.0
    type_out(f"🎯 有結果時 A 勝率（條件勝率）：{P_eff_A*100:.2f}%")
