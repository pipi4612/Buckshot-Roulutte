import random
import time
import sys
from functools import lru_cache


# ===============================
# 🖋️ 輸出文字（模擬動畫）
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
# 🔢 理性策略表（622 + 手銬 + 平手）
# 狀態: V(m, b, turn, lifeA, lifeB, hcA)
# m: 剩餘膛位數（含當前膛）
# b: 從當前膛到尾的實彈數
# turn: 0=A, 1=B
# lifeA, lifeB: 命數
# hcA: 1=A 尚有手銬；0=已用過
# 回傳 (A勝率, 最佳動作)
# ===============================
@lru_cache(None)
def V(m, b, turn, lifeA, lifeB, hcA):
    # --- 子彈用盡 ---
    if b <= 0:
        if lifeA == lifeB:
            return 0.5, "draw"
        return (1.0, "terminal") if lifeA > lifeB else (0.0, "terminal")

    # --- 有人死亡 ---
    if lifeA <= 0 and lifeB <= 0:
        return 0.5, "draw"
    if lifeA <= 0:
        return 0.0, "terminal"
    if lifeB <= 0:
        return 1.0, "terminal"

    # 防禦：理論上不會出現 m<=0 且 b>0；保險處理
    if m <= 0:
        if lifeA == lifeB:
            return 0.5, "draw"
        return (1.0, "terminal") if lifeA > lifeB else (0.0, "terminal")

    p = b / m  # 當前膛為實彈機率

    # -----------------------------------
    # 手銬兩連動（逐槍結算；遇死即停）
    # seq: "OO","OS","SO","SS"
    # -----------------------------------
    def EV_two_actions(m1, b1, lifeA1, lifeB1, seq):
        p1 = b1 / m1
        ev = 0.0

        def after_first_blank():
            return EV_second(m1 - 1, b1, lifeA1, lifeB1, seq[1])

        def after_first_live(target):
            if target == 'O':  # 打中對手
                lifeB2 = lifeB1 - 1
                if lifeB2 <= 0:
                    return 1.0
                return EV_second(m1 - 1, b1 - 1, lifeA1, lifeB2, seq[1])
            else:              # 打中自己
                lifeA2 = lifeA1 - 1
                if lifeA2 <= 0:
                    return 0.0
                return EV_second(m1 - 1, b1 - 1, lifeA2, lifeB1, seq[1])

        if seq[0] == 'O':
            if p1 < 1:
                ev += (1 - p1) * after_first_blank()
            if p1 > 0:
                ev += p1 * after_first_live('O')
        else:  # 'S'
            if p1 < 1:
                ev += (1 - p1) * after_first_blank()
            if p1 > 0:
                ev += p1 * after_first_live('S')
        return ev

    def EV_second(m2, b2, lifeA2, lifeB2, a2):
        if b2 <= 0 or m2 <= 0:
            if lifeA2 == lifeB2:
                return 0.5
            return 1.0 if lifeA2 > lifeB2 else 0.0

        p2 = b2 / m2

        def handoff_to_B(m3, b3, lifeA3, lifeB3):
            return V(m3, b3, 1, lifeA3, lifeB3, 0)[0]

        ev2 = 0.0
        if a2 == 'O':  # 第二槍射對手
            if p2 < 1:
                ev2 += (1 - p2) * handoff_to_B(m2 - 1, b2, lifeA2, lifeB2)
            if p2 > 0:
                lifeB3 = lifeB2 - 1
                if lifeB3 <= 0:
                    ev2 += p2 * 1.0
                else:
                    ev2 += p2 * handoff_to_B(m2 - 1, b2 - 1, lifeA2, lifeB3)
        else:           # 第二槍射自己
            if p2 < 1:
                ev2 += (1 - p2) * handoff_to_B(m2 - 1, b2, lifeA2, lifeB2)
            if p2 > 0:
                lifeA3 = lifeA2 - 1
                if lifeA3 <= 0:
                    ev2 += p2 * 0.0
                else:
                    ev2 += p2 * handoff_to_B(m2 - 1, b2 - 1, lifeA3, lifeB2)
        return ev2

    # --- A 回合（最大化）---
    if turn == 0:
        # 不用手銬：兩個基本動作
        EV_self = 0.0
        if p < 1:
            V_same = V(m - 1, b, 0, lifeA, lifeB, hcA)[0]
            EV_self += (1 - p) * V_same
        if p > 0:
            hit_self = V(m - 1, b - 1, 1, lifeA - 1, lifeB, hcA)[0] if lifeA > 1 else 0.0
            EV_self += p * hit_self

        EV_opp = 0.0
        if p < 1:
            EV_opp += (1 - p) * V(m - 1, b, 1, lifeA, lifeB, hcA)[0]
        if p > 0:
            hit_opp = V(m - 1, b - 1, 1, lifeA, lifeB - 1, hcA)[0] if lifeB > 1 else 1.0
            EV_opp += p * hit_opp

        best_val, best_act = (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

        # 若還有手銬，考慮四種兩連動
        if hcA == 1:
            for seq in ("OO", "OS", "SO", "SS"):
                ev_hc = EV_two_actions(m, b, lifeA, lifeB, seq)
                if ev_hc > best_val:
                    best_val, best_act = ev_hc, "hc-" + seq
        return best_val, best_act

    # --- B 回合（最小化）---
    else:
        # 射自己
        EV_Bself = 0.0
        if p < 1:
            V_same = V(m - 1, b, 1, lifeA, lifeB, hcA)[0]  # 自射空包 → 保留回合
            EV_Bself += (1 - p) * V_same
        if p > 0:
            # ★ 修正點：若 B 只剩 1 命且命中自己 → 當場死亡 → A 勝率 = 1.0
            hit_Bself = V(m - 1, b - 1, 0, lifeA, lifeB - 1, hcA)[0] if lifeB > 1 else 1.0
            EV_Bself += p * hit_Bself

        # 射對方
        EV_Bopp = 0.0
        if p < 1:
            EV_Bopp += (1 - p) * V(m - 1, b, 0, lifeA, lifeB, hcA)[0]
        if p > 0:
            hit_Bopp = V(m - 1, b - 1, 0, lifeA - 1, lifeB, hcA)[0] if lifeA > 1 else 0.0
            EV_Bopp += p * hit_Bopp

        # B 選使 A 勝率最小者
        return (EV_Bself, "B-self") if EV_Bself < EV_Bopp else (EV_Bopp, "B-opp")


# ===============================
# 🎮 單局遊戲（6,2,2 + 手銬；A 起手必用手銬 = OO）
# ===============================
def simulate_one_game(show_text=True, show_bullets=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))
    idx = 0
    turn = 0  # 0=A, 1=B
    lifeA, lifeB = 2, 2
    hcA = 1  # A 有一次手銬（起手必用）
    round_count = 0
    first_turn = True

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）")
        type_out("規則：6格彈匣，2顆實彈，A、B 各有 2 條命，不旋轉。")
        type_out("A 有一次手銬，『起手必用』，採理性策略（max/min）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}")
        time.sleep(1)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        # --- 子彈用盡 → 比命/平手 ---
        if b == 0:
            if show_text:
                type_out("⚖️ 實彈用盡。")
                if lifeA == lifeB:
                    type_out("🤝 雙方生命相同 → 平手。")
                elif lifeA > lifeB:
                    type_out("🏆 勝者：A（生命多於B）")
                else:
                    type_out("🏆 勝者：B（生命多於A）")
            if lifeA == lifeB:
                return "Draw", round_count
            return ("A", round_count) if lifeA > lifeB else ("B", round_count)

        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")
            type_out(f"❤️ A命={lifeA} | B命={lifeB} | 手銬={'有' if hcA==1 else '無'}")

        # ============ A 回合 ============
        if turn == 0:
            # 起手必用手銬 → 固定 "OO"
            if first_turn and hcA == 1:
                seq = "OO"
                if show_text:
                    type_out(f"⛓️ A 使用手銬（起手必用）→ 連續兩次行動（{seq[0]} → {seq[1]}）")
                for i in range(2):
                    target = "B"  # OO
                    if show_text:
                        type_out(f"💥 A 對 {target} 開第 {i+1} 槍！")
                    was_live = idx in live_positions
                    if was_live:
                        live_positions.remove(idx)
                        lifeB -= 1
                        if show_text:
                            type_out("💀 【實彈】命中 B！")
                        if lifeB <= 0:
                            if show_text:
                                type_out("☠️ B 命歸零，A 勝。\n")
                            return "A", round_count
                    else:
                        if show_text:
                            type_out("💨 空包彈。")
                    idx = (idx + 1) % chambers
                # 兩槍結束、無人死亡 → 換 B，手銬變無
                hcA = 0
                first_turn = False
                turn = 1
                if show_text:
                    type_out("🔄 手銬回合結束 → 換 B 行動。\n")
                continue

            # 非起手或已無手銬 → 走 DP 決策
            _, action = V(m, b, turn, lifeA, lifeB, hcA)

            shoot_self = (action == "self")
            target = "A" if shoot_self else "B"
            if show_text:
                type_out(f"🧠 A 決策：{action}")
                type_out(f"💥 A 對 {target} 開槍！")

            was_live = idx in live_positions
            if was_live:
                live_positions.remove(idx)
                if target == "A":
                    lifeA -= 1
                    if show_text:
                        type_out("💀 【實彈】命中 A！")
                    if lifeA <= 0:
                        if show_text:
                            type_out("☠️ A 命歸零，B 勝。\n")
                        return "B", round_count
                else:
                    lifeB -= 1
                    if show_text:
                        type_out("💀 【實彈】命中 B！")
                    if lifeB <= 0:
                        if show_text:
                            type_out("☠️ B 命歸零，A 勝。\n")
                        return "A", round_count
            else:
                if show_text:
                    type_out("💨 空包彈。")

            idx = (idx + 1) % chambers
            if shoot_self and not was_live:
                if show_text:
                    type_out("🔁 A 射自己是空包彈 → 保留回合。\n")
                continue
            else:
                turn = 1
                if show_text:
                    type_out("🔄 換 B 行動。\n")
                continue

        # ============ B 回合 ============
        else:
            _, action = V(m, b, turn, lifeA, lifeB, hcA)
            shoot_self = (action == "B-self")
            target = "B" if shoot_self else "A"
            if show_text:
                type_out(f"🧠 B 決策：{action}")
                type_out(f"💥 B 對 {target} 開槍！")

            was_live = idx in live_positions
            if was_live:
                live_positions.remove(idx)
                if target == "A":
                    lifeA -= 1
                    if show_text:
                        type_out("💀 【實彈】命中 A！")
                    if lifeA <= 0:
                        if show_text:
                            type_out("☠️ A 命歸零，B 勝。\n")
                        return "B", round_count
                else:
                    lifeB -= 1
                    if show_text:
                        type_out("💀 【實彈】命中 B！")
                    if lifeB <= 0:
                        if show_text:
                            type_out("☠️ B 命歸零，A 勝。\n")
                        return "A", round_count
            else:
                if show_text:
                    type_out("💨 空包彈。")

            idx = (idx + 1) % chambers
            if shoot_self and not was_live:
                if show_text:
                    type_out("🔁 B 射自己是空包彈 → 保留回合。\n")
                continue
            else:
                turn = 0
                if show_text:
                    type_out("🔄 換 A 行動。\n")
                continue


# ===============================
# 🧮 蒙地卡羅模擬
# ===============================
def monte_carlo(trials=100000):
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
    return A_win / trials, B_win / trials, Draw / trials, total_rounds / trials


# ===============================
# 🚀 主程式執行（單局 + 模擬）
# ===============================
if __name__ == "__main__":
    simulate_one_game(show_text=True, show_bullets=True)
    type_out("\n📈 開始蒙地卡羅模擬（100,000 局）...\n", 0.03)
    start = time.time()
    A_rate, B_rate, D_rate, avg_rounds = monte_carlo(100000)
    end = time.time()

    type_out(f"✅ 模擬完成，用時 {end - start:.2f} 秒")
    type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
    type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
    type_out(f"🔸 平手率：{D_rate*100:.2f}%")
    type_out(f"🔸 平均輪數：約 {avg_rounds:.2f} 輪\n")

    P_eff_A = A_rate / (1 - D_rate) if (1 - D_rate) > 0 else 0.5
    type_out(f"🎯 有結果時 A 勝率（條件勝率）：{P_eff_A*100:.2f}%")

