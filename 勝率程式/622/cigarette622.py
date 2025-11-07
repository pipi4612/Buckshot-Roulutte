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
# 🔢 理性策略表（含雙命＋平手＋香菸觸發條件＋空包階段）
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
def V(m, b, turn, lifeA, lifeB, cigA, last_hit_by):
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
        # 若輪到 B，B 會吃空保留回合到 m=0，阻止 A 回合到來（因此 A 無法回血）
        # 經過空包階段後直接比命
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

    # --- m==1 特例（最後一格一定開，且維持你模板行為）---
    if m == 1:
        if turn == 0:  # A 對 B
            new_lifeB = lifeB - 1
            if new_lifeB <= 0 and lifeA <= 0:
                return 0.5, "opp"
            elif new_lifeB <= 0:
                return 1.0, "opp"
            else:
                # 開完最後一格 → m=0, b-1 ；last_hit_by 與 A 無關
                return V(0, b - 1, 1, lifeA, new_lifeB, cigA, -1)[0], "opp"
        else:  # B 對 A
            new_lifeA = lifeA - 1
            if new_lifeA <= 0 and lifeB <= 0:
                return 0.5, "B-opp"
            elif new_lifeA <= 0:
                return 0.0, "B-opp"
            else:
                # 被 B 打到 → 記錄 last_hit_by = 1；進到 A 的回合，但 m=0 → 立即比命（A無機會再開）
                return V(0, b - 1, 0, new_lifeA, lifeB, cigA, 1)[0], "B-opp"

    # --- 一般情況 ---
    p = b / m  # 命中實彈機率

    if turn == 0:
        # A 射自己：空包留回合；實彈自己 -1 命（last_hit_by=0）
        stay_same = V(m - 1, b, 0, lifeA, lifeB, cigA, -1)[0]
        hit_self = V(m - 1, b - 1, 1, lifeA - 1, lifeB, cigA, 0)[0] if lifeA > 1 else 0.0
        EV_self = (1 - p) * stay_same + p * hit_self

        # A 射對方：空包換 B；實彈 B -1 命
        miss_opp = V(m - 1, b, 1, lifeA, lifeB, cigA, -1)[0]
        hit_opp = V(m - 1, b - 1, 1, lifeA, lifeB - 1, cigA, -1)[0] if lifeB > 1 else 1.0
        EV_opp = (1 - p) * miss_opp + p * hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

    else:
        # B 射自己：空包留回合；實彈自己 -1 命
        stay_same = V(m - 1, b, 1, lifeA, lifeB, cigA, -1)[0]
        hit_Bself = V(m - 1, b - 1, 0, lifeA, lifeB - 1, cigA, -1)[0] if lifeB > 1 else 1.0
        EV_Bself = (1 - p) * stay_same + p * hit_Bself

        # B 射 A：空包換 A；實彈 A -1 命（last_hit_by=1）
        miss_Bopp = V(m - 1, b, 0, lifeA, lifeB, cigA, -1)[0]
        hit_Bopp = V(m - 1, b - 1, 0, lifeA - 1, lifeB, cigA, 1)[0] if lifeA > 1 else 0.0
        EV_Bopp = (1 - p) * miss_Bopp + p * hit_Bopp

        return (EV_Bself, "B-self") if EV_Bself < EV_Bopp else (EV_Bopp, "B-opp")


# ===============================
# 🎮 單局遊戲（6,2,2 + 香菸）
# ===============================
def simulate_one_game(show_text=True, show_bullets=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))  # 兩顆實彈
    idx = 0                 # 不再取模，線性走到 6 結束
    turn = 0                # 0=A, 1=B
    lifeA, lifeB = 2, 2
    cig_used = False
    last_hit_by = -1
    round_count = 0

    if show_text:
        type_out(f"🎲 遊戲開始（seed={seed}）")
        type_out("規則：6格彈匣，2顆實彈，A、B 各有 2 條命，不旋轉。")
        type_out("A 有一次香菸（+1命），只能在『被B射中後』且輪到自己、命=1 時自動使用。理性策略（max/min）。")
        if show_bullets:
            type_out(f"💣 本局實彈位置：{sorted(list(live_positions))}")
        time.sleep(1)

    while True:
        # 終止：膛位走完
        if idx >= chambers:
            if show_text:
                type_out("\n🔚 6 格已全走完，進行生命比較。")
            if lifeA == 1 and lifeB == 1:
                if show_text: type_out("🤝 雙方各剩一命 → 平手。")
                return "Draw", round_count
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("🏆 勝者：" + winner if winner != "Draw" else "🤝 平手")
            return winner, round_count

        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = len([p for p in live_positions if p >= idx])

        if show_text:
            type_out(f"\n--- 第 {round_count} 輪 ---")
            type_out(f"目前輪到 {player}，膛位 {idx}（剩 {m} 格、其中 {b} 顆實彈）")
            type_out(f"❤️ A命={lifeA} | B命={lifeB}")

        # --- 空包階段（b==0）的即時處理 ---
        if b == 0:
            if turn == 0 and (not cig_used) and lifeA == 1 and last_hit_by == 1:
                cig_used = True
                lifeA += 1
                if show_text:
                    type_out("🚬 A 使用香菸（空包階段起手）→ 回復 1 命（A命=2）。")
            # 直接走到結束（把剩餘空包吃完），不逐輪印出
            if show_text:
                type_out("⚖️ 實彈已退光 → 只剩空包，直接比命。")
            # 比命
            if lifeA == 1 and lifeB == 1:
                if show_text: type_out("🤝 雙方各剩一命 → 平手。")
                return "Draw", round_count
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            if show_text:
                type_out("🏆 勝者：" + winner if winner != "Draw" else "🤝 平手")
            return winner, round_count

        # --- A 回合起手：香菸觸發條件 ---
        if turn == 0 and (not cig_used) and lifeA == 1 and last_hit_by == 1:
            cig_used = True
            lifeA += 1
            if show_text:
                type_out("🚬 A 使用香菸 → 回復 1 命（A命=2）。")

        # --- 理性決策 ---
        _, action = V(m, b, turn, lifeA, lifeB, 0 if cig_used else 1, last_hit_by)
        shoot_self = action.endswith("self")
        target = player if shoot_self else ("B" if player == "A" else "A")

        if show_text:
            type_out(f"🧠 {player} 決策：{action}")
            type_out(f"💥 {player} 對 {target} 開槍！")
            time.sleep(0.2)

        # --- 槍擊結果 ---
        was_live = idx in live_positions
        if was_live:
            live_positions.remove(idx)
            if show_text:
                type_out(f"💀 【實彈】命中 {target}！")
            if target == "A":
                lifeA -= 1
                last_hit_by = 1  # 被 B 擊中
                if lifeA <= 0:
                    if show_text:
                        type_out("☠️ A 命歸零，B 勝。\n")
                    return "B", round_count
            else:
                lifeB -= 1
                last_hit_by = -1  # 與 A 無關
                if lifeB <= 0:
                    if show_text:
                        type_out("☠️ B 命歸零，A 勝。\n")
                    return "A", round_count
        else:
            if show_text:
                type_out("💨 空包彈。")
            last_hit_by = -1  # 沒打中 A

        # --- 換膛與回合處理（不取模；走到 6 結束）---
        idx += 1
        if shoot_self:
            if was_live:
                if show_text:
                    type_out(f"💥 {player} 射自己是【實彈】 → 結束回合。")
                if player == "A":
                    last_hit_by = 0
                turn ^= 1
            else:
                if show_text:
                    type_out(f"🔁 {player} 射自己是空包彈 → 保留回合。")
                # 保留回合 → 不切換 turn
                continue
        else:
            turn ^= 1
            if show_text:
                type_out(f"🔄 換 {('B' if turn==1 else 'A')} 行動。")


# ===============================
# 🧮 蒙地卡羅模擬
# ===============================
def monte_carlo(trials=100_000):
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
# 🚀 主程式執行
# ===============================
if __name__ == "__main__":
    simulate_one_game(show_text=True, show_bullets=True)
    type_out("\n📈 開始蒙地卡羅模擬（1,00,000 局）...\n", 0.03)
    start = time.time()
    A_rate, B_rate, D_rate, avg_rounds = monte_carlo(100_000)
    end = time.time()

    type_out(f"✅ 模擬完成，用時 {end - start:.2f} 秒")
    type_out(f"🔹 A 勝率：{A_rate*100:.2f}%")
    type_out(f"🔹 B 勝率：{B_rate*100:.2f}%")
    type_out(f"🔸 平手率：{D_rate*100:.2f}%")
    type_out(f"🔸 平均輪數：約 {avg_rounds:.2f} 輪\n")

    P_eff_A = A_rate / (1 - D_rate) if (1 - D_rate) > 0 else 0.5
    type_out(f"🎯 有結果時 A 勝率（條件勝率）：{P_eff_A*100:.2f}%")
