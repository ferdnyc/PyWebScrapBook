import os
import tempfile
import unittest
from base64 import b64decode
from datetime import datetime, timezone
from unittest import mock

from lxml import etree

from webscrapbook import WSB_DIR, util
from webscrapbook._polyfill import zipfile
from webscrapbook.scrapbook.convert import wsb2sb
from webscrapbook.scrapbook.convert.wsb2sb import NC, NS1, RDF

from . import TEMP_DIR, TestBookMixin, glob_files


def setUpModule():
    # set up a temp directory for testing
    global _tmpdir, tmpdir
    _tmpdir = tempfile.TemporaryDirectory(prefix='wsb2sb-', dir=TEMP_DIR)
    tmpdir = os.path.realpath(_tmpdir.name)

    # mock out user config
    global mockings
    mockings = (
        mock.patch('webscrapbook.scrapbook.host.WSB_USER_DIR', os.devnull),
        mock.patch('webscrapbook.WSB_USER_DIR', os.devnull),
        mock.patch('webscrapbook.WSB_USER_CONFIG', os.devnull),
    )
    for mocking in mockings:
        mocking.start()


def tearDownModule():
    # cleanup the temp directory
    _tmpdir.cleanup()

    # stop mock
    for mocking in mockings:
        mocking.stop()


class Test(TestBookMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = 8192

    def setUp(self):
        """Set up a general temp test folder
        """
        self.test_root = tempfile.mkdtemp(dir=tmpdir)
        self.test_input = os.path.join(self.test_root, 'input')
        self.test_input_tree = os.path.join(self.test_input, WSB_DIR, 'tree')
        self.test_output = os.path.join(self.test_root, 'output')
        self.test_output_rdf = os.path.join(self.test_output, 'scrapbook.rdf')

        os.makedirs(self.test_input_tree, exist_ok=True)


class TestRun(Test):
    def test_meta_basic(self):
        """A sample of typical WebScrapBook item."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'title': 'Hello 中文',
                'create': '20200102000000000',
                'modify': '20200103000000000',
                'source': 'http://example.com',
                'icon': 'favicon.bmp',
                'comment': 'some comment\nsecond line\nthird line',
                'charset': 'UTF-8',
                'locked': True,
            },
        })

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write('page content')

        icon_file = os.path.join(self.test_input, '20200101000000000', 'favicon.bmp')
        os.makedirs(os.path.dirname(icon_file), exist_ok=True)
        with open(icon_file, 'wb') as fh:
            fh.write(b64decode('Qk08AAAAAAAAADYAAAAoAAAAAQAAAAEAAAABACAAAAAAAAYAAAASCwAAEgsAAAAAAAAAAAAAAP8AAAAA'))

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(tree.getroot().tag, f'{RDF}RDF')
        self.assertEqual(dict(tree.find(f'{RDF}Description').attrib), {
            f'{RDF}about': f'urn:scrapbook:item{oid}',
            f'{NS1}id': oid,
            f'{NS1}type': '',
            f'{NS1}title': 'Hello 中文',
            f'{NS1}create': util.datetime_to_id_legacy(util.id_to_datetime('20200102000000000')),
            f'{NS1}modify': util.datetime_to_id_legacy(util.id_to_datetime('20200103000000000')),
            f'{NS1}source': 'http://example.com',
            f'{NS1}icon': f'resource://scrapbook/data/{oid}/favicon.bmp',
            f'{NS1}comment': 'some comment __BR__ second line __BR__ third line',
            f'{NS1}chars': 'UTF-8',
            f'{NS1}lock': 'true'
        })

    def test_meta_separator(self):
        """A sample of typical WebScrapBook separator item."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': 'separator',
                'title': 'Hello 中文',
                'create': '20200102000000000',
                'modify': '20200103000000000',
            },
        })

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(dict(tree.find(f'{NC}BookmarkSeparator').attrib), {
            f'{RDF}about': f'urn:scrapbook:item{oid}',
            f'{NS1}id': oid,
            f'{NS1}type': 'separator',
            f'{NS1}title': 'Hello 中文',
            f'{NS1}create': util.datetime_to_id_legacy(util.id_to_datetime('20200102000000000')),
            f'{NS1}modify': util.datetime_to_id_legacy(util.id_to_datetime('20200103000000000')),
            f'{NS1}source': '',
            f'{NS1}icon': '',
            f'{NS1}comment': '',
            f'{NS1}chars': '',
        })

    def test_meta_type01(self):
        """postit => note"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': 'postit',
            },
        })

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write("""\
<!DOCTYPE html><html><head>\
<meta charset="UTF-8">\
<meta name="viewport" content="width=device-width">\
<style>pre { white-space: pre-wrap; overflow-wrap: break-word; }</style>\
</head><body><pre>
postit page content < & > &lt; &amp; &gt;
</pre></body></html>""")

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(tree.find(f'{RDF}Description').attrib[f'{NS1}type'], 'note')

        # check output legacy note format
        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), """\
<html><head><meta http-equiv="Content-Type" content="text/html;Charset=UTF-8"></head><body><pre>
postit page content < & > &lt; &amp; &gt;
</pre></body></html>""")

    def test_meta_type02(self):
        """note => notex"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': 'note',
            },
        })

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write('note page content')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(tree.find(f'{RDF}Description').attrib[f'{NS1}type'], 'notex')

    def test_meta_marked01(self):
        """true marked property with "" type => marked type"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'marked': True,
            },
        })

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write('page content')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(tree.find(f'{RDF}Description').attrib[f'{NS1}type'], 'marked')
        self.assertIsNone(tree.find(f'{RDF}Description').attrib.get(f'{NS1}marked'))

    def test_meta_marked02(self):
        """marked property with other type => discard marked"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': 'file',
                'marked': True,
            },
        })

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write('page content')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(tree.find(f'{RDF}Description').attrib[f'{NS1}type'], 'file')
        self.assertIsNone(tree.find(f'{RDF}Description').attrib.get(f'{NS1}marked'))

    def test_meta_marked03(self):
        """false marked property => normal type"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'marked': False,
            },
        })

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write('page content')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(tree.find(f'{RDF}Description').attrib[f'{NS1}type'], '')
        self.assertIsNone(tree.find(f'{RDF}Description').attrib.get(f'{NS1}marked'))

    def test_meta_create(self):
        """empty create property => no create property"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'create': '',
            },
        })

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertIsNone(tree.find(f'{RDF}Description').attrib.get(f'{NS1}create'))

    def test_meta_modify(self):
        """empty modify property => no modify property"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'modify': '',
            },
        })

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertIsNone(tree.find(f'{RDF}Description').attrib.get(f'{NS1}modify'))

    def test_meta_icon01(self):
        """Empty icon with icon-moz property => moz-icon:// """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': 'image',
                'icon': '',
                'icon-moz': 'moz-icon://myimage.png?size=16',
            },
        })

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(
            tree.find(f'{RDF}Description').attrib[f'{NS1}icon'],
            'moz-icon://myimage.png?size=16',
        )

    def test_meta_icon02(self):
        """File with empty icon => moz-icon:// """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': 'file',
                'icon': '',
            },
        })
        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write('<meta charset="UTF-8"><meta http-equiv="refresh" content="0;URL=./myfile.txt">')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(
            tree.find(f'{RDF}Description').attrib[f'{NS1}icon'],
            'moz-icon://myfile.txt?size=16',
        )

    def test_meta_icon03(self):
        """Absolute URL => use as-is"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'icon': 'data:image/bmp;base64,Qk08AAAAAAAAADYAAAAoAAAAAQAAAAEAAAABACAAAAAAAAYAAAASCwAAEgsAAAAAAAAAAAAAAP8AAAAA',
            },
        })

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(
            tree.find(f'{RDF}Description').attrib[f'{NS1}icon'],
            'data:image/bmp;base64,Qk08AAAAAAAAADYAAAAoAAAAAQAAAAEAAAABACAAAAAAAAYAAAASCwAAEgsAAAAAAAAAAAAAAP8AAAAA',
        )

    def test_meta_icon04(self):
        """Favicon cache => icon folder"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000.html',
                'type': '',
                'icon': '.wsb/tree/favicon/dbc82be549e49d6db9a5719086722a4f1c5079cd.bmp',
            },
        })
        icon_file = os.path.join(self.test_input_tree, 'favicon', 'dbc82be549e49d6db9a5719086722a4f1c5079cd.bmp')
        os.makedirs(os.path.dirname(icon_file), exist_ok=True)
        with open(icon_file, 'wb') as fh:
            fh.write(b64decode('Qk08AAAAAAAAADYAAAAoAAAAAQAAAAEAAAABACAAAAAAAAYAAAASCwAAEgsAAAAAAAAAAAAAAP8AAAAA'))

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(
            tree.find(f'{RDF}Description').attrib[f'{NS1}icon'],
            'resource://scrapbook/icon/dbc82be549e49d6db9a5719086722a4f1c5079cd.bmp',
        )
        self.assertTrue(
            os.path.isfile(os.path.join(self.test_output, 'icon', 'dbc82be549e49d6db9a5719086722a4f1c5079cd.bmp')),
        )

    def test_meta_icon05(self):
        """Item folder => mapped item folder"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'icon': 'favicon.bmp',
            },
        })
        icon_file = os.path.join(self.test_input, '20200101000000000', 'favicon.bmp')
        os.makedirs(os.path.dirname(icon_file), exist_ok=True)
        with open(icon_file, 'wb') as fh:
            fh.write(b64decode('Qk08AAAAAAAAADYAAAAoAAAAAQAAAAEAAAABACAAAAAAAAYAAAASCwAAEgsAAAAAAAAAAAAAAP8AAAAA'))

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        ts = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(
            tree.find(f'{RDF}Description').attrib[f'{NS1}icon'],
            f'resource://scrapbook/data/{ts}/favicon.bmp',
        )
        self.assertTrue(
            os.path.isfile(os.path.join(self.test_output, 'data', ts, 'favicon.bmp')),
        )

    def test_meta_icon06(self):
        """Data folder => data folder"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
                'icon': '../icons/favicon.bmp',
            },
        })
        icon_file = os.path.join(self.test_input, 'icons', 'favicon.bmp')
        os.makedirs(os.path.dirname(icon_file), exist_ok=True)
        with open(icon_file, 'wb') as fh:
            fh.write(b64decode('Qk08AAAAAAAAADYAAAAoAAAAAQAAAAEAAAABACAAAAAAAAYAAAASCwAAEgsAAAAAAAAAAAAAAP8AAAAA'))

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(
            tree.find(f'{RDF}Description').attrib[f'{NS1}icon'],
            'resource://scrapbook/data/icons/favicon.bmp',
        )
        self.assertTrue(
            os.path.isfile(os.path.join(self.test_output, 'data', 'icons', 'favicon.bmp')),
        )

    def test_meta_icon07(self):
        """Outside of data folder => scrapbook folder"""
        self.init_book(
            self.test_input,
            config="""\
[book ""]
data_dir = data
tree_dir = tree
""",
            meta={
                '20200101000000000': {
                    'index': '20200101000000000/index.html',
                    'type': '',
                    'icon': '../../icons/favicon.bmp',
                },
            },
        )
        icon_file = os.path.join(self.test_input, 'icons', 'favicon.bmp')
        os.makedirs(os.path.dirname(icon_file), exist_ok=True)
        with open(icon_file, 'wb') as fh:
            fh.write(b64decode('Qk08AAAAAAAAADYAAAAoAAAAAQAAAAEAAAABACAAAAAAAAYAAAASCwAAEgsAAAAAAAAAAAAAAP8AAAAA'))

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(
            tree.find(f'{RDF}Description').attrib[f'{NS1}icon'],
            'resource://scrapbook/icons/favicon.bmp',
        )
        self.assertTrue(
            os.path.isfile(os.path.join(self.test_output, 'icons', 'favicon.bmp')),
        )

    def test_id_mapping01(self):
        """WebScrapBook timestamp => legacy ScrapBook timestamp"""
        self.init_book(
            self.test_input,
            meta={
                '20200101000000000': {
                    'type': 'folder',
                },
                '20200101000001000': {
                    'type': 'folder',
                },
                '20200101000002000': {
                    'type': 'folder',
                },
            },
            toc={
                'root': [
                    '20200101000000000',
                    '20200101000001000',
                    '20200101000002000',
                ],
            },
        )

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual([node.attrib[f'{NS1}id'] for node in tree.findall(f'{RDF}Description')], [
            util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000')),
            util.datetime_to_id_legacy(util.id_to_datetime('20200101000001000')),
            util.datetime_to_id_legacy(util.id_to_datetime('20200101000002000')),
        ])
        self.assertEqual([node.attrib[f'{RDF}resource'] for node in tree.findall(f'{RDF}Seq/{RDF}li')], [
            'urn:scrapbook:item' + util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000')),
            'urn:scrapbook:item' + util.datetime_to_id_legacy(util.id_to_datetime('20200101000001000')),
            'urn:scrapbook:item' + util.datetime_to_id_legacy(util.id_to_datetime('20200101000002000')),
        ])

    def test_id_mapping02(self):
        """If conflict, increament by 1 from timestamp"""
        self.init_book(
            self.test_input,
            meta={
                '20200101000000000': {
                    'type': 'folder',
                },
                '20200101000000001': {
                    'type': 'folder',
                },
                '20200101000000010': {
                    'type': 'folder',
                },
            },
            toc={
                'root': [
                    '20200101000000000',
                    '20200101000000001',
                    '20200101000000010',
                ],
            },
        )

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual([node.attrib[f'{NS1}id'] for node in tree.findall(f'{RDF}Description')], [
            util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000')),
            util.datetime_to_id_legacy(util.id_to_datetime('20200101000001000')),
            util.datetime_to_id_legacy(util.id_to_datetime('20200101000002000')),
        ])
        self.assertEqual([node.attrib[f'{RDF}resource'] for node in tree.findall(f'{RDF}Seq/{RDF}li')], [
            'urn:scrapbook:item' + util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000')),
            'urn:scrapbook:item' + util.datetime_to_id_legacy(util.id_to_datetime('20200101000001000')),
            'urn:scrapbook:item' + util.datetime_to_id_legacy(util.id_to_datetime('20200101000002000')),
        ])

    def test_id_mapping03(self):
        """Legacy timestamp => use as-is"""
        self.init_book(
            self.test_input,
            meta={
                '20200101000000': {
                    'type': 'folder',
                },
                '20200101000010': {
                    'type': 'folder',
                },
                '20200101000100': {
                    'type': 'folder',
                },
            },
            toc={
                'root': [
                    '20200101000000',
                    '20200101000010',
                    '20200101000100',
                ],
            },
        )

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual([node.attrib[f'{NS1}id'] for node in tree.findall(f'{RDF}Description')], [
            '20200101000000',
            '20200101000010',
            '20200101000100',
        ])
        self.assertEqual([node.attrib[f'{RDF}resource'] for node in tree.findall(f'{RDF}Seq/{RDF}li')], [
            'urn:scrapbook:item20200101000000',
            'urn:scrapbook:item20200101000010',
            'urn:scrapbook:item20200101000100',
        ])

    def test_id_mapping04(self):
        """Increament by 1 from now if not timestamp"""
        self.init_book(
            self.test_input,
            meta={
                'dummy1': {
                    'type': 'folder',
                },
                'dummy2': {
                    'type': 'folder',
                },
                'dummy3': {
                    'type': 'folder',
                },
            },
            toc={
                'root': [
                    'dummy1',
                    'dummy2',
                    'dummy3',
                ],
            },
        )

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        ts_now = datetime.now(timezone.utc).timestamp()
        id_list = [n.attrib[f'{NS1}id'] for n in tree.findall(f'{RDF}Description')]
        ts_list = [util.id_to_datetime_legacy(id).timestamp() for id in id_list]
        self.assertAlmostEqual(ts_list[0], ts_now, delta=3)
        self.assertEqual(ts_list[0] + 1, ts_list[1])
        self.assertEqual(ts_list[0] + 2, ts_list[2])

        self.assertEqual([node.attrib[f'{RDF}resource'] for node in tree.findall(f'{RDF}Seq/{RDF}li')], [
            'urn:scrapbook:item' + id_list[0],
            'urn:scrapbook:item' + id_list[1],
            'urn:scrapbook:item' + id_list[2],
        ])

    def test_toc_no_root(self):
        """root list not exist => empty root container"""
        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertIsNotNone(tree.find(f'{RDF}Seq[@{RDF}about="urn:scrapbook:root"]'))
        self.assertIsNone(tree.find(f'{RDF}Seq[@{RDF}about="urn:scrapbook:root"]/{RDF}li'))

    def test_toc_duplicate(self):
        """Duplicated item => preserve only the first one (depth first)"""
        self.init_book(
            self.test_input,
            meta={
                '20200101000001': {
                    'type': 'folder'
                },
                '20200101000002': {
                    'type': 'folder'
                },
                '20200101000003': {
                    'type': 'folder',
                },
            },
            toc={
                'root': [
                    '20200101000001',
                    '20200101000002',
                    '20200101000003',
                ],
                '20200101000001': [
                    '20200101000002',
                ],
            },
        )

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        with open(self.test_output_rdf, 'rb') as fh:
            tree = etree.parse(fh)

        self.assertEqual(
            [
                node.attrib[f'{RDF}resource']
                for node in
                tree.findall(f'{RDF}Seq[@{RDF}about="urn:scrapbook:root"]/{RDF}li')
            ],
            [
                'urn:scrapbook:item20200101000001',
                'urn:scrapbook:item20200101000003',
            ],
        )

        self.assertEqual(
            [
                node.attrib[f'{RDF}resource']
                for node in
                tree.findall(f'{RDF}Seq[@{RDF}about="urn:scrapbook:item20200101000001"]/{RDF}li')
            ],
            [
                'urn:scrapbook:item20200101000002',
            ],
        )

    def test_copy_data_files01(self):
        """###/index.html => copy ###/* to <ID>/*"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write('page content')
        with open(os.path.join(index_dir, 'page.html'), 'w', encoding='UTF-8') as fh:
            fh.write('dummy')
        os.makedirs(os.path.join(self.test_input, '20200101000000001'), exist_ok=True)
        with open(os.path.join(self.test_input, 'other.html'), 'w', encoding='UTF-8') as fh:
            fh.write('dummy')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(glob_files(self.test_output), {
            os.path.join(self.test_output, ''),
            os.path.join(self.test_output, 'scrapbook.rdf'),
            os.path.join(self.test_output, 'data'),
            os.path.join(self.test_output, 'data', oid),
            os.path.join(self.test_output, 'data', oid, 'index.html'),
            os.path.join(self.test_output, 'data', oid, 'page.html'),
        })

    def test_copy_data_files02(self):
        """###.html => copy ###.html to <ID>/*"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000.html',
                'type': '',
            },
        })

        with open(os.path.join(self.test_input, '20200101000000000.html'), 'w', encoding='UTF-8') as fh:
            fh.write('page content')
        with open(os.path.join(self.test_input, 'page.html'), 'w', encoding='UTF-8') as fh:
            fh.write('dummy')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(glob_files(self.test_output), {
            os.path.join(self.test_output, ''),
            os.path.join(self.test_output, 'scrapbook.rdf'),
            os.path.join(self.test_output, 'data'),
            os.path.join(self.test_output, 'data', oid),
            os.path.join(self.test_output, 'data', oid, 'index.html'),
        })

    def test_copy_data_files03(self):
        """###.htz => copy internal files to <ID>/*"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000.htz',
                'type': '',
            },
        })

        with zipfile.ZipFile(os.path.join(self.test_input, '20200101000000000.htz'), 'w') as zh:
            zh.writestr('index.html', 'page content')
            zh.writestr('page.html', 'dummy')
            zh.writestr('subdir/page2.html', 'dummy2')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(glob_files(self.test_output), {
            os.path.join(self.test_output, ''),
            os.path.join(self.test_output, 'scrapbook.rdf'),
            os.path.join(self.test_output, 'data'),
            os.path.join(self.test_output, 'data', oid),
            os.path.join(self.test_output, 'data', oid, 'index.html'),
            os.path.join(self.test_output, 'data', oid, 'page.html'),
            os.path.join(self.test_output, 'data', oid, 'subdir'),
            os.path.join(self.test_output, 'data', oid, 'subdir', 'page2.html'),
        })

    def test_copy_data_files04(self):
        """###.maff => copy internal files of first topdir to <ID>/*"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000.maff',
                'type': '',
            },
        })

        with zipfile.ZipFile(os.path.join(self.test_input, '20200101000000000.maff'), 'w') as zh:
            zh.writestr('20200101000000000/index.html', 'page content')
            zh.writestr('20200101000000000/page.html', 'dummy')
            zh.writestr('20200101000000000/subdir/page2.html', 'dummy2')
            zh.writestr('20200101000000001/index.html', 'page content 2')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(glob_files(self.test_output), {
            os.path.join(self.test_output, ''),
            os.path.join(self.test_output, 'scrapbook.rdf'),
            os.path.join(self.test_output, 'data'),
            os.path.join(self.test_output, 'data', oid),
            os.path.join(self.test_output, 'data', oid, 'index.html'),
            os.path.join(self.test_output, 'data', oid, 'page.html'),
            os.path.join(self.test_output, 'data', oid, 'subdir'),
            os.path.join(self.test_output, 'data', oid, 'subdir', 'page2.html'),
        })

    def test_copy_data_files05(self):
        """###.maff => copy nothing if no page"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000.maff',
                'type': '',
            },
        })

        with zipfile.ZipFile(os.path.join(self.test_input, '20200101000000000.maff'), 'w') as zh:
            zh.writestr('index.html', 'dummy')

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        self.assertEqual(glob_files(self.test_output), {
            os.path.join(self.test_output, ''),
            os.path.join(self.test_output, 'scrapbook.rdf'),
        })

    def test_copy_data_files06(self):
        """foo.bar => copy it and create meta refresh"""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '中文#1.xhtml',
                'type': '',
            },
        })

        with open(os.path.join(self.test_input, '中文#1.xhtml'), 'w', encoding='UTF-8') as fh:
            fh.write("""\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Title of document</title>
</head>
<body>
some content
</body>
</html>
""")

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        self.assertEqual(glob_files(self.test_output), {
            os.path.join(self.test_output, ''),
            os.path.join(self.test_output, 'scrapbook.rdf'),
            os.path.join(self.test_output, 'data'),
            os.path.join(self.test_output, 'data', oid),
            os.path.join(self.test_output, 'data', oid, 'index.html'),
            os.path.join(self.test_output, 'data', oid, '中文#1.xhtml'),
        })
        self.assertEqual(
            util.get_meta_refreshed_file(os.path.join(self.test_output, 'data', oid, 'index.html')),
            os.path.join(self.test_output, 'data', oid, '中文#1.xhtml'),
        )


class TestConvertHtmlFile(Test):
    def test_convert_html_file_linemarker01(self):
        """Convert linemarker."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """<html><body><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" style="background: #FFFF00; background: linear-gradient(transparent 40%, rgba(255,255,0,0.9) 90%, transparent 100%);" class="first">Lorem ipsum dolor </scrapbook-linemarker><strong><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" style="background: #FFFF00; background: linear-gradient(transparent 40%, rgba(255,255,0,0.9) 90%, transparent 100%);">sit amet</scrapbook-linemarker></strong><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" style="background: #FFFF00; background: linear-gradient(transparent 40%, rgba(255,255,0,0.9) 90%, transparent 100%);" class="last">, consectetur adipiscing elit.</scrapbook-linemarker></body></html>"""  # noqa: E501

        expected = """<html><body><span data-sb-id="20200101000000000" data-sb-obj="linemarker" class="linemarker-marked-line" style="background: #FFFF00; background: linear-gradient(transparent 40%, rgba(255,255,0,0.9) 90%, transparent 100%);">Lorem ipsum dolor </span><strong><span data-sb-id="20200101000000000" data-sb-obj="linemarker" class="linemarker-marked-line" style="background: #FFFF00; background: linear-gradient(transparent 40%, rgba(255,255,0,0.9) 90%, transparent 100%);">sit amet</span></strong><span data-sb-id="20200101000000000" data-sb-obj="linemarker" class="linemarker-marked-line" style="background: #FFFF00; background: linear-gradient(transparent 40%, rgba(255,255,0,0.9) 90%, transparent 100%);">, consectetur adipiscing elit.</span></body></html>"""  # noqa: E501

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_linemarker02(self):
        """Convert annotated linemarker."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """<html><body><b><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" style="border-bottom: 2px dotted #FF0000;" class="first" title="inline annotation
2nd line">Suspendisse eget</scrapbook-linemarker></b><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" style="border-bottom: 2px dotted #FF0000;" class="last" title="inline annotation
2nd line"> interdum quam, eu semper ipsum</scrapbook-linemarker>.<style data-scrapbook-elem="annotation-css">/* stylesheet */</style><script data-scrapbook-elem="annotation-loader">/* script */</script></body></html>"""  # noqa: E501

        expected = """<html><body><b><span data-sb-id="20200101000000000" data-sb-obj="inline" class="scrapbook-inline" style="border-bottom: 2px dotted #FF0000;" title="inline annotation
2nd line">Suspendisse eget</span></b><span data-sb-id="20200101000000000" data-sb-obj="inline" class="scrapbook-inline" style="border-bottom: 2px dotted #FF0000;" title="inline annotation
2nd line"> interdum quam, eu semper ipsum</span>.</body></html>"""  # noqa: E501

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_sticky01(self):
        """Convert sticky (styled plaintext)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """<html><body><scrapbook-sticky data-scrapbook-id="20200101000000000" data-scrapbook-elem="sticky" class="styled plaintext" style="width: 250px; height: 100px; left: 572px; top: 83px;">annotation
2nd line</scrapbook-sticky><style data-scrapbook-elem="annotation-css">/* stylesheet */</style><script data-scrapbook-elem="annotation-loader">/* script */</script></body></html>"""  # noqa: E501

        expected = """<html><body><div data-sb-obj="freenote" style="cursor: help; overflow: visible; border: 1px solid #CCCCCC; border-top-width: 12px; background: #FAFFFA; opacity: 0.95; padding: 0px; z-index: 500000; text-align: start; font-size: small; line-height: 1.2em; word-wrap: break-word; position: absolute; width: 250px; height: 100px; left: 572px; top: 83px;">annotation<br>2nd line</div></body></html>"""  # noqa: E501

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_sticky02(self):
        """Convert sticky (styled plaintext relative)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """<html><body><scrapbook-sticky data-scrapbook-id="20200101000000000" data-scrapbook-elem="sticky" class="styled plaintext relative">annotation
2nd line</scrapbook-sticky><style data-scrapbook-elem="annotation-css">/* stylesheet */</style><script data-scrapbook-elem="annotation-loader">/* script */</script></body></html>"""  # noqa: E501

        expected = """<html><body><div data-sb-obj="freenote" style="cursor: help; overflow: visible; margin: 16px auto; border: 1px solid #CCCCCC; border-top-width: 12px; background: #FAFFFA; opacity: 0.95; padding: 0px; z-index: 500000; text-align: start; font-size: small; line-height: 1.2em; word-wrap: break-word; position: static;">annotation<br>2nd line</div></body></html>"""  # noqa: E501

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_sticky03(self):
        """Convert sticky (styled)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """<html><body><scrapbook-sticky data-scrapbook-id="20200101000000000" data-scrapbook-elem="sticky" class="styled" style="left: 367px; top: 323px; width: 250px; height: 100px;">annotation<div><b>2nd</b> line</div></scrapbook-sticky><style data-scrapbook-elem="annotation-css">/* stylesheet */</style><script data-scrapbook-elem="annotation-loader">/* script */</script></body></html>"""  # noqa: E501

        expected = """<html><body><div data-sb-obj="freenote" style="cursor: help; overflow: visible; border: 1px solid #CCCCCC; border-top-width: 12px; background: #FAFFFA; opacity: 0.95; padding: 0px; z-index: 500000; text-align: start; font-size: small; line-height: 1.2em; word-wrap: break-word; position: absolute; left: 367px; top: 323px; width: 250px; height: 100px;">annotation<div><b>2nd</b> line</div></div></body></html>"""  # noqa: E501

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_sticky04(self):
        """Convert sticky (styled relative)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """<html><body><scrapbook-sticky data-scrapbook-id="20200101000000000" data-scrapbook-elem="sticky" class="styled relative" style="height: 42.6px;">annotation<div><b>2nd</b> line</div></scrapbook-sticky><style data-scrapbook-elem="annotation-css">/* stylesheet */</style><script data-scrapbook-elem="annotation-loader">/* script */</script></body></html>"""  # noqa: E501

        expected = """<html><body><div data-sb-obj="freenote" style="cursor: help; overflow: visible; margin: 16px auto; border: 1px solid #CCCCCC; border-top-width: 12px; background: #FAFFFA; opacity: 0.95; padding: 0px; z-index: 500000; text-align: start; font-size: small; line-height: 1.2em; word-wrap: break-word; position: static; height: 42.6px;">annotation<div><b>2nd</b> line</div></div></body></html>"""  # noqa: E501

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_sticky05(self):
        """Convert sticky (plaintext relative)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """<html><body><scrapbook-sticky data-scrapbook-elem="sticky" class="plaintext relative" style="border: 1px dotted rgb(215, 221, 191) !important; margin: 10px !important; padding: 10px !important; font-size: 12px !important; font-weight: normal !important; line-height: 16px !important; text-decoration: none !important; color: rgb(96, 96, 96) !important; background-color: rgb(239, 248, 206) !important; cursor: pointer !important; white-space: pre-wrap;">Legacy block comment.
Second line.</scrapbook-sticky><style data-scrapbook-elem="annotation-css">/* stylesheet */</style><script data-scrapbook-elem="annotation-loader">/* script */</script></body></html>"""  # noqa: E501

        expected = """<html><body><div class="scrapbook-block-comment" style="border: 1px dotted rgb(215, 221, 191) !important; margin: 10px !important; padding: 10px !important; font-size: 12px !important; font-weight: normal !important; line-height: 16px !important; text-decoration: none !important; color: rgb(96, 96, 96) !important; background-color: rgb(239, 248, 206) !important; cursor: pointer !important; white-space: pre-wrap;">Legacy block comment.
Second line.</div></body></html>"""  # noqa: E501

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_other(self):
        """Convert other elements."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'index': '20200101000000000/index.html',
                'type': '',
            },
        })

        input = """\
<!DOCTYPE html>
<html>
<head>
<title data-scrapbook-elem="title">My page</title>
</head>
<body>
Donec nec lacus<span data-scrapbook-elem="annotation">(my legacy <em>inline</em>annotation)</span> efficitur.
<a data-scrapbook-elem="link-url" href="http://example.com">Suspendisse eget interdum quam</a>, eu semper <span data-scrapbook-id="20200101000000000">ipsum</span>.
</body>
</html>
"""  # noqa: E501

        expected = """\
<!DOCTYPE html>
<html>
<head>
<title data-sb-obj="title">My page</title>
</head>
<body>
Donec nec lacus<span data-sb-obj="annotation">(my legacy <em>inline</em>annotation)</span> efficitur.
<a data-sb-obj="link-url" href="http://example.com">Suspendisse eget interdum quam</a>, eu semper <span data-sb-id="20200101000000000">ipsum</span>.
</body>
</html>
"""

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_convert_html_file_skip_special_tags(self):
        """Do not rewrite content in <template>, <xml>, <math>, etc.
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """\
<!DOCTYPE html>
<html>
<body>
<xmp>
<span data-scrapbook-elem="annotation">foo</span>
</xmp>
<template>
<span data-scrapbook-elem="annotation">foo</span>
</template>
<svg>
<text data-scrapbook-elem="annotation">foo</text>
</svg>
<math>
<mtext data-scrapbook-elem="annotation">foo</mtext>
</math>
</body>
</html>
"""

        expected = """\
<!DOCTYPE html>
<html>
<body>
<xmp>
<span data-scrapbook-elem="annotation">foo</span>
</xmp>
<template>
<span data-scrapbook-elem="annotation">foo</span>
</template>
<svg>
<text data-scrapbook-elem="annotation">foo</text>
</svg>
<math>
<mtext data-scrapbook-elem="annotation">foo</mtext>
</math>
</body>
</html>
"""

        index_dir = os.path.join(self.test_input, '20200101000000000')
        os.makedirs(index_dir, exist_ok=True)
        with open(os.path.join(index_dir, 'index.html'), 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in wsb2sb.run(self.test_input, self.test_output):
            pass

        oid = util.datetime_to_id_legacy(util.id_to_datetime('20200101000000000'))
        with open(os.path.join(self.test_output, 'data', oid, 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)


if __name__ == '__main__':
    unittest.main()
