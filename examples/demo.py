"""Demo + measurement: one realistic noisy run, then `feed_ai()`.

Prints the human (terminal) output you'd otherwise copy-paste, the compact
feed_ai() block, and the real size reduction. The README numbers come from
running this.

    PYTHONPATH=. python examples/demo.py
"""
import io

import loglucid
from loglucid import get_logger
from loglucid.tokens import estimate


def main():
    # Capture one run as colored terminal output (what you'd paste today).
    term = io.StringIO()
    term.isatty = lambda: True            # force the colored human format
    loglucid.configure(format="human", stream=term, level="DEBUG")
    log = get_logger("checkout")
    log.buffer._dq.clear()

    log.info("server started", port=8080, workers=4)
    for i in range(40):                    # 40 lines of debug noise
        log.debug("cache lookup", key=f"user:{i % 5}", hit=(i % 3 == 0))
    log.info("request received", method="POST", path="/orders", req_id="r-1001")
    log.warn("upstream slow", url="https://pay.internal/charge", ms=812)
    log.warn("retrying upstream", attempt=2)
    try:
        amount = -5
        if amount < 0:
            raise ValueError("amount must be positive")
    except ValueError as e:
        log.error("payment failed", exc=e, order_id=99, req_id="r-1001")

    term_text = term.getvalue()
    feed = log.feed_ai(last=60, max_tokens=2000)

    print("=== feed_ai() output (this is what you paste) ===")
    print(feed)
    t_chars, f_chars = len(term_text), len(feed)
    t_tok, f_tok = estimate(term_text), estimate(feed)
    print("=== size ===")
    print(f"raw terminal logs : {t_chars} chars  ~{t_tok} tokens")
    print(f"feed_ai block     : {f_chars} chars  ~{f_tok} tokens")
    print(f"reduction         : {100 * (1 - f_chars / t_chars):.0f}% chars, "
          f"{100 * (1 - f_tok / t_tok):.0f}% tokens")


if __name__ == "__main__":
    main()
