import random
import time
import sys
from functools import lru_cache

# ===============================
# 文字輸出
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
# 動態規劃：V(m, b, turn)
# m: 當前到末端剩餘格數（含當前）
# b: 當前到末端剩餘實彈數（611 => 0 或 1）
# turn: 0=A, 1=B
# 回傳: (A勝率, 推薦動作)
#   A 動作: "opp"/"self"
#   B 動作: "B-opp"/"B-self"
# ===============================
@lru_cache(None)
def V(m, b, turn):
    # 邊界與終止（611理論上只在命中時終止；以下為保險）
    if m <= 0 or b <= 0:
        return 0.0, "terminal"

    # 最後一格：理性必射對方
    if m == 1:
        if turn == 0:
            return 1.0, "opp"     # A 射對方 → A勝
        else:
            return 0.0, "B-opp"   # B 射A → A敗

    p = b / m  # 無情報下命中率

    if turn == 0:
        # A：最大化 A 勝率
        V_same, _ = V(m - 1, b, 0)   # 自射空包 → 保留回合（仍A）
        V_pass, _ = V(m - 1, b, 1)   # 射對方空包 → 換B
        EV_self = (1 - p) * V_same               # 自射命中→A輸(0)，不寫也OK
        EV_opp  = p * 1.0 + (1 - p) * V_pass    # 射對方命中→A勝(1)
        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")
    else:
        # B：最小化 A 勝率
        V_same, _ = V(m - 1, b, 1)   # 自射空包 → 保留回合（仍B）
        V_pass, _ = V(m - 1, b, 0)   # 射對方空包 → 換A
        EV_self = p * 1.0 + (1 - p) * V_same    # 自射命中→A勝(1)
        EV_opp  = p * 0.0 + (1 - p) * V_pass    # 射對方命中→A敗(0)
        # 相等時偏好射對方
        return (EV_Bself := EV_self, "B-self") if EV_self < EV_opp else (EV_opp, "B-opp")

# ===============================
# 🎮 單局遊戲（手銬611：A 第一回合必用 OO，其後理性）
# ===============================
def simulate_one_game_handcuff_611(show_text=True, show_bullets=False):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    bullet_pos = rng.randrange(chambers)     # 唯一實彈
    idx = 0                                  # 起始膛位
    turn = 0                                 # 0=A, 1=B
    round_count = 0
    first_turn = True                        # A 的第一回合旗標

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})")
        type_out("規則：6格1發實彈（611），不旋轉；自射空包保留回合、射對方空包換人；"
                 "只剩最後一格必射對方。A 有一次手銬，『第一回合必用』兩連動（OO）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{bullet_pos}")
        time.sleep(0.5)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = 1 if bullet_pos >= idx else 0     # 611：當前到末端的實彈數

        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")

        # ========== A 第一回合：必用手銬 (固定 OO) ==========
        if turn == 0 and first_turn:
            first_turn = False
            if show_text:
                type_out("⛓️ A 使用手銬（起手必用）→ 連續兩次行動（O → O）")
            for i in range(2):
                target = "B"  # OO：都射對方
                if show_text:
                    type_out(f"💥 A（手銬第 {i+1} 槍）對 {target} 開槍！")
                    time.sleep(0.3)
                # 命中即終局
                if idx == bullet_pos:
                    winner = "A"  # 射對方命中 → A勝
                    if show_text:
                        type_out("💥 【實彈】！")
                        type_out(f"🏆 勝者：{winner}\n")
                    return winner, round_count
                else:
                    if show_text: type_out("💨 空包。")
                    idx = (idx + 1) % chambers
            # 兩槍皆空包 → 換 B
            if show_text: type_out("🔄 手銬回合結束（皆空包）→ 換 B 行動。\n")
            turn = 1
            continue

        # ========== 其後回合：理性決策 ==========
        # 特例：只剩最後一格 → 必射對方
        if m == 1:
            shoot_self = False
            if show_text: type_out("只剩最後一格 → 射向對方！")
        else:
            _, action = V(m, b, turn)
            shoot_self = (action in ("self", "B-self"))

        target = player if shoot_self else ("B" if player == "A" else "A")
        if show_text:
            type_out(f"🧠 {player} 決策：{'B-self' if (turn==1 and shoot_self) else ('self' if shoot_self else ('opp' if turn==0 else 'B-opp'))}")
            type_out(f"💥 {player} 對 {target} 開槍！")

        # 命中即終局
        if idx == bullet_pos:
            winner = "B" if target == "A" else "A"
            if show_text:
                type_out("💥 【實彈】！")
                type_out(f"🏆 勝者：{winner}\n")
            return winner, round_count
        else:
            if show_text: type_out("💨 空包。")
            idx = (idx + 1) % chambers
            if shoot_self:
                if show_text: type_out(f"🔁 {player} 射自己空包 → 保留回合。\n")
                continue
            else:
                turn ^= 1
                if show_text: type_out(f"🔄 {player} 射對方空包 → 換 {('B' if player=='A' else 'A')}。\n")
                continue

# ===============================
# 蒙地卡羅模擬
# ===============================
def monte_carlo_simulation(trials=500000):
    A_win = 0
    total_rounds = 0
    for _ in range(trials):
        winner, rounds = simulate_one_game_handcuff_611(show_text=False)
        if winner == "A":
            A_win += 1
        total_rounds += rounds
    return A_win / trials, 1 - A_win / trials, total_rounds / trials

# ===============================
# 執行
# ===============================
if __name__ == "__main__":
    simulate_one_game_handcuff_611(show_text=True, show_bullets=True)
    type_out("\n📈 開始蒙地卡羅模擬（500,000 局）...\n", 0.03)
    s = time.time()
    A_rate, B_rate, avg_rounds = monte_carlo_simulation(500000)
    e = time.time()
    type_out(f"✅ 模擬完成，用時 {e - s:.2f} 秒", 0.03)
    type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
    type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
    type_out(f"🔸 平均遊戲輪數：約 {avg_rounds:.2f} 輪\n")
