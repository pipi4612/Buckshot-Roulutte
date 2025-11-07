import random, time, sys
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
# 動態規劃 (A最大化/B最小化：回傳 A 勝率)
# － 終局：彈光時以命數判勝（轉換器622不會平手）
# ===============================
@lru_cache(None)
def V(m, b, turn, lifeA, lifeB):
    # 正確的終局
    if m <= 0 or b <= 0:
        if lifeA > lifeB:  return 1.0, "terminal"
        if lifeB > lifeA:  return 0.0, "terminal"
        return 0.5, "terminal"  # 保底；本模型理論上用不到

    p = b / m

    if turn == 0:  # A 最大化
        # 射自己（空包保留回合）
        V_same, _ = V(m-1, b, 0, lifeA, lifeB)
        hit_self = V(m-1, b-1, 1, lifeA-1, lifeB)[0] if lifeA > 1 else 0.0
        EV_self = (1 - p) * V_same + p * hit_self

        # 射對方
        hit_opp = V(m-1, b-1, 1, lifeA, lifeB-1)[0] if lifeB > 1 else 1.0
        EV_opp = (1 - p) * V(m-1, b, 1, lifeA, lifeB)[0] + p * hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

    else:         # B 最小化
        # 射自己（若 lifeB==1 且中彈 → A 直接獲勝 = 1.0）
        V_same, _ = V(m-1, b, 1, lifeA, lifeB)
        hit_self = V(m-1, b-1, 0, lifeA, lifeB-1)[0] if lifeB > 1 else 1.0
        EV_self = (1 - p) * V_same + p * hit_self

        # 射對方（= 射 A）
        hit_opp = V(m-1, b-1, 0, lifeA-1, lifeB)[0] if lifeA > 1 else 0.0
        EV_opp = (1 - p) * V(m-1, b, 0, lifeA, lifeB)[0] + p * hit_opp

        return (EV_self, "B-self") if EV_self <= EV_opp else (EV_opp, "B-opp")

# ===============================
# 單局遊戲（轉換器 622）
# ===============================
def simulate_one_game_converter(show_text=True, show_bullets=False):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)
    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 2 顆實彈
    idx = 0
    turn = 0  # 0=A, 1=B
    lifeA, lifeB = 2, 2
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})")
        type_out("規則：6格2發實彈，A、B各2命，不旋轉。")
        type_out("A 有一次轉換器，第一回合使用。A、B 理性（max/min）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}")
        time.sleep(0.4)

    # --- 第一回合：A 使用轉換器（必用） ---
    if show_text:
        type_out(f"🔁 A 使用轉換器 → 翻轉第{idx}膛")
    if idx in live_positions:
        live_positions.remove(idx)
        if show_text:
            type_out("   👉 原本是【實彈】→ 翻成【空包彈】（-1 顆實彈）")
    else:
        live_positions.add(idx)
        if show_text:
            type_out("   👉 原本是【空包彈】→ 翻成【實彈】（+1 顆實彈）")

    # 👇 第一回合決策輸出（與迴圈內格式一致）
    if show_text:
        player = "A"
        shoot_self = False  # 首回合策略為射 B
        t = "自己" if shoot_self else ("B" if player=="A" else "A")
        type_out(f"🧠 {player} 決策→射{t}")

    # --- 轉換後立刻射擊（射 B） ---
    was_live = idx in live_positions
    if was_live:
        live_positions.remove(idx)
        lifeB -= 1
        if show_text:
            type_out(f"💥 A 對 B 開槍！命中！B 剩 {lifeB} 命。")
        if lifeB <= 0:
            if show_text: type_out("🏆 A 勝！")
            return "A", 1
    else:
        if show_text:
            type_out("💨 空包彈。未命中。")

    # --- 進入正常回合 ---
    idx = (idx + 1) % chambers
    turn = 1
    round_count = 1

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        # 彈光 → 以命數判勝
        if b == 0:
            if show_text:
                type_out("🏁 彈光。")
            if lifeA > lifeB:
                if show_text: type_out("🏆 A 勝！")
                return "A", round_count
            elif lifeB > lifeA:
                if show_text: type_out("🏆 B 勝！")
                return "B", round_count
            else:
                # 理論上不會進到這裡；保底給 A
                if show_text: type_out("⚠️ 例外：命數相同（理論上不會發生）")
                return "A", round_count

        if show_text:
            type_out(f"--- 第{round_count}輪 ---")
            type_out(f"目前{player}，膛位{idx}（剩{m}格、{b}實彈）")

        # 理性決策
        _, action = V(m, b, turn, lifeA, lifeB)
        shoot_self = action.endswith("self")
        target = player if shoot_self else ("B" if player == "A" else "A")

        if show_text:
            t = "自己" if shoot_self else ("B" if player=="A" else "A")
            type_out(f"🧠 {player} 決策→射{t}")

        # 開槍
        was_live = idx in live_positions
        if was_live:
            live_positions.remove(idx)
            if target == "A":
                lifeA -= 1
                if show_text: type_out("💥 實彈命中 A！")
                if lifeA <= 0:
                    if show_text: type_out("🏆 B 勝！")
                    return "B", round_count
            else:
                lifeB -= 1
                if show_text: type_out("💥 實彈命中 B！")
                if lifeB <= 0:
                    if show_text: type_out("🏆 A 勝！")
                    return "A", round_count
        else:
            if show_text: type_out("💨 空包。")

        # 換膛與回合
        idx = (idx + 1) % chambers
        if shoot_self:
            if not was_live:
                if show_text: type_out(f"🔁 {player} 射自己空包→續回合。")
                continue
            else:
                turn ^= 1
        else:
            turn ^= 1

# ===============================
# 蒙地卡羅模擬
# ===============================
def monte_carlo_simulation(trials=500000):
    A_win = 0
    total_rounds = 0
    for _ in range(trials):
        w, r = simulate_one_game_converter(show_text=False)
        if w == "A":
            A_win += 1
        total_rounds += r
    return A_win / trials, 1 - (A_win / trials), total_rounds / trials

# ===============================
# 執行
# ===============================
simulate_one_game_converter(show_text=True, show_bullets=True)
type_out("\n📈 開始蒙地卡羅模擬（500,000局）...")
s = time.time()
A_rate, B_rate, avg = monte_carlo_simulation(500000)
e = time.time()
type_out(f"✅ 完成，用時 {e-s:.2f}s")
type_out(f"🔹 A勝率：{A_rate*100:.2f}%")
type_out(f"🔹 B勝率：{B_rate*100:.2f}%")
type_out(f"🔸 平均輪數：約 {avg:.2f} 輪")

