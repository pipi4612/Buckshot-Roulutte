# items/handcuff611.py
import random, time
from engine.type_out import type_out
from engine.dp611 import V

def simulate_handcuff_611(show_text=True, show_bullets=False, anim=True):
    seed = int(time.time() * 1000) % (2**32)
    rng = random.Random(seed)
    chambers = 6
    bullet_pos = rng.randrange(chambers)
    idx, turn = 0, 0
    first_turn = True
    round_count = 0

    if show_text:
        type_out(f"🎲 手銬611 開始（seed={seed})", enable=anim)
        type_out("A 起手必用手銬：連開兩槍都射對方（OO），其後理性。", enable=anim)
        if show_bullets: type_out(f"💣 實彈位置：[{bullet_pos}]", enable=anim)

    while True:
        round_count += 1
        m = chambers - idx
        b = 1 if bullet_pos >= idx else 0

        # A 起手 OO
        if turn == 0 and first_turn:
            first_turn = False
            if show_text: type_out("⛓️ A 使用手銬 → 兩連動（O→O）", enable=anim)
            for i in range(2):
                if idx == bullet_pos:
                    if show_text:
                        type_out("💥 【實彈】！", enable=anim)
                        type_out("🏆 勝者：A\n", enable=anim)
                    return "A", round_count, seed
                else:
                    if show_text: type_out(f"💨 空包（第{i+1}槍）。", enable=anim)
                    idx += 1
            turn = 1
            if show_text: type_out("🔄 手銬回合結束 → 換 B。", enable=anim)
            continue

        # 理性決策
        if m == 1:
            shoot_self = False
            if show_text: type_out("只剩最後一格 → 射向對方！", enable=anim)
        else:
            _, action = V(m, b, turn)
            shoot_self = (action in ("self", "B-self"))
            if show_text:
                t = "自己" if shoot_self else ("B" if turn==0 else "A")
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
