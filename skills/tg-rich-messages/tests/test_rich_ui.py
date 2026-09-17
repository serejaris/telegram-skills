import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('rich_ui', Path(__file__).parents[1] / 'scripts/rich_ui.py')
ui = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ui)


def cell(text='value', **extra):
    return {'text': text, 'align': 'left', 'valign': 'top', **extra}


class RichUI(unittest.TestCase):
    def test_literal_json_detached_and_compact_table(self):
        raw = '{"x":"<script>&\\n😀"}'
        blocks = [{'type': 'heading', 'text': 'Result', 'size': 2},
                  {'type': 'table', 'is_compact': True, 'cells': [[cell('Label', is_header=True), cell('Value')]]},
                  {'type': 'details', 'summary': 'API', 'blocks': [{'type': 'pre', 'text': raw, 'language': 'json'}]}]
        result = ui.build_blocks_message(blocks)
        self.assertIs(result['skip_entity_detection'], True)
        self.assertEqual(result['blocks'][2]['blocks'][0]['text'], raw)
        blocks[1]['cells'][0][0]['text'] = 'changed'
        self.assertEqual(result['blocks'][1]['cells'][0][0]['text'], 'Label')

    def test_text_exact_boundary_including_nested_summary(self):
        ui.build_blocks_message([{'type': 'pre', 'text': '😀' * 32768}])
        with self.assertRaises(ValueError):
            ui.build_blocks_message([{'type': 'details', 'summary': 'x', 'blocks': [{'type': 'pre', 'text': 'x' * 32768}]}])

    def test_table_rows_count_toward_blocks(self):
        ui.build_blocks_message([{'type': 'table', 'cells': [[cell()]] * 499}])
        with self.assertRaises(ValueError):
            ui.build_blocks_message([{'type': 'table', 'cells': [[cell()]] * 500}])

    def test_nesting_and_cycle(self):
        block = {'type': 'paragraph', 'text': 'leaf'}
        for _ in range(15):
            block = {'type': 'details', 'summary': 's', 'blocks': [block]}
        ui.build_blocks_message([block])
        with self.assertRaises(ValueError):
            ui.build_blocks_message([{'type': 'details', 'summary': 's', 'blocks': [block]}])
        cycle = {'type': 'details', 'summary': 's'}
        cycle['blocks'] = [cycle]
        with self.assertRaises(ValueError):
            ui.build_blocks_message([cycle])

    def test_malformed_block_matrix(self):
        bad = [None, [], [None], [{'type': []}], [{'type': 'thinking', 'text': 'x'}],
               [{'type': 'heading', 'text': 'x', 'size': True}], [{'type': 'heading', 'text': 'x', 'size': 7}],
               [{'type': 'paragraph', 'text': {'type': 'bold', 'text': 'x'}}],
               [{'type': 'paragraph', 'text': '\ud800'}], [{'type': 'pre', 'text': 'x', 'html': 'x'}],
               [{'type': 'details', 'summary': 's', 'blocks': [], 'is_open': False}],
               [{'type': 'table', 'cells': [[{'text': 'missing alignment'}]]}],
               [{'type': 'table', 'cells': [[cell(align='diagonal')]]}],
               [{'type': 'table', 'cells': [[cell()]*21]}],
               [{'type': 'table', 'cells': [[cell(colspan=20), cell()]]}],
               [{'type': 'table', 'cells': [[cell(rowspan=True)]]}],
               [{'type': 'table', 'cells': [[cell()]], 'is_compact': False}]]
        for value in bad:
            with self.subTest(value=repr(value)[:60]), self.assertRaises(ValueError):
                ui.build_blocks_message(value)
        with self.assertRaises(ValueError):
            ui.build_blocks_message([{'type': 'paragraph', 'text': 'x'}], skip_entity_detection=1)

    def test_native_button_actions_and_color(self):
        self.assertEqual(ui.styled_button('Run', callback_data='run', style='primary'),
                         {'text': 'Run', 'callback_data': 'run', 'style': 'primary'})
        self.assertEqual(ui.styled_button('Copy', copy_text='literal'), {'text': 'Copy', 'copy_text': {'text': 'literal'}})
        self.assertEqual(ui.styled_button('Open', url='tg://resolve?domain=example')['url'], 'tg://resolve?domain=example')
        ui.styled_button('x', copy_text='x'*256, style='success')
        ui.styled_button('x', url='https://example.com', style='danger')

    def test_callback_utf8_boundary(self):
        ui.styled_button('x', callback_data='😀'*16)
        with self.assertRaises(ValueError):
            ui.styled_button('x', callback_data='😀'*16+'x')

    def test_invalid_button_matrix(self):
        cases = [{}, {'callback_data': ''}, {'callback_data': []}, {'callback_data': 'x', 'url': 'https://example.com'},
                 {'callback_data': 'x', 'style': 'link'}, {'callback_data': 'x', 'style': []},
                 {'copy_text': 'x'*257}, {'copy_text': ''}, {'url': 'javascript:alert(1)'},
                 {'url': 'https://example.com\n'}, {'url': 'https://['}]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ui.styled_button('x', **kwargs)
        with self.assertRaises(ValueError):
            ui.styled_button('', callback_data='x')


if __name__ == '__main__':
    unittest.main()
