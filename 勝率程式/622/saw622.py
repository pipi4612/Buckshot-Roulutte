import random
import time
import sys
from functools import lru_cache

# ===============================
# 🖋️ 安全修正版 type_out（不重複輸出）
# ===============================
def type_out(text, delay=0.03, newline=True):
    s = text if isinstance(text, str) else str(text)
    for ch in s:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        sys.stdout.write("\n")
        sys.stdout.flush()


# ===============================
# 🔢 理性策略表（無手鋸狀態；第一回合已強制用掉）
# ===============================
@lru_cache(None)
def V(m, b, turn, lifeA, lifeB):
    # --- 終局：有人沒命 ---
    if lifeA <= 0 and lifeB <= 0:
        return 0.5, "draw"
    if lifeA <= 0:
        return 0.0, "terminal"
    if lifeB <= 0:
        return 1.0, "terminal"

    # --- 沒剩膛位 or 沒剩實彈：只剩空包 → 直接比命 ---
    if m <= 0 or b <= 0:
        if lifeA == lifeB:
            return 0.5, "draw"
        return (1.0, "terminal") if lifeA > lifeB else (0.0, "terminal")

    p = b / m  # 命中實彈機率

    if turn == 0:
        # A 動作：self, opp
        keep_turn = V(m - 1, b, 0, lifeA, lifeB)[0]
        hit_self = V(m - 1, b - 1, 1, lifeA - 1, lifeB)[0] if lifeA > 1 else 0.0
        EV_self = (1 - p) * keep_turn + p * hit_self

        miss_opp = V(m - 1, b, 1, lifeA, lifeB)[0]
        hit_opp = V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0] if lifeB > 1 else 1.0
        EV_opp = (1 - p) * miss_opp + p * hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

    else:
        # B 動作：self, opp
        keep_Bturn = V(m - 1, b, 1, lifeA, lifeB)[0]
        hit_Bself = V(m - 1, b - 1, 0, lifeA, lifeB - 1)[0] if lifeB > 1 else 1.0
        EV_Bself = (1 - p) * keep_Bturn + p * hit_Bself

        miss_Bopp = V(m - 1, b, 0, lifeA, lifeB)[0]
        hit_Bopp = V(m - 1, b - 1, 0, lifeA - 1, lifeB)[0] if lifeA > 1 else 0.0
        EV_Bopp = (1 - p) * miss_Bopp + p * hit_Bopp

        return (EV_Bself, "B-self") if EV_Bself <= EV_Bopp else (EV_Bopp, "B-opp")


# ===============================
# 🎮 單局遊戲（6,2,2 + 手鋸；第一回合強制用手鋸）
# ===============================
def simulate_one_game(show_text=True, show_bullets=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))
    idx = 0
    turn = 0
    lifeA, lifeB = 2, 2
    round_count = 0
    first_round_done = False

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）")
        type_out("規則：6格彈匣，2顆實彈，A、B 各有 2 條命，不旋轉。")
        type_out("A 有一次手鋸（短槍管）：第一回合使用 並一定射對方。")
        type_out("若命中，傷害=2 → B 直接死亡；打空也會消耗（本局只這一回強化）。")
        type_out("雙方理性策略（A 最大化勝率、B 最小化 A 勝率）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}")
        time.sleep(1)

    while True:
        if idx >= chambers or not any(p >= idx for p in live_positions):
            if show_text:
                type_out("\n⚖️ 所有彈膛已射完，比較生命判勝。")
            if lifeA == lifeB:
                if show_text:
                    type_out("🤝 雙方生命相同 → 平手。")
                return "Draw", round_count
            winner = "A" if lifeA > lifeB else "B"
            if show_text:
                type_out(f"🏆 勝者：{winner}")
            return winner, round_count

        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        if show_text:
            type_out(f"\n--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")
            type_out(f"❤️ A命={lifeA} | B命={lifeB}")

        # 第一回合：A 強制用手鋸
        if not first_round_done and turn == 0:
            action = "saw-opp"
            first_round_done = True
        else:
            _, action = V(m, b, turn, lifeA, lifeB)

        shoot_self = action.endswith("self")
        use_saw = (action == "saw-opp")
        target = ("B" if player == "A" else "A") if not shoot_self else player

        if show_text:
            if use_saw:
                type_out("🪚 A 使用手鋸（短槍管）：這一槍若命中，B 直接死亡！")
            type_out(f"🧠 {player} 決策：{action}")
            type_out(f"💥 {player} 對 {target} 開槍！")

        was_live = idx in live_positions
        if was_live:
            live_positions.remove(idx)
            if show_text:
                type_out(f"💀 【實彈】命中 {target}！")
            if target == "A":
                lifeA -= 1
                if lifeA <= 0:
                    if show_text:
                        type_out("☠️ A 命歸零，B 勝。")
                    return "B", round_count
            else:
                lifeB -= (2 if use_saw else 1)
                if lifeB <= 0:
                    if show_text:
                        if use_saw:
                            type_out("💥 手鋸重擊 -2 命 → B 死亡。A 勝！")
                        else:
                            type_out("☠️ B 命歸零，A 勝。")
                    return "A", round_count
        else:
            if show_text:
                type_out("💨 空包彈。")

        idx += 1
        if shoot_self:
            if was_live:
                turn ^= 1
            else:
                if show_text:
                    type_out("🔁 自射空包 → 保留回合。")
                continue
        else:
            turn ^= 1
            if show_text:
                type_out(f"🔄 換 {('B' if turn==1 else 'A')} 行動。")


# ===============================
# 🧮 蒙地卡羅模擬（第一回合必用手鋸）
# ===============================
def monte_carlo(trials=300000):
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
# 🚀 主程式
# ===============================
if __name__ == "__main__":
    simulate_one_game(show_text=True, show_bullets=True)

    type_out("\n📈 開始蒙地卡羅（300,000 局）...\n", 0.03)
    start = time.time()
    A_rate, B_rate, D_rate, avg_rounds = monte_carlo(300000)
    end = time.time()

    type_out(f"✅ 模擬完成，用時 {end - start:.2f} 秒")
    type_out(f"🔹 A 勝率：{A_rate * 100:.2f}%")
    type_out(f"🔹 B 勝率：{B_rate * 100:.2f}%")
    type_out(f"🔸 平手率：{D_rate * 100:.2f}%")
    type_out(f"🔸 平均輪數：約 {avg_rounds:.2f} 輪\n")

    P_eff_A = A_rate / (1 - D_rate) if (1 - D_rate) > 0 else 0.5
    type_out(f"🎯 有結果時 A 勝率（條件勝率）：{P_eff_A * 100:.2f}%")
