# items/cigarette611.py
from engine.base611 import simulate_no_item_611

def simulate_cigarette_611(show_text=True, show_bullets=False, anim=True):
    # 等同無道具611（A勝率=50%）
    return simulate_no_item_611(show_text=show_text, show_bullets=show_bullets, anim=anim)
