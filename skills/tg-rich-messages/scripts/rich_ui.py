"""Deterministic Bot API 10.3 UI subset. MIT; no I/O or credentials.

Supported blocks: heading, paragraph, pre, table, details. RichText is
restricted to literal strings. This is intentionally not the full Bot API.
"""
from copy import deepcopy
from urllib.parse import urlsplit

__version__ = '1.3.0'
MAX_TEXT = 32768
MAX_BLOCKS = 500
MAX_DEPTH = 16
STYLES = frozenset(('danger', 'success', 'primary'))


def _text(value):
    if not isinstance(value, str):
        raise ValueError('text must be a literal string')
    try:
        value.encode('utf-8')
    except UnicodeError:
        raise ValueError('text must be valid Unicode') from None
    return len(value)


def _fields(value, required, optional=()):
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - set(optional):
        raise ValueError('unsupported or missing fields')


def _true_fields(value, names):
    for name in names:
        if name in value and value[name] is not True:
            raise ValueError('optional flag must be true or omitted')


def build_blocks_message(blocks, *, skip_entity_detection=True):
    """Return a detached InputRichMessage or raise ValueError.

    Preflight counts literal Unicode code points; official limits say UTF-8
    characters, not bytes. Table rows count toward the 500-block limit.
    This does not replace server/client validation of the complete protocol.
    """
    if type(skip_entity_detection) is not bool:
        raise ValueError('skip_entity_detection must be boolean')
    count = chars = 0

    def visit(items, depth):
        nonlocal count, chars
        if not isinstance(items, list) or not items or depth > MAX_DEPTH:
            raise ValueError('blocks must be nonempty and within nesting limit')
        for block in items:
            if not isinstance(block, dict):
                raise ValueError('block must be an object')
            kind = block.get('type')
            if not isinstance(kind, str):
                raise ValueError('block type must be a string')
            count += 1
            if kind in ('paragraph', 'heading', 'pre'):
                required = {'type', 'text'} | ({'size'} if kind == 'heading' else set())
                _fields(block, required, ('language',) if kind == 'pre' else ())
                chars += _text(block['text'])
                if kind == 'heading' and (type(block['size']) is not int or not 1 <= block['size'] <= 6):
                    raise ValueError('heading size must be 1..6')
                if 'language' in block:
                    _text(block['language'])
            elif kind == 'details':
                _fields(block, {'type', 'summary', 'blocks'}, ('is_open',))
                chars += _text(block['summary'])
                _true_fields(block, ('is_open',))
                visit(block['blocks'], depth + 1)
            elif kind == 'table':
                _fields(block, {'type', 'cells'}, ('caption', 'is_compact', 'is_bordered', 'is_striped'))
                _true_fields(block, ('is_compact', 'is_bordered', 'is_striped'))
                if 'caption' in block:
                    chars += _text(block['caption'])
                rows = block['cells']
                if not isinstance(rows, list) or not rows:
                    raise ValueError('table must contain rows')
                for row in rows:
                    count += 1
                    if not isinstance(row, list) or not row or len(row) > 20:
                        raise ValueError('table row must have 1..20 cells')
                    width = 0
                    for cell in row:
                        _fields(cell, {'align', 'valign'}, ('text', 'is_header', 'colspan', 'rowspan'))
                        if cell['align'] not in ('left', 'center', 'right') or cell['valign'] not in ('top', 'middle', 'bottom'):
                            raise ValueError('invalid table alignment')
                        _true_fields(cell, ('is_header',))
                        if 'text' in cell:
                            chars += _text(cell['text'])
                        for span in ('colspan', 'rowspan'):
                            if span in cell and (type(cell[span]) is not int or cell[span] < 1):
                                raise ValueError('span must be a positive integer')
                        width += cell.get('colspan', 1)
                    if width > 20:
                        raise ValueError('table row spans exceed 20 columns')
            else:
                raise ValueError('unsupported block type')
            if count > MAX_BLOCKS or chars > MAX_TEXT:
                raise ValueError('rich message exceeds documented limits')

    try:
        visit(blocks, 1)
    except RecursionError:
        raise ValueError('cyclic or excessive nesting') from None
    return {'blocks': deepcopy(blocks), 'skip_entity_detection': skip_entity_detection}


def styled_button(text, *, callback_data=None, url=None, copy_text=None, style=None):
    """Return a native InlineKeyboardButton with exactly one supported action.

    RichMessageButton's special 'link' style is not an inline keyboard style.
    copy_text is a literal string and becomes CopyTextButton {'text': ...}.
    """
    if not _text(text):
        raise ValueError('button text must not be empty')
    if style is not None and (not isinstance(style, str) or style not in STYLES):
        raise ValueError('unsupported inline button style')
    actions = [(key, value) for key, value in (('callback_data', callback_data), ('url', url), ('copy_text', copy_text)) if value is not None]
    if len(actions) != 1:
        raise ValueError('button requires exactly one action')
    key, value = actions[0]
    length = _text(value)
    if key == 'callback_data' and not 1 <= len(value.encode('utf-8')) <= 64:
        raise ValueError('callback_data must be 1..64 UTF-8 bytes')
    if key == 'copy_text' and not 1 <= length <= 256:
        raise ValueError('copy_text must be 1..256 characters')
    if key == 'url':
        if any(c.isspace() or ord(c) < 32 for c in value):
            raise ValueError('invalid button URL')
        try:
            parsed = urlsplit(value)
        except ValueError:
            raise ValueError('invalid button URL') from None
        if parsed.scheme not in ('http', 'https', 'tg') or not parsed.netloc:
            raise ValueError('button URL must use HTTP, HTTPS or tg')
    result = {'text': text, key: {'text': value} if key == 'copy_text' else value}
    if style is not None:
        result['style'] = style
    return result
