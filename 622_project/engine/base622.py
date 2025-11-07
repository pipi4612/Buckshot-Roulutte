# engine/base622.py
import random
import time
from functools import lru_cache
from engine.type_out import type_out

# ===============================
# 動態規劃：A 最大化勝率 / B 最小化 A 勝率
# ===============================
@lru_cache(None)
def V_base622(m, b, turn, lifeA, lifeB):
    """理性策略值表 V(m,b,turn,lifeA,lifeB) → (A勝率, 動作字串)"""
    if lifeA <= 0 and lifeB <= 0:
        return 0.5, "draw"
    if lifeA <= 0:
        return 0.0, "terminal"
    if lifeB <= 0:
        return 1.0, "terminal"

    if m <= 0 or b <= 0:
        if lifeA > lifeB: return 1.0, "terminal"
        if lifeB > lifeA: return 0.0, "terminal"
        return 0.5, "draw"

    p = b / m

    if turn == 0:  # A 最大化
        V_same, _ = V_base622(m-1, b, 0, lifeA, lifeB)
        hit_self = V_base622(m-1, b-1, 1, lifeA-1, lifeB)[0] if lifeA > 1 else 0.0
        EV_self = (1-p)*V_same + p*hit_self

        V_pass, _ = V_base622(m-1, b, 1, lifeA, lifeB)
        hit_opp = 1.0 if lifeB <= 1 else V_base622(m-1, b-1, 1, lifeA, lifeB-1)[0]
        EV_opp = (1-p)*V_pass + p*hit_opp

        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")

    else:  # B 最小化
        V_same, _ = V_base622(m-1, b, 1, lifeA, lifeB)
        hit_self = 1.0 if lifeB <= 1 else V_base622(m-1, b-1, 0, lifeA, lifeB-1)[0]
        EV_self = (1-p)*V_same + p*hit_self

        V_pass, _ = V_base622(m-1, b, 0, lifeA, lifeB)
        hit_opp = 0.0 if lifeA <= 1 else V_base622(m-1, b-1, 0, lifeA-1, lifeB)[0]
        EV_opp = (1-p)*V_pass + p*hit_opp

        return (EV_self, "B-self") if EV_self <= EV_opp else (EV_opp, "B-opp")

# ===============================
# 無道具單局模擬
# ===============================
def simulate_no_item_622(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)
    chambers = 6
    live_positions = set(rng.sample(range(chambers), 2))
    idx, turn, lifeA, lifeB = 0, 0, 2, 2
    rounds = 0

    if show_text:
        type_out(f"🎲 無道具對局（seed={seed})", enable=anim)
        if show_bullets:
            type_out(f"💣 實彈位置：{sorted(live_positions)}", enable=anim)

    while True:
        rounds += 1
        m = chambers - idx
        b = sum(p >= idx for p in live_positions)
        if b == 0:
            winner = "A" if lifeA > lifeB else ("B" if lifeB > lifeA else "Draw")
            return winner, rounds, seed

        _, action = V_base622(m, b, turn, lifeA, lifeB)
        shoot_self = action.endswith("self")
        target = "A" if (turn==1 and not shoot_self) else "B" if (turn==0 and not shoot_self) else ("A" if turn==0 else "B")

        was_live = idx in live_positions
        if was_live:
            live_positions.remove(idx)
            if target == "A": lifeA -= 1
            else: lifeB -= 1

        if lifeA <= 0: return "B", rounds, seed
        if lifeB <= 0: return "A", rounds, seed

        idx = (idx+1) % chambers
        if shoot_self and not was_live:
            continue
        turn ^= 1
