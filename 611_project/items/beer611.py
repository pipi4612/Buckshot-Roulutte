# items/beer611.py
import random, time
from engine.type_out import type_out
from functools import lru_cache

@lru_cache(None)
def V(m, b, turn):
    if b <= 0:
        return 0.5, "draw"  # 啤酒唯一會退光 → 平手
    if m == 1:
        return (1.0, "opp") if turn == 0 else (0.0, "B-opp")
    p = b / m
    if turn == 0:
        EV_self = (1 - p) * V(m - 1, b, 0)[0]
        EV_opp  = p * 1 + (1 - p) * V(m - 1, b, 1)[0]
        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")
    else:
        EV_self = p * 1 + (1 - p) * V(m - 1, b, 1)[0]
        EV_opp  = (1 - p) * V(m - 1, b, 0)[0]
        return (EV_self, "B-self") if EV_self <= EV_opp else (EV_opp, "B-opp")

def simulate_beer_611(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)
    chambers = 6
    live_pos = rng.randrange(chambers)
    idx, turn = 0, 0
    beer_used = False
    round_count = 0

    if show_text:
        type_out(f"🎲 啤酒611 開始（seed={seed}）", enable=anim)
        type_out("A 第一回合必用啤酒；退當前膛的子彈。退光→平手。", enable=anim)
        if show_bullets: type_out(f"💣 實彈位置：[{live_pos}]", enable=anim)

    while True:
        round_count += 1
        m = chambers - idx
        b = 1 if live_pos >= idx else 0

        if b == 0:
            if show_text: type_out("⚖️ 實彈已退光 → 平手。", enable=anim)
            return "Draw", round_count, seed

        if turn == 0 and not beer_used:
            beer_used = True
            if show_text:
                type_out(f"🍺 A 使用啤酒 → 退掉第 {idx} 格子彈。", enable=anim)
            if idx == live_pos:
                if show_text: type_out("👉 這格是【實彈】→ 平手。\n", enable=anim)
                return "Draw", round_count, seed
            else:
                if show_text: type_out("👉 這格是空包彈，被退掉。", enable=anim)
                idx += 1
                continue

        # 理性決策
        _, action = V(m, b, turn)
        shoot_self = action.endswith("self")
        target_is_A = (turn == 1 and not shoot_self) or (turn == 0 and shoot_self)

        if idx == live_pos:
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
