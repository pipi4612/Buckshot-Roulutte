# 622.py
# ===============================================================
# 6-2-2 主程式（與 611.py 結構對齊）
# - single：依指定/抽選道具，顯示完整過程（可關動畫/顯示彈位）
# - many  ：先「抽選並示範 1 局」→ 再做 N 次抽選統計（預設 10,000 局）
# ===============================================================

# --- A 方案 path guard：確保優先載入本專案(622_project)的 engine / items ---
import os, sys
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

# 若先前在同個工作階段載過別專案的同名套件，這裡把它們清掉避免衝突
if 'engine' in sys.modules:
    _m = sys.modules['engine']
    _f = getattr(_m, '__file__', '') or ''
    if not os.path.abspath(_f).startswith(os.path.join(THIS_DIR, 'engine')):
        del sys.modules['engine']

if 'items' in sys.modules:
    _m = sys.modules['items']
    _f = getattr(_m, '__file__', '') or ''
    if not os.path.abspath(_f).startswith(os.path.join(THIS_DIR, 'items')):
        del sys.modules['items']
# --- end path guard ---

import random
import argparse
from collections import defaultdict

from engine.type_out import type_out
from engine.base622 import simulate_no_item_622

from items.converter622 import simulate_converter_622
from items.cigarette622 import simulate_cigarette_622
from items.saw622 import simulate_saw_622
from items.beer622 import simulate_beer_622
from items.handcuff622 import simulate_handcuff_622
from items.magnifier622 import simulate_magnifier_622
from items.phone622 import simulate_phone_622

# ===============================================================
# 各道具模組
# ===============================================================
ITEMS = {
    "converter": simulate_converter_622,  # 轉換器：A 第1回合翻轉當前膛後立刻射擊
    "cigarette": simulate_cigarette_622,  # 香菸：A 被 B 射中後、命=1、輪到自己時自動 +1 命（一次）
    "saw":       simulate_saw_622,        # 手鋸：A 第1回合必用，命中對方 -2 命
    "beer":      simulate_beer_622,       # 啤酒：A 第一次行動退當前膛，仍保留回合
    "handcuff":  simulate_handcuff_622,   # 手銬：開局強制 B 射自己一次，之後理性
    "magnifier": simulate_magnifier_622,  # 放大鏡：A 第1回合只查看當前膛；看空自射、看實射對方
    "phone":     simulate_phone_622,      # 手機：A 第1回合看 2~5 膛之一（B 不知情），之後理性
    "none":      simulate_no_item_622,    # 無道具（備用）
}

ALL_ITEMS = ["converter","cigarette","saw","beer","handcuff","magnifier","phone"]

# ===============================================================
# 權重設定（先平均；你之後可依實測 A 勝率微調）
#    WEIGHTED_WEIGHTS 與 WEIGHTED_POOL 對應
# ===============================================================
WEIGHTED_POOL = ["beer","phone","magnifier","converter","handcuff","cigarette","saw"]
WEIGHTED_WEIGHTS = [0.10, 0.05, 0.20, 0.05, 0.20, 0.20, 0.20]

# ===============================================================
# 道具選擇
# ===============================================================
def _pick_item(mode: str) -> str:
    """選道具：
       - 'weighted'：依 WEIGHTED_WEIGHTS 抽
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
def run_one_game(item="weighted", show_text=True, show_bullets=False, anim=True, **kwargs):
    """
    執行單局遊戲：
      - item: 'weighted' / 'random' / 指定道具名稱
      - show_text=True    顯示過程；False 靜默
      - show_bullets=True 顯示實彈位置（除錯/教學用）
      - anim=True         逐字動畫（僅 show_text=True 時有效）
    回傳：dict {item, winner, rounds, seed}
    """
    chosen = _pick_item(item)
    if show_text:
        type_out(f"🎯 本局道具：{chosen}", enable=anim)

    sim = ITEMS[chosen]
    if chosen == "phone":
        winner, rounds, seed = sim(show_text=show_text, show_bullets=show_bullets, anim=anim, **kwargs)
    else:
        winner, rounds, seed = sim(show_text=show_text, show_bullets=show_bullets, anim=anim)

    result = {"item": chosen, "winner": winner, "rounds": rounds, "seed": seed}
    if show_text:
        print(result)
    return result

# ===============================================================
# 多局統計（僅統計，不示範）
# ===============================================================
def run_many_games(trials=100000, item="weighted", show_progress=False, quiet=False, **kwargs):
    """
    進行多局抽選並統計（靜默跑局）：
      - A 勝率 = A_win / N
      - 平手率 = Draw / N
      - A 條件勝率 = A_win / (A_win + B_win)（排除平手）
    """
    total = trials
    A = B = D = 0
    per_item_counts = defaultdict(int)

    if not quiet:
        print(f"📊 開始進行 {total} 次抽選對局（模式：{item}）...\n")

    for t in range(trials):
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

    print("====== 622 模擬結果統計 ======")
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
# 先示範一局，再做多局統計（符合你 611 的流程）
# ===============================================================
def demo_then_many(trials=100000, item="weighted", demo_bullets=True, anim=True, show_progress=False, quiet=False, **kwargs):
    print("🎬 先抽選並示範 1 局：\n")
    run_one_game(item=item, show_text=True, show_bullets=demo_bullets, anim=anim, **kwargs)
    print("\n———————— 進入大量模擬 ————————\n")
    return run_many_games(trials=trials, item=item, show_progress=show_progress, quiet=quiet, **kwargs)

# ===============================================================
# 命令列參數（預設示範局顯示彈位；用 --no-bullets 可關）
# ===============================================================
def _build_arg_parser():
    p = argparse.ArgumentParser(description="622 對局：單局 / 多局統計（先示範一局）")
    p.add_argument("--mode", choices=["single","many"], default="many",
                   help="運行模式：single=單局；many=先示範一局後多局統計（預設 many）")
    p.add_argument("--item", default="weighted",
                   help="道具：weighted/random/或指定名稱（converter/cigarette/saw/beer/handcuff/magnifier/phone）")
    p.add_argument("--trials", type=int, default=100000, help="多局統計試次（預設 100000）")

    # ✅ 預設顯示彈位；若不要，提供 --no-bullets 關閉
    p.add_argument("--bullets", dest="bullets", action="store_true",
                   help="示範局顯示實彈位置（預設開）")
    p.add_argument("--no-bullets", dest="bullets", action="store_false",
                   help="示範局不顯示實彈位置")
    p.set_defaults(bullets=True)

    p.add_argument("--no-anim", action="store_true", help="單局/示範時關閉逐字動畫")
    p.add_argument("--quiet", action="store_true", help="多局時不輸出起始提示")
    p.add_argument("--progress", action="store_true", help="多局顯示每 1000 局進度")
    return p

# ===============================================================
# 主執行區
# ===============================================================
if __name__ == "__main__":
    args = _build_arg_parser().parse_args()

    if args.mode == "single":
        # 只跑一局：預設顯示過程；可用 --bullets 顯示彈位；--no-anim 關動畫
        run_one_game(
            item=args.item,
            show_text=True,
            show_bullets=args.bullets,
            anim=not args.no_anim,
        )
    else:
        # 先抽選並示範 1 局 → 再跑統計（與 611 流程一致）
        demo_then_many(
            trials=args.trials,
            item=args.item,
            demo_bullets=args.bullets,   # 預設 True，會顯示 💣 本局實彈位置
            anim=not args.no_anim,
            show_progress=args.progress,
            quiet=args.quiet,
        )
