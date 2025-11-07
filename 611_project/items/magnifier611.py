# items/magnifier611.py
import random, time
from engine.type_out import type_out
from engine.dp611 import V

def simulate_magnifier_611(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)
    chambers = 6
    bullet_pos = rng.randrange(chambers)
    idx, turn = 0, 0
    mag_used = False
    round_count = 0

    if show_text:
        type_out(f"🎲 放大鏡611 開始（seed={seed})", enable=anim)
        type_out("A 第一回合用放大鏡，只看【當前膛位】實/空；僅當前一槍生效。", enable=anim)
        if show_bullets: type_out(f"💣 實彈位置：[{bullet_pos}]", enable=anim)

    while True:
        round_count += 1
        player_A = (turn == 0)
        m = chambers - idx
        b = 1 if bullet_pos >= idx else 0

        # 放大鏡資訊
        using_mag = (player_A and not mag_used)
        if using_mag:
            mag_used = True
            saw_live = (idx == bullet_pos)
            if show_text:
                type_out(f"🪞 放大鏡 → 看到：{'實彈' if saw_live else '空包彈'}", enable=anim)
            p_post = 1.0 if saw_live else 0.0
        else:
            p_post = b / m

        # 決策
        if m == 1:
            shoot_self = False
            if show_text: type_out("只剩最後一格 → 射向對方！", enable=anim)
        else:
            V_same, _ = V(m - 1, b, turn)
            V_pass, _ = V(m - 1, b, 1 - turn)
            if player_A:
                EV_self = (1 - p_post) * V_same
                EV_opp  = p_post * 1 + (1 - p_post) * V_pass
                shoot_self = EV_self > EV_opp
            else:
                EV_self = p_post * 1 + (1 - p_post) * V_same
                EV_opp  = (1 - p_post) * V_pass
                shoot_self = EV_self <= EV_opp
            if show_text:
                t = "自己" if shoot_self else ("B" if player_A else "A")
                type_out(f"🧠 決策→射{t}", enable=anim)

        # 結果
        target_is_A = (turn == 1 and not shoot_self) or (turn == 0 and shoot_self)
        if idx == bullet_pos:
            winner = "B" if target_is_A else "A"
            if show_text:
                type_out("💥 【實彈】！", enable=anim)
                type_out(f"🏆 勝者：{winner}\n", enable=anim)
            return winner, round_count, seed
        else:
            if show_text: type_out("💨 空包。", enable=anim)
            idx += 1
            if shoot_self:
                if show_text: type_out("🔁 自射空包 → 保留回合。", enable=anim)
            else:
                turn ^= 1
                if show_text: type_out("🔄 射對方空包 → 換人。", enable=anim)
