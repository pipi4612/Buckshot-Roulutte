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
# 動態規劃（含雙命和平手規則）
# 狀態：V(m,b,turn, lifeA, lifeB) 回傳 (A勝率, 最佳動作字串)
# ===============================
@lru_cache(None)
def V(m, b, turn, lifeA, lifeB):
    # --- 新增：沒有剩餘膛位（m<=0）時的收斂處理，避免除以 0 ---
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
        # B 射自己（B 想讓 A 勝率最小）
        V_same, _ = V(m - 1, b, 1, lifeA, lifeB)
        hit_Bself = 1.0 if lifeB <= 1 else V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0]
        EV_Bself  = (1 - p) * V_same + p * hit_Bself

        # B 射 A
        V_pass, _ = V(m - 1, b, 0, lifeA, lifeB)
        hit_Bopp  = 0.0 if lifeA <= 1 else V(m - 1, b - 1, 0, lifeA - 1, lifeB)[0]
        EV_Bopp   = (1 - p) * V_pass + p * hit_Bopp

        return (EV_Bself, "B-self") if EV_Bself <= EV_Bopp else (EV_Bopp, "B-opp")

# ===============================
# 手機後驗命中率（A 端使用）
# phone_info = (K, "live"/"blank") 或 None
# ===============================
def posterior_p_phone(idx, m, b, phone_info):
    if phone_info is None:
        return b / m
    K, kind = phone_info
    # 若資訊位置已在過去，資訊失效
    if K < idx:
        return b / m
    # 當前膛就是 K
    if K == idx:
        return 1.0 if kind == "live" else 0.0
    # 未來某膛是 K
    if m <= 1:
        return b / m
    if kind == "live":
        # 一顆實彈已固定在 K，其餘 (m-1) 格有 (b-1) 顆
        return (b - 1) / (m - 1)
    else:
        # K 確定是空，實彈仍是 b 顆分布於 (m-1) 格
        return b / (m - 1)

# ===============================
# 單局遊戲（手機 6-2-2）
# ===============================
def simulate_one_game_phone622(show_text=True, show_bullets=False):
    seed = int(time.time() * 1000) % (2**32)
    rng  = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 2 顆實彈
    idx = 0
    turn = 0  # 0 = A, 1 = B
    lifeA, lifeB = 2, 2
    phone_used = False
    phone_info = None
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed})")
        type_out("規則：6格、2顆實彈、A/B 各 2 命，不旋轉。")
        type_out("A 有一次手機，第一回合使用。A、B 理性（A 最大化、B 最小化 A 勝率）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}")
        time.sleep(0.5)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = sum(1 for p in live_positions if p >= idx)

        # --- 子彈用盡：依生命判勝負或平手 ---
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

        # --- A 第一回合使用手機 ---
        if turn == 0 and not phone_used:
            phone_used = True
            K = rng.choice([2, 3, 4, 5])
            phone_kind = "live" if K in live_positions else "blank"
            phone_info = (K, phone_kind)
            if show_text:
                t = "實彈" if phone_kind == "live" else "空包"
                type_out(f"📱 A 使用手機 → 第 {K} 膛是【{t}】")
                time.sleep(0.2)

        # --- 理性決策（A 用後驗，B 用原始機率） ---
        if turn == 0:
            p_hit = posterior_p_phone(idx, m, b, phone_info)
            # 續局價值（空包分支）
            V_same = V(m - 1, b, 0, lifeA, lifeB)[0]  # 自射空包 → 保留回合
            V_pass = V(m - 1, b, 1, lifeA, lifeB)[0]  # 射對方空包 → 換對方
            # 命中分支
            val_hit_self = 0.0 if lifeA <= 1 else V(m - 1, b - 1, 1, lifeA - 1, lifeB)[0]
            val_hit_opp  = 1.0 if lifeB <= 1 else V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0]
            EV_self = (1 - p_hit) * V_same + p_hit * val_hit_self
            EV_opp  = (1 - p_hit) * V_pass + p_hit * val_hit_opp
            shoot_self = (EV_self > EV_opp)  # 平手偏向射對方
        else:
            p_hit = b / m
            V_same = V(m - 1, b, 1, lifeA, lifeB)[0]  # 自射空包 → 保留回合
            V_pass = V(m - 1, b, 0, lifeA, lifeB)[0]  # 射對方空包 → 換 A
            val_hit_self = 1.0 if lifeB <= 1 else V(m - 1, b - 1, 1, lifeA, lifeB - 1)[0]
            val_hit_opp  = 0.0 if lifeA <= 1 else V(m - 1, b - 1, 0, lifeA - 1, lifeB)[0]
            EV_Bself = (1 - p_hit) * V_same + p_hit * val_hit_self
            EV_Bopp  = (1 - p_hit) * V_pass + p_hit * val_hit_opp
            shoot_self = (EV_Bself < EV_Bopp)  # B 取較小 → 平手偏向射自己

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
def monte_carlo_phone622(trials=1_000_000):
    A = B = D = 0
    total_rounds = 0
    for _ in range(trials):
        result, rounds = simulate_one_game_phone622(show_text=False)
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
simulate_one_game_phone622(show_text=True, show_bullets=True)
type_out("\n📈 開始蒙地卡羅模擬（1,000,000 局）...\n", 0.03)
s = time.time()
A_rate, B_rate, D_rate, avg_rounds = monte_carlo_phone622(1_000_000)
e = time.time()
type_out(f"✅ 完成，用時 {e-s:.2f} 秒")
type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
type_out(f"🔸 平手率：{D_rate*100:.2f}%")
type_out(f"🔸 平均輪數：約 {avg_rounds:.2f} 輪\n")

# 有結果時 A 的條件勝率
P_eff_A = A_rate / (1 - D_rate) if (1 - D_rate) > 0 else 0.5
type_out(f"🎯 有結果時 A 勝率（條件）：{P_eff_A*100:.2f}%")
