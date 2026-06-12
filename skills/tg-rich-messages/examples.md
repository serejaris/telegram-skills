# tg-rich-messages — Examples

Working HTML and Markdown examples for common rich message patterns.
All examples use `$TELEGRAM_BOT_TOKEN` and `$CHAT_ID` from environment.

---

## 1. Structured report (HTML)

Section heading, paragraph, bordered table, footer.

```python
import json, os, urllib.request

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])

html = """
<h2>Q2 Summary</h2>
<p>Revenue was up across all channels. Key numbers below.</p>
<table bordered striped>
  <caption>Revenue by channel</caption>
  <tr>
    <th align="left">Channel</th>
    <th align="right">Revenue</th>
    <th align="right">vs Q1</th>
  </tr>
  <tr>
    <td>Organic</td>
    <td align="right"><b>$18 400</b></td>
    <td align="right"><mark>+12%</mark></td>
  </tr>
  <tr>
    <td>Paid</td>
    <td align="right"><b>$9 200</b></td>
    <td align="right">+3%</td>
  </tr>
</table>
<footer>Generated automatically · Do not reply</footer>
"""

payload = {"chat_id": CHAT_ID, "rich_message": {"html": html}}
req = urllib.request.Request(
    f"https://api.telegram.org/bot{TOKEN}/sendRichMessage",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as r:
    print(json.load(r))
```

---

## 2. Structured report (Markdown equivalent)

Same content using the `markdown` field:

```python
markdown = """\
## Q2 Summary

Revenue was up across all channels. Key numbers below.

| Channel | Revenue | vs Q1 |
|:--------|--------:|------:|
| Organic | **$18 400** | ==+12%== |
| Paid    | **$9 200**  | +3%  |
"""

payload = {"chat_id": CHAT_ID, "rich_message": {"markdown": markdown}}
```

---

## 3. Collapsible section with nested blocks (HTML)

Use `<details>` for FAQ-style or expandable content.

```python
html = """
<h2>Deployment Notes</h2>
<p>Production deploy completed successfully.</p>

<details open>
  <summary><b>Changelog</b></summary>
  <ul>
    <li>Added rate limiting on /api/submit</li>
    <li>Fixed null pointer in user lookup</li>
    <li>Upgraded dependency to v2.3.1</li>
  </ul>
</details>

<details>
  <summary>Rollback instructions</summary>
  <pre><code class="language-bash">kubectl rollout undo deployment/api</code></pre>
  <p>Then notify #ops-alerts.</p>
</details>
"""
```

---

## 4. Photo collage with caption (HTML)

Collage renders as a grid. Mix photos and videos freely.

```python
html = """
<h3>Event Photos</h3>
<tg-collage>
  <figure>
    <img src="https://example.com/img/event-1.jpg"/>
    <figcaption>Opening ceremony</figcaption>
  </figure>
  <img src="https://example.com/img/event-2.jpg"/>
  <img src="https://example.com/img/event-3.jpg"/>
</tg-collage>
<p>Photos from the annual meetup, June 2026.</p>
"""
```

---

## 5. Slideshow (Markdown)

```python
markdown = """\
### Product Tour

<tg-slideshow>
![](https://example.com/slide-1.jpg "Dashboard overview")
![](https://example.com/slide-2.jpg "Analytics view")
![](https://example.com/slide-3.jpg "Settings panel")
</tg-slideshow>

Swipe through the slides above to explore the product.
"""
```

---

## 6. Map block (HTML)

Static map, no markers. Zoom must be 13–20.

```python
html = """
<h3>Event Location</h3>
<p>The conference takes place at the venue below.</p>
<tg-map lat="48.8566" long="2.3522" zoom="15"/>
<footer>Doors open at 09:00</footer>
"""
```

---

## 7. Math (HTML — inline + block)

```python
html = """
<h2>Black-Scholes Formula</h2>
<p>The price of a European call option is
<tg-math>C = S_0 N(d_1) - K e^{-rT} N(d_2)</tg-math>
where <tg-math>d_1 = \\frac{\\ln(S_0/K) + (r + \\sigma^2/2)T}{\\sigma\\sqrt{T}}</tg-math>.</p>

<p>Variance of returns:</p>
<tg-math-block>\\sigma^2 = \\frac{1}{N-1}\\sum_{i=1}^{N}(r_i - \\bar{r})^2</tg-math-block>
"""
```

---

## 8. Streaming AI reply with thinking block

Only valid for **private chats**. `chat_id` must be an Integer.
After streaming completes, call `sendRichMessage` to persist.

```python
import json, os, urllib.request

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])  # must be integer, not @username

def send_draft(draft_id: int, html: str) -> None:
    payload = {
        "chat_id": CHAT_ID,
        "draft_id": draft_id,
        "rich_message": {"html": html},
    }
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendRichMessageDraft",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req).read()

def send_final(html: str) -> dict:
    payload = {"chat_id": CHAT_ID, "rich_message": {"html": html}}
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendRichMessage",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)

DRAFT_ID = 42  # non-zero; same ID = animated update

# --- Step 1: Show thinking block while LLM generates ---
send_draft(DRAFT_ID, '<tg-thinking>Analyzing your request…</tg-thinking>')

# --- Step 2: Stream partial output ---
partial = "<h3>Analysis</h3><p>The dataset shows a clear upward trend in Q2…"
send_draft(DRAFT_ID, f'<tg-thinking>Writing…</tg-thinking>{partial}')

# --- Step 3: Finalize — REQUIRED, draft expires in 30s ---
final_html = """
<h3>Analysis</h3>
<p>The dataset shows a clear upward trend in Q2, driven by three factors:</p>
<ul>
  <li>Increased organic traffic from SEO improvements</li>
  <li>Successful email re-engagement campaign</li>
  <li>New referral tier launched May 15</li>
</ul>
<footer>Generated by your AI assistant</footer>
"""
result = send_final(final_html)
```

> **Draft rules:** `draft_id` must be non-zero. Calls with the same `draft_id` animate
> into each other. Draft disappears after 30 seconds — always finalize.

---

## 9. Footnotes / references (HTML)

```python
html = """
<h2>Research Findings</h2>
<p>Transformer models outperform RNNs on long sequences
<a href="#fn-vaswani">1</a>
and have become the dominant architecture
<a href="#fn-brown">2</a>.</p>

<hr/>

<tg-reference name="fn-vaswani">Vaswani et al., "Attention Is All You Need", NeurIPS 2017.</tg-reference>
<tg-reference name="fn-brown">Brown et al., "Language Models are Few-Shot Learners", NeurIPS 2020.</tg-reference>
"""
```

---

## 10. editMessageText — switch to rich

Replace an existing text message with a rich one. `text` and `rich_message` are mutually
exclusive — pass exactly one.

```python
payload = {
    "chat_id": CHAT_ID,
    "message_id": 1234,
    "rich_message": {
        "html": "<h3>Updated Report</h3><p>See revised figures below.</p>"
    },
    # do NOT also include "text" — that would error
}
req = urllib.request.Request(
    f"https://api.telegram.org/bot{TOKEN}/editMessageText",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
```

---

## 11. Ordered list with custom numbering (HTML)

```python
html = """
<h3>Setup Steps</h3>
<ol type="1">
  <li>Clone the repository</li>
  <li>Copy <code>.env.example</code> to <code>.env</code></li>
  <li>Run <code>docker compose up -d</code></li>
  <li>Open <a href="http://localhost:3000">localhost:3000</a></li>
</ol>

<h3>Appendix — Roman numerals</h3>
<ol type="i">
  <li>Background theory</li>
  <li>Derivation</li>
  <li>Worked examples</li>
</ol>
"""
```

---

## 12. Anchor navigation (HTML)

```python
html = """
<p>Jump to: <a href="#section-2">Section 2</a> · <a href="#section-3">Section 3</a></p>

<h2>Section 1</h2>
<p>Introduction content…</p>

<a name="section-2"></a>
<h2>Section 2</h2>
<p>Main body content…</p>

<a name="section-3"></a>
<h2>Section 3</h2>
<p>Conclusions…</p>

<p><a href="">Back to top</a></p>
"""
```

> An `<a href="">` with an empty href links back to the top of the message
> (maps to `RichTextAnchorLink` with `anchor_name: ""`).
