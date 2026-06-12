# Heading 1

## Heading 2

### Heading 3

#### Heading 4

##### Heading 5

###### Heading 6

---

## Inline Formatting

Plain paragraph with **bold**, *italic*, ~~strikethrough~~, `inline code`,
==marked text==, and ||spoiler||.

A [link to Telegram](https://telegram.org) and an
[email](mailto:user@example.com) and a [phone](tel:+12345678901).

A [user mention](tg://user?id=123456789).

---

## Code Block

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("world"))
```

```
Plain preformatted block without language tag.
```

---

## Blockquote

> This is a single-line blockquote.

> First line of a multi-line quote.
> Second line continues here.
>
> And a new paragraph inside the quote.

>> Nested blockquote level 2.

---

## Lists

### Unordered

- Item one
- Item two
  - Nested item A
  - Nested item B
    - Deeply nested item
- Item three

### Ordered

1. First item
2. Second item
   1. Sub-item 2.1
   2. Sub-item 2.2
3. Third item

### Task List

- [ ] Unchecked task
- [x] Checked task
- [ ] Another unchecked task

---

## Table

| Name      | Role       | Score |
|:----------|:----------:|------:|
| Alice     | Developer  |    99 |
| **Bob**   | Designer   |    87 |
| `Charlie` | Manager    |    76 |

---

## Divider (already shown above)

---

## Photo Block

![A sample photo](https://picsum.photos/800/600 "Optional caption")

![No caption photo](https://picsum.photos/400/300)

---

## Footnotes

This sentence has a reference[^ref1].

Another sentence references something else[^ref2].

[^ref1]: Definition of the first footnote.
[^ref2]: Definition of the second footnote with **bold** text.

---

## LaTeX Formulas

Inline formula: $E = mc^2$ appears inside text.

Block formula:

$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

---

## HTML Extensions (pass-through in Rich Markdown)

<u>Underlined text</u> and <ins>also underlined</ins>.

Text with <sub>subscript</sub> and <sup>superscript</sup>.

<aside>This is a pull quote.<cite>Famous Author</cite></aside>

<details open><summary>Collapsible section title with **bold**</summary>

### Inside Details

Some content inside the collapsible block.

</details>

---

## Final Paragraph

This concludes the sample fixture covering all supported Markdown mappings:
headings, inline formatting, code blocks, blockquotes, lists (unordered,
ordered, task), tables, dividers, photo blocks, footnotes, LaTeX, and
HTML pass-through extensions.
