# items/phone611.py
import random, time
from engine.type_out import type_out
from engine.dp611 import V

def _posterior_p_phone(idx, m, b, phone_info):
    if phone_info is None:
        return b / m
    K, kind = phone_info
    if K < idx:
        return b / m
    if K == idx:
        return 1.0 if kind == "live" else 0.0
    # K > idx（未來某膛；611 只有 1 發）
    if kind == "live":
        return 0.0            # 實彈在未來 → 當前不會中
    else:
        return b / (m - 1)    # 排除 1 個空包位置

def simulate_phone_611(show_text=True, show_bullets=False, anim=True):
    """手機611：A 第1回合一次性查看第2~5膛的實/空；B 不知情。"""
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)

    chambers = 6
    bullet_pos = rng.randrange(chambers)  # 0..5
    idx, turn = 0, 0                      # 不旋轉 → 只遞增
    phone_used = False
    phone_info = None
    round_count = 0

    if show_text:
        type_out(f"🎲 手機611 開始（seed={seed})", enable=anim)
        type_out("規則：6格1發，不旋轉；A 第1回合用手機查看第2~5膛之一（實/空）。B 不知情。", enable=anim)
        type_out("自射空包保留回合；射對方空包換人；最後一格必射對方。", enable=anim)
        if show_bullets:
            type_out(f"💣 實彈位置：[{bullet_pos}]", enable=anim)

    while True:
        round_count += 1
        playerA = (turn == 0)
        m = chambers - idx
        b = 1 if bullet_pos >= idx else 0

        if show_text:
            p = "A" if playerA else "B"
            type_out(f"--- 第 {round_count} 輪 ---", enable=anim)
            type_out(f"輪到 {p}，膛位 {idx}（剩 {m} 格、{b} 顆實彈）", enable=anim)

        # A 第一次行動：手機揭露 K ∈ {2,3,4,5}
        if playerA and not phone_used:
            phone_used = True
            K = rng.choice([2, 3, 4, 5])
            phone_kind = "live" if (K == bullet_pos) else "blank"
            phone_info = (K, phone_kind)
            if show_text:
                t = "實彈" if phone_kind == "live" else "空包彈"
                type_out(f"📱 手機 → 第 {K} 膛是【{t}】", enable=anim)

        # 決策
        if m == 1:
            shoot_self = False
            if show_text: type_out("只剩最後一格 → 射向對方！", enable=anim)
        else:
            p_post = _posterior_p_phone(idx, m, b, phone_info) if playerA else (b / m)
            V_same, _ = V(m - 1, b, turn)       # 自射空包 → 保留回合
            V_pass, _ = V(m - 1, b, 1 - turn)   # 射對方空包 → 換人
            if playerA:
                EV_self = (1 - p_post) * V_same
                EV_opp  = p_post * 1 + (1 - p_post) * V_pass
                shoot_self = (EV_self > EV_opp)     # A：>= 偏向射對方 → 這裡用 >
            else:
                EV_self = p_post * 1 + (1 - p_post) * V_same
                EV_opp  = (1 - p_post) * V_pass
                shoot_self = (EV_self <= EV_opp)    # B：<= 偏向自射
            if show_text:
                t = "自己" if shoot_self else ("B" if playerA else "A")
                type_out(f"🧠 決策→射{t}", enable=anim)

        # 執行射擊
        target_is_A = (turn == 1 and not shoot_self) or (turn == 0 and shoot_self)
        if idx == bullet_pos:
            winner = "B" if target_is_A else "A"
            if show_text:
                type_out("💥 【實彈】！", enable=anim)
                type_out(f"🏆 勝者：{winner}\n", enable=anim)
            return winner, round_count, seed
        else:
            if show_text: type_out("💨 空包。", enable=anim)
            idx += 1  # 不要用 % chambers（不旋轉）
            if shoot_self:
                if show_text: type_out("🔁 自射空包 → 續回合。", enable=anim)
            else:
                turn ^= 1
                if show_text: type_out("🔄 射對方空包 → 換人。", enable=anim)
