# engine/type_out.py
import sys, time

def type_out(text, delay=0.03, newline=True, enable=True):
    """逐字輸出，可用 enable=False 關掉動畫"""
    if not enable:
        print(text, end="\n" if newline else "")
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        sys.stdout.write("\n")
        sys.stdout.flush()
