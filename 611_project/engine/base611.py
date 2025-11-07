# engine/base611.py
import random, time
from .type_out import type_out
from .dp611 import V

def simulate_no_item_611(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)
    chambers = 6
    live_pos = rng.randrange(chambers)
    idx = 0
    turn = 0  # 0=A,1=B
    round_count = 0

    if show_text:
        type_out(f"🎲 無道具611 開始（seed={seed}）", enable=anim)
        type_out("規則：6格1實彈，不旋轉；自射空包保留回合；射對方空包換人；最後一格必射對方。", enable=anim)
        if show_bullets:
            type_out(f"💣 實彈位置：[{live_pos}]", enable=anim)

    while True:
        round_count += 1
        player = "A" if turn == 0 else "B"
        m = chambers - idx
        b = 1 if live_pos >= idx else 0

        if show_text:
            type_out(f"--- 第 {round_count} 輪 ---", enable=anim)
            type_out(f"輪到 {player}，膛位 {idx}（剩 {m} 格、{b} 顆實彈）", enable=anim)

        # 理性決策
        if m == 1:
            shoot_self = False
            if show_text: type_out("只剩最後一格 → 射向對方！", enable=anim)
        else:
            _, action = V(m, b, turn)
            shoot_self = (action in ("self", "B-self"))
            if show_text:
                t = "自己" if shoot_self else ("B" if player=="A" else "A")
                type_out(f"🧠 {player} 決策→射{t}", enable=anim)

        target = player if shoot_self else ("B" if player=="A" else "A")

        # 結果
        if idx == live_pos:
            winner = "B" if target == "A" else "A"
            if show_text:
                type_out("💥 【實彈】！", enable=anim)
                type_out(f"🏆 勝者：{winner}\n", enable=anim)
            return winner, round_count, seed
        else:
            if show_text: type_out("💨 空包。", enable=anim)
            idx += 1
            if shoot_self:
                if show_text: type_out(f"🔁 {player} 射自己空包 → 續回合。", enable=anim)
            else:
                turn ^= 1
                if show_text: type_out(f"🔄 射對方空包 → 換 {('B' if turn==1 else 'A')}。", enable=anim)
