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
# 動態規劃 (A最大化 / B最小化 A勝率)
# 狀態: V(m, b, turn)
# m: 當前到末端剩餘格數（含當前）
# b: 當前到末端剩餘實彈數（611 => b 只會是 0 或 1）
# turn: 0=A, 1=B
# 回傳: (A勝率, 建議動作)
# ===============================
@lru_cache(None)
def V(m, b, turn):
    # 邊界保護
    if m <= 0:        # 沒格數可開，視作終止（611實務上不會走到）
        return 0.0, "terminal"
    if b <= 0:        # 沒有實彈（611理論上不會走到，保險用）
        return 0.0, "terminal"

    # 最後一格：直接決定勝負（理性玩家必射對方）
    if m == 1:
        if turn == 0:   # A 的回合
            return 1.0, "opp"     # A 射對手必勝
        else:           # B 的回合
            return 0.0, "B-opp"   # B 射 A，A 必敗

    p = b / m   # 先驗命中率（無額外情報時）
    if turn == 0:
        # A 回合：最大化 A 勝率
        V_same, _ = V(m - 1, b, 0)   # 自射空包 → 保留回合
        V_pass, _ = V(m - 1, b, 1)   # 射對方空包 → 換 B
        EV_self = (1 - p) * V_same
        EV_opp  = p * 1 + (1 - p) * V_pass
        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")
    else:
        # B 回合：最小化 A 勝率
        V_same, _ = V(m - 1, b, 1)   # 自射空包 → 保留回合（仍是B）
        V_pass, _ = V(m - 1, b, 0)   # 射對方空包 → 換 A
        EV_self = p * 1 + (1 - p) * V_same   # 自射命中 => A 勝 (對A=1)
        EV_opp  = p * 0 + (1 - p) * V_pass   # 射對方命中 => A 敗 (對A=0)
        return (EV_self, "B-self") if EV_self <= EV_opp else (EV_opp, "B-opp")

# ===============================
# 放大鏡的後驗機率（只對「當前膛位」生效一次）
# 用放大鏡後，若看到實彈 => p_post=1；看到空包 => p_post=0
# 未使用放大鏡或已使用後/換到新膛位 => 回到先驗 p=b/m
# ===============================
def posterior_p_magnifier(m, b, using_mag_now, see_live, see_blank):
    if using_mag_now:
        if see_live:  return 1.0
        if see_blank: return 0.0
    return b / m

# ===============================
# 🎮 單局遊戲（理性 放大鏡 611）
# ===============================
def simulate_one_game_mag(show_text=True, show_bullets=False):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    bullet_pos = rng.randrange(chambers)   # 唯一實彈
    idx = 0                                # 起始膛位
    turn = 0                               # 0=A, 1=B
    mag_used = False
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})")
        type_out("規則：6格1發實彈(611)，不旋轉。A、B 理性（A最大化/B最小化 A勝率）。\n"
                 "A 有一次放大鏡，『第一回合使用』，僅能看到【當前膛位】是否實/空。\n"
                 "自射空包保留回合；射對方空包換人；只剩最後一格必射對方。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{bullet_pos}")
        time.sleep(0.5)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = 1 if bullet_pos >= idx else 0   # 從當前到末端的實彈數（611 => 0或1）

        # 611：理論上遊戲只會在有人中彈時結束，這裡不另外處理 b==0

        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")

        # =========================
        # 放大鏡（A 第一次回合才用，且只對當前膛位給資訊）
        # =========================
        see_live = False
        see_blank = False
        using_mag_now = (turn == 0) and (not mag_used)
        if using_mag_now:
            mag_used = True
            if idx == bullet_pos:
                see_live = True
                if show_text: type_out("🪞 A 使用放大鏡 → 看到【實彈】！")
            else:
                see_blank = True
                if show_text: type_out("🪞 A 使用放大鏡 → 看到【空包彈】。")

        # =========================
        # 理性決策（用後驗 p_post 取代 p=b/m）
        # =========================
        # 特例：只剩最後一格，理性必射對方
        if m == 1:
            shoot_self = False
            if show_text: type_out("只剩最後一格 → 射向對方！")
        else:
            # 決定 p_post
            p_post = posterior_p_magnifier(m, b, using_mag_now, see_live, see_blank)
            # 讀 DP（無情報）做期望的「狀態值」
            V_same, _ = V(m - 1, b, turn)       # 自射空包 → 保留回合
            V_pass, _ = V(m - 1, b, 1 - turn)   # 射對方空包 → 換人

            if turn == 0:
                # A 最大化 A 勝率
                EV_self = (1 - p_post) * V_same
                EV_opp  = p_post * 1 + (1 - p_post) * V_pass
                shoot_self = EV_self > EV_opp
            else:
                # B 最小化 A 勝率（沿用你的手機版tie-break）
                EV_self = p_post * 1 + (1 - p_post) * V_same
                EV_opp  = p_post * 0 + (1 - p_post) * V_pass
                shoot_self = EV_self <= EV_opp

            if show_text:
                t = "自己" if shoot_self else ("B" if player == "A" else "A")
                type_out(f"🧠 {player} 決策→射{t}")

        # =========================
        # 執行射擊與結果
        # =========================
        target = player if shoot_self else ("B" if player == "A" else "A")
        if idx == bullet_pos:
            # 命中實彈 → 立結
            winner = "B" if target == "A" else "A"
            if show_text:
                type_out("💥 【實彈】！")
                type_out(f"🏆 勝者：{winner}\n")
            return winner, round_count
        else:
            # 空包
            if show_text: type_out("💨 空包。")
            idx = (idx + 1) % chambers
            if shoot_self:
                # 自射空包 → 保留回合
                if show_text: type_out(f"🔁 {player} 射自己空包 → 續回合。")
                continue
            else:
                # 射對方空包 → 換人
                if show_text: type_out(f"🔄 {player} 射對方空包 → 換人。")
                turn ^= 1
                continue

# ===============================
# 蒙地卡羅模擬
# ===============================
def monte_carlo_simulation(trials=500000):
    A_win = 0
    total_rounds = 0
    for _ in range(trials):
        winner, rounds = simulate_one_game_mag(show_text=False)
        if winner == "A":
            A_win += 1
        total_rounds += rounds
    return A_win / trials, 1 - A_win / trials, total_rounds / trials

# ===============================
# 執行
# ===============================
if __name__ == "__main__":
    simulate_one_game_mag(show_text=True, show_bullets=True)
    type_out("\n📈 開始蒙地卡羅模擬（500,000 局）...\n", 0.03)
    s = time.time()
    A_rate, B_rate, avg_rounds = monte_carlo_simulation(500000)
    e = time.time()
    type_out(f"✅ 模擬完成，用時 {e - s:.2f} 秒")
    type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
    type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
    type_out(f"🔸 平均遊戲輪數：約 {avg_rounds:.2f} 輪\n")

