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
# 動態規劃（含雙命與平手規則）
# 狀態：V(m,b,turn, lifeA, lifeB) → (A勝率, 最佳動作字串)
# ===============================
@lru_cache(None)
def V(m, b, turn, lifeA, lifeB):
    # --- 沒剩膛位（避免除以 0）→ 按生命比較/平手收斂 ---
    if m <= 0:
        if lifeA > lifeB:
            return 1.0, "terminal"
        elif lifeB > lifeA:
            return 0.0, "terminal"
        else:
            return 0.5, "draw"

    # --- 子彈用盡 ---
    if b <= 0:
        if lifeA > lifeB:
            return 1.0, "terminal"
        elif lifeB > lifeA:
            return 0.0, "terminal"
        else:
            return 0.5, "draw"

    # --- 生命歸零（保險）---
    if lifeA <= 0 and lifeB <= 0:
        return 0.5, "draw"
    if lifeA <= 0:
        return 0.0, "terminal"
    if lifeB <= 0:
        return 1.0, "terminal"

    # --- 最後一格（m == 1）---
    if m == 1:
        if turn == 0:  # A 行動
            new_lifeB = lifeB - 1
            if new_lifeB <= 0:
                return 1.0, "opp"
            else:
                # 打中對方但未死 → 子彈用盡，進入 b=0 的生命比較
                return V(0, 0, 1, lifeA, new_lifeB)[0], "opp"
        else:          # B 行動
            new_lifeA = lifeA - 1
            if new_lifeA <= 0:
                return 0.0, "B-opp"
            else:
                return V(0, 0, 0, new_lifeA, lifeB)[0], "B-opp"

    # --- 一般情況 ---
    p = b / m
    if turn == 0:
        # A 射自己
        V_same, _ = V(m - 1, b, 0, lifeA, lifeB)
        hit_self = 0.0 if lifeA <= 1 else V(m - 1, b - 1, 1, lifeA - 1, lifeB)[0]
        EV_self = (1 - p) * V_same + p * hit_self

        # A 射對方
        V_pass, _ = V(m - 1, b, 1, lifeA, lifeB)
        hit_opp = 1.0 if lifeB <= 1 else V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0]
        EV_opp  = (1 - p) * V_pass + p * hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")
    else:
        # B 射自己（最小化 A 勝率）
        V_same, _ = V(m - 1, b, 1, lifeA, lifeB)
        hit_Bself = 1.0 if lifeB <= 1 else V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0]
        EV_Bself  = (1 - p) * V_same + p * hit_Bself

        # B 射 A
        V_pass, _ = V(m - 1, b, 0, lifeA, lifeB)
        hit_Bopp  = 0.0 if lifeA <= 1 else V(m - 1, b - 1, 0, lifeA - 1, lifeB)[0]
        EV_Bopp   = (1 - p) * V_pass + p * hit_Bopp

        return (EV_Bself, "B-self") if EV_Bself <= EV_Bopp else (EV_Bopp, "B-opp")

# ===============================
# 🎮 單局（放大鏡 6-2-2）
# A 第一回合必用放大鏡：看當前膛（idx=0）是實或空
#   看見實 → 射對方；看見空 → 射自己（保留回合）
# 後續一律用 DP 理性決策（與啤酒模板一致）
# ===============================
def simulate_one_game_magnifier622(show_text=True, show_bullets=False):
    seed = int(time.time() * 1000) % (2**32)
    rng  = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 2 顆實彈
    idx = 0
    turn = 0  # 0 = A, 1 = B
    lifeA, lifeB = 2, 2
    mag_used = False
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})")
        type_out("規則：6格、2顆實彈、A/B 各 2 命，不旋轉。")
        type_out("A 有一次放大鏡，第一回合使用，只查看當前膛位內容。")
        type_out("之後雙方皆依理性策略（A 最大化、B 最小化 A 勝率）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}")
        time.sleep(0.5)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = sum(1 for p in live_positions if p >= idx)

        # --- 子彈用盡：生命比較或平手 ---
        if b == 0:
            if show_text:
                type_out("⚖️ 實彈退光。")
                if lifeA > lifeB:
                    type_out("🏆 勝者：A（生命較多）")
                elif lifeB > lifeA:
                    type_out("🏆 勝者：B（生命較多）")
                else:
                    type_out("🤝 雙方生命相同 → 平手")
            if lifeA > lifeB:
                return "A", round_count
            elif lifeB > lifeA:
                return "B", round_count
            else:
                return "Draw", round_count

        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")
            type_out(f"❤️ A命={lifeA} | B命={lifeB}")

        # --- A 第一回合使用放大鏡（只看 idx=0 當前膛）---
        if turn == 0 and not mag_used:
            mag_used = True
            saw_live = (idx in live_positions)
            if show_text:
                t = "實彈" if saw_live else "空包"
                type_out(f"🪞 A 使用放大鏡 → 當前膛位是【{t}】")
                time.sleep(0.2)
            # 放大鏡當步決策：實→射對方；空→射自己
            shoot_self = (not saw_live)
        else:
            # --- 理性決策（與啤酒模板一致）---
            if turn == 0:
                # A：最大化 A 勝率
                V_same = V(m - 1, b, 0, lifeA, lifeB)[0]  # 自射空包 → 保留回合
                V_pass = V(m - 1, b, 1, lifeA, lifeB)[0]  # 射對方空包 → 換對方
                # 命中分支
                val_hit_self = 0.0 if lifeA <= 1 else V(m - 1, b - 1, 1, lifeA - 1, lifeB)[0]
                val_hit_opp  = 1.0 if lifeB <= 1 else V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0]
                p = b / m
                EV_self = (1 - p) * V_same + p * val_hit_self
                EV_opp  = (1 - p) * V_pass + p * val_hit_opp
                shoot_self = (EV_self > EV_opp)  # 平手偏向射對方
            else:
                # B：最小化 A 勝率
                V_same = V(m - 1, b, 1, lifeA, lifeB)[0]  # 自射空包 → 保留回合
                V_pass = V(m - 1, b, 0, lifeA, lifeB)[0]  # 射對方空包 → 換 A
                val_hit_self = 1.0 if lifeB <= 1 else V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0]
                val_hit_opp  = 0.0 if lifeA <= 1 else V(m - 1, b - 1, 0, lifeA - 1, lifeB)[0]
                p = b / m
                EV_Bself = (1 - p) * V_same + p * val_hit_self
                EV_Bopp  = (1 - p) * V_pass + p * val_hit_opp
                shoot_self = (EV_Bself < EV_Bopp)  # 平手偏向射自己

        if show_text:
            t = "自己" if shoot_self else ("B" if player == "A" else "A")
            type_out(f"🧠 {player} 決策 → 射{t}")

        # --- 槍擊結果 ---
        was_live = (idx in live_positions)
        if was_live:
            # 移除該發實彈
            live_positions.remove(idx)
            if show_text:
                who = "自己" if shoot_self else ("A" if player == "B" else "B")
                type_out(f"💥 【實彈】命中 {who}！")
            if shoot_self:
                if player == "A":
                    lifeA -= 1
                    if lifeA <= 0:
                        if show_text: type_out("☠️ A 命歸零，B 勝。\n")
                        return "B", round_count
                else:
                    lifeB -= 1
                    if lifeB <= 0:
                        if show_text: type_out("☠️ B 命歸零，A 勝。\n")
                        return "A", round_count
                # 自射中彈 → 回合結束換對方
                idx = (idx + 1) % chambers
                turn ^= 1
                continue
            else:
                # 射對方命中
                if player == "A":
                    lifeB -= 1
                    if lifeB <= 0:
                        if show_text: type_out("☠️ B 命歸零，A 勝。\n")
                        return "A", round_count
                else:
                    lifeA -= 1
                    if lifeA <= 0:
                        if show_text: type_out("☠️ A 命歸零，B 勝。\n")
                        return "B", round_count
                idx = (idx + 1) % chambers
                turn ^= 1
                continue
        else:
            if show_text:
                type_out("💨 空包。")
            idx = (idx + 1) % chambers
            if shoot_self:
                if show_text: type_out(f"🔁 {player} 射自己空包 → 保留回合。\n")
                continue
            else:
                if show_text: type_out(f"🔄 {player} 射對方空包 → 換人。\n")
                turn ^= 1
                continue

# ===============================
# 蒙地卡羅模擬
# ===============================
def monte_carlo_magnifier622(trials=1_000_000):
    A = B = D = 0
    total_rounds = 0
    for _ in range(trials):
        result, rounds = simulate_one_game_magnifier622(show_text=False)
        if result == "A":
            A += 1
        elif result == "B":
            B += 1
        else:
            D += 1
        total_rounds += rounds
    return A/trials, B/trials, D/trials, total_rounds/trials

# ===============================
# 執行
# ===============================
simulate_one_game_magnifier622(show_text=True, show_bullets=True)
type_out("\n📈 開始蒙地卡羅模擬（1,000,000 局）...\n", 0.03)
s = time.time()
A_rate, B_rate, D_rate, avg_rounds = monte_carlo_magnifier622(1_000_000)
e = time.time()
type_out(f"✅ 完成，用時 {e-s:.2f} 秒")
type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
type_out(f"🔸 平手率：{D_rate*100:.2f}%")
type_out(f"🔸 平均輪數：約 {avg_rounds:.2f} 輪\n")

# 有結果時 A 的條件勝率
P_eff_A = A_rate / (1 - D_rate) if (1 - D_rate) > 0 else 0.5
type_out(f"🎯 有結果時 A 勝率（條件）：{P_eff_A*100:.2f}%")
