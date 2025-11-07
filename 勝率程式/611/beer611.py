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
# 🔢 理性策略表（6-1-1，含「啤酒退光→平手」）
# 狀態：m=剩餘格數(含當前)，b=剩餘實彈數(∈{0,1})，turn=0(A)/1(B)
# ===============================
@lru_cache(None)
def V(m, b, turn):
    """回傳 (A勝率, 最佳動作字串)"""
    # --- 終局：沒有實彈 → 平手（只有啤酒退掉唯一實彈才會發生）---
    if b <= 0:
        return 0.5, "draw"

    # --- 最後一格 ---
    if m == 1:
        if turn == 0:   # A 開最後一格：一定射對方必勝
            return 1.0, "opp"
        else:           # B 開最後一格：一定射 A，A 必敗
            return 0.0, "B-opp"

    p = b / m

    if turn == 0:
        # A 射自己：打中就輸（A勝率0），空包彈保留回合
        EV_self = (1 - p) * V(m - 1, b, 0)[0]
        # A 射對方：打中直接贏；空包彈換 B
        EV_opp  = p * 1 + (1 - p) * V(m - 1, b, 1)[0]
        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")
    else:
        # B 射自己：打中 B 死→A贏；空包彈保留回合在 B
        EV_Bself = p * 1 + (1 - p) * V(m - 1, b, 1)[0]
        # B 射 A：打中 A 死→A輸；空包彈換 A
        EV_Bopp  = p * 0 + (1 - p) * V(m - 1, b, 0)[0]
        return (EV_Bself, "B-self") if EV_Bself <= EV_Bopp else (EV_Bopp, "B-opp")

# ===============================
# 🎮 單局遊戲（6,1,1 + 啤酒）
# ===============================
def simulate_one_game_611(show_text=True, show_bullets=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    # 唯一實彈
    live_pos = rng.randrange(chambers)   # 單一位置 [0..5]
    idx = 0
    turn = 0  # 0=A, 1=B
    beer_used = False
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）")
        type_out("規則：6格彈匣，1顆實彈，A、B 各 1 命，不旋轉。")
        type_out("A 有一次啤酒，第一回合必用。理性策略（A 最大化 / B 最小化 A 勝率）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：[{live_pos}]")
        time.sleep(1)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = 1 if live_pos >= idx else 0

        # --- 沒有實彈：平手（只會在啤酒退掉實彈時出現） ---
        if b == 0:
            if show_text:
                type_out("⚖️ 實彈已退光 → 平手。")
            return "Draw", round_count

        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")

        # --- A 第一回合必用啤酒 ---
        if turn == 0 and not beer_used:
            beer_used = True
            if show_text:
                type_out(f"🍺 A 使用啤酒 → 退掉第 {idx} 格子彈。")
            if idx == live_pos:
                if show_text:
                    type_out("   👉 這格是【實彈】，被退掉 → 平手。\n")
                return "Draw", round_count  # 唯一平手情形
            else:
                if show_text:
                    type_out("   👉 這格是空包彈，被退掉。")
                idx += 1
                # 仍是 A 回合
                continue

        # --- 理性決策 ---
        _, action = V(m, b, turn)
        shoot_self = action.endswith("self")
        target = player if shoot_self else ("B" if player == "A" else "A")

        if show_text:
            type_out(f"🧠 {player} 決策：{action}")
            type_out(f"💥 {player} 對 {target} 開槍！")
            time.sleep(0.2)

        # --- 槍擊結果 ---
        was_live = (idx == live_pos)
        if was_live:
            if show_text:
                type_out(f"💀 這發是【實彈】！{target} 被擊中。")
            winner = "B" if target == "A" else "A"
            if show_text:
                type_out(f"🏆 勝者：{winner}\n")
            return winner, round_count
        else:
            if show_text:
                type_out("💨 空包彈。")

        # --- 換膛與回合處理 ---
        idx += 1
        if shoot_self:
            if show_text:
                type_out(f"🔁 {player} 射自己是空包彈 → 保留回合。\n")
            # turn 不變
            continue
        else:
            turn ^= 1
            if show_text:
                type_out(f"🔄 換 {('B' if turn==1 else 'A')} 行動。\n")
            continue

# ===============================
# 🧮 蒙地卡羅模擬
# ===============================
def monte_carlo_611(trials=1_000_000):
    A_win = B_win = Draw = 0
    total_rounds = 0
    for _ in range(trials):
        result, rounds = simulate_one_game_611(show_text=False)
        if result == "A":
            A_win += 1
        elif result == "B":
            B_win += 1
        else:
            Draw += 1
        total_rounds += rounds
    return A_win/trials, B_win/trials, Draw/trials, total_rounds/trials

# ===============================
# 🚀 主程式執行
# ===============================
simulate_one_game_611(show_text=True, show_bullets=True)
type_out("\n📈 開始蒙地卡羅模擬（1000,000 局）...\n", 0.03)
start = time.time()
A_rate, B_rate, D_rate, avg_rounds = monte_carlo_611(1_000_000)
end = time.time()

type_out(f"✅ 模擬完成，用時 {end - start:.2f} 秒")
type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
type_out(f"🔸 平手率：{D_rate*100:.2f}%")
type_out(f"🔸 平均輪數：約 {avg_rounds:.2f} 輪\n")

# 有結果時（排除平手）的 A 條件勝率
P_eff_A = A_rate / (1 - D_rate) if (1 - D_rate) > 0 else 0.5
type_out(f"🎯 有結果時 A 勝率（條件勝率）：{P_eff_A*100:.2f}%")
