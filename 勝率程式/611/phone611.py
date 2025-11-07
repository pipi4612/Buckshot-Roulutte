# 611.py
import random
from collections import defaultdict

from engine.type_out import type_out
from engine.base611 import simulate_no_item_611
from items.converter611 import simulate_converter_611
from items.cigarette611 import simulate_cigarette_611
from items.saw611 import simulate_saw_611
from items.beer611 import simulate_beer_611
from items.handcuff611 import simulate_handcuff_611
from items.magnifier611 import simulate_magnifier_611
from items.phone611 import simulate_phone_611

# ===============================================================
# 各道具模組
# ===============================================================
ITEMS = {
    "converter": simulate_converter_611,  # 轉換器：A不敗；1/6平手、5/6必勝
    "cigarette": simulate_cigarette_611,  # 香菸：等同無道具
    "saw":       simulate_saw_611,        # 鋸子：等同無道具
    "beer":      simulate_beer_611,       # 啤酒：退當前膛；退光→平手
    "handcuff":  simulate_handcuff_611,   # 手銬：A起手OO，後理性
    "magnifier": simulate_magnifier_611,  # 放大鏡：A起手看當前膛
    "phone":     simulate_phone_611,      # 手機：第1回合看 2~5 膛之一（B 不知情）
    "none":      simulate_no_item_611,    # 無道具（備用）
}

ALL_ITEMS = ["converter","cigarette","saw","beer","handcuff","magnifier","phone"]

# ===============================================================
# 權重設定（讓整體 A 勝率 ≈ 65%）
# ===============================================================
# 無條件 A 勝率（平手已折算）：
# beer 0.4997, cigarette 0.5, saw 0.5, phone 0.6968,
# magnifier 0.6816, handcuff 0.6699, converter 0.8333
# 權重（加總=1）：[0.078, 0.078, 0.078, 0.233, 0.233, 0.233, 0.067]
WEIGHTED_POOL = ["beer","cigarette","saw","phone","magnifier","handcuff","converter"]
WEIGHTED_WEIGHTS = [0.078, 0.078, 0.078, 0.233,   0.233,      0.233,      0.067]

# ===============================================================
# 道具選擇
# ===============================================================
def _pick_item(mode: str) -> str:
    """選道具：
       - 'weighted'：依權重抽（整體 A 勝率≈65%）
       - 'random'  ：七種等機率
       - 其餘      ：指定名稱
    """
    if mode == "weighted":
        return random.choices(WEIGHTED_POOL, weights=WEIGHTED_WEIGHTS, k=1)[0]
    if mode == "random":
        return random.choice(ALL_ITEMS)
    return mode

# ===============================================================
# 單局遊戲（可顯示完整過程）
# ===============================================================
def run_one_game(item="weighted", show_text=True, show_bullets=False, anim=True,
                 print_result_dict=False, **kwargs):
    """
    執行單局遊戲：
      - item: 'weighted' / 'random' / 指定道具名稱
      - show_text=True  顯示過程；False 則靜默
      - show_bullets=True 顯示實彈位置（除錯/教學用）
      - anim=True 啟用逐字動畫（僅 show_text=True 時有感）
      - print_result_dict=False 不印 result dict（畫面更乾淨）
    備註：手機可接受額外參數（kwargs）以便未來擴充。
    回傳：dict {item, winner, rounds, seed}
    """
    chosen = _pick_item(item)
    if show_text:
        type_out(f"開始第一次遊玩", enable=anim)
        type_out(f"🎯 本局抽選出的道具為：{chosen}", enable=anim)

    sim = ITEMS[chosen]
    if chosen == "phone":
        winner, rounds, seed = sim(show_text=show_text, show_bullets=show_bullets, anim=anim, **kwargs)
    else:
        winner, rounds, seed = sim(show_text=show_text, show_bullets=show_bullets, anim=anim)

    result = {"item": chosen, "winner": winner, "rounds": rounds, "seed": seed}
    if show_text and print_result_dict:
        print(result)
    return result

# ===============================================================
# 多局統計（預設 10,000 次權重抽選）
# ===============================================================
def run_many_games(trials=10000, item="weighted", show_progress=False, quiet=False, **kwargs):
    """
    進行多局抽選並統計：
      - A 勝率 = A_win / N
      - 平手率 = Draw / N
      - 條件勝率 = A_win / (A_win + B_win)（排除平手）
    參數：
      - trials: 對局數（預設 10000）
      - item: 'weighted' / 'random' / 指定道具
      - show_progress: True 時每 1000 局輸出進度
      - quiet: True 時不輸出起始提示（預設 False 會提示）
      - kwargs: 轉傳給單局（如手機擴充參數）
    輸出：印出總統計並回傳統計 dict。
    """
    total = trials
    A = B = D = 0
    per_item_counts = defaultdict(int)

    if not quiet:
        print(f"\n📈 開始進行 {total} 次權重抽選模擬...\n")

    for t in range(trials):
        # 單局以靜默模式執行
        res = run_one_game(item=item, show_text=False, show_bullets=False, anim=False, **kwargs)
        per_item_counts[res["item"]] += 1

        if res["winner"] == "A":
            A += 1
        elif res["winner"] == "B":
            B += 1
        else:
            D += 1

        if show_progress and (t+1) % 1000 == 0:
            print(f"  -> 進度 {t+1}/{trials}")

    a_rate = A / total
    d_rate = D / total
    cond_rate = A / (A + B) if (A + B) > 0 else 0.0

    # 最終統計輸出
    print("====== 611 模擬結果統計 ======")
    print(f"對局數         : {total}")
    print(f"A 勝率         : {a_rate*100:.2f}%")
    print(f"平手率         : {d_rate*100:.2f}%")
    print(f"A 條件勝率     : {cond_rate*100:.2f}% (排除平手)")
    print("道具抽選分布   :")
    for k in sorted(per_item_counts.keys()):
        v = per_item_counts[k]
        print(f"  - {k:<10s}: {v:6d}  ({v/total*100:5.2f}%)")

    return {
        "trials": total,
        "A_rate": a_rate,
        "Draw_rate": d_rate,
        "A_conditional_rate": cond_rate,
        "per_item_counts": dict(per_item_counts),
        "A": A, "B": B, "Draw": D,
    }

# ===============================================================
# 主執行區：先跑一局完整對局 → 再做 10,000 次權重抽選統計
# ===============================================================
if __name__ == "__main__":
    # 1) 先跑一局：顯示完整過程（含實彈位置、逐字動畫）
    run_one_game(item="weighted", show_text=True, show_bullets=True, anim=True,
                 print_result_dict=False)

    # 2) 再跑 10,000 次權重抽選：只印起始提示與最終統計
    run_many_games(trials=10000, item="weighted", show_progress=False, quiet=False)
