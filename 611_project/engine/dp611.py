# engine/dp611.py
from functools import lru_cache

@lru_cache(None)
def V(m, b, turn):
    """
    無道具 611 的價值函數：
    狀態：m=剩餘格數(含當前)，b∈{0,1}，turn=0(A)/1(B)
    回傳：(A勝率, 動作字串)；A: "opp"/"self"，B: "B-opp"/"B-self"
    """
    # 保險邊界（理論上 611 對局不會自然走到）
    if b <= 0 or m <= 0:
        return 0.0, "terminal"

    # 最後一格：理性必射對方
    if m == 1:
        return (1.0, "opp") if turn == 0 else (0.0, "B-opp")

    p = b / m  # 命中率
    if turn == 0:
        V_same, _ = V(m - 1, b, 0)  # 自射空包 → 保留回合
        V_pass, _ = V(m - 1, b, 1)  # 射對方空包 → 換 B
        EV_self = (1 - p) * V_same
        EV_opp  = p * 1.0 + (1 - p) * V_pass
        return (EV_opp, "opp") if EV_opp >= EV_self else (EV_self, "self")
    else:
        V_same, _ = V(m - 1, b, 1)  # B自射空包 → 保留回合
        V_pass, _ = V(m - 1, b, 0)  # B射對方空包 → 換 A
        EV_self = p * 1.0 + (1 - p) * V_same   # 自射命中 → A勝
        EV_opp  = p * 0.0 + (1 - p) * V_pass   # 射對方命中 → A敗
        return (EV_self, "B-self") if EV_self <= EV_opp else (EV_opp, "B-opp")
