import os
import tempfile
import unittest
from unittest import mock

from webscrapbook._polyfill import zipfile
from webscrapbook.scrapbook.convert import migrate

from . import TEMP_DIR, TestBookMixin, glob_files


def setUpModule():
    # set up a temp directory for testing
    global _tmpdir, tmpdir
    _tmpdir = tempfile.TemporaryDirectory(prefix='migrate-', dir=TEMP_DIR)
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
        self.test_output = os.path.join(self.test_root, 'output')


class TestConvertDataFilesLegacy(Test):
    def test_data_postit(self):
        """Convert postit."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': 'postit',
                'index': '20200101000000000/index.html',
            },
        })

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write("""\
<html><head><meta http-equiv="Content-Type" content="text/html;Charset=UTF-8"></head><body><pre>
postit page content < & > &lt; &amp; &gt;
</pre></body></html>""")

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), """\
<!DOCTYPE html><html><head>\
<meta charset="UTF-8">\
<meta name="viewport" content="width=device-width">\
<style>pre { white-space: pre-wrap; overflow-wrap: break-word; }</style>\
</head><body><pre>
postit page content < & > &lt; &amp; &gt;
</pre></body></html>""")

    def test_data_annotations_linemarker01(self):
        """Convert linemarker."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body><span data-sb-id="1577836800000" data-sb-obj="linemarker" class="linemarker-marked-line" style="background-color: yellow;">Lorem ipsum dolor sit </span><b><span data-sb-id="1577836800000" data-sb-obj="linemarker" class="linemarker-marked-line" style="background-color: yellow;">amet</span></b><span data-sb-id="1577836800000" data-sb-obj="linemarker" class="linemarker-marked-line" style="background-color: yellow;">, consectetur adipiscing elit.</span></body></html>"""  # noqa: E501

        expected = """<html><body><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" class="first" style="background-color: yellow;">Lorem ipsum dolor sit </scrapbook-linemarker><b><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" style="background-color: yellow;">amet</scrapbook-linemarker></b><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" class="last" style="background-color: yellow;">, consectetur adipiscing elit.</scrapbook-linemarker></body></html>"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_data_annotations_linemarker02(self):
        """Convert legacy ScrapBook linemarker."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body><span class="linemarker-marked-line" style="background-color: yellow;">Lorem ipsum dolor sit </span><b><span class="linemarker-marked-line" style="background-color: yellow;">amet</span></b><span class="linemarker-marked-line" style="background-color: yellow;">, consectetur adipiscing elit.</span></body></html>"""  # noqa: E501

        expected = """<html><body><scrapbook-linemarker data-scrapbook-elem="linemarker" style="background-color: yellow;">Lorem ipsum dolor sit </scrapbook-linemarker><b><scrapbook-linemarker data-scrapbook-elem="linemarker" style="background-color: yellow;">amet</scrapbook-linemarker></b><scrapbook-linemarker data-scrapbook-elem="linemarker" style="background-color: yellow;">, consectetur adipiscing elit.</scrapbook-linemarker></body></html>"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), expected)

    def test_data_annotations_inline01(self):
        """Convert inline annotation."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body>Lorem ipsum dolor <span data-sb-id="1577836800000" data-sb-obj="inline" class="scrapbook-inline" style="border-bottom: 2px dotted rgb(255, 51, 51); cursor: help;" title="test inline annotation">sit amet, </span><b><span data-sb-id="1577836800000" data-sb-obj="inline" class="scrapbook-inline" style="border-bottom: 2px dotted rgb(255, 51, 51); cursor: help;" title="test inline annotation">consectetur</span></b><span data-sb-id="1577836800000" data-sb-obj="inline" class="scrapbook-inline" style="border-bottom: 2px dotted rgb(255, 51, 51); cursor: help;" title="test inline annotation"> adipiscing elit</span>.</body></html>"""  # noqa: E501

        expected = """<html><body>Lorem ipsum dolor <scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" class="first" style="border-bottom: 2px dotted rgb(255, 51, 51); cursor: help;" title="test inline annotation">sit amet, </scrapbook-linemarker><b><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" style="border-bottom: 2px dotted rgb(255, 51, 51); cursor: help;" title="test inline annotation">consectetur</scrapbook-linemarker></b><scrapbook-linemarker data-scrapbook-id="20200101000000000" data-scrapbook-elem="linemarker" class="last" style="border-bottom: 2px dotted rgb(255, 51, 51); cursor: help;" title="test inline annotation"> adipiscing elit</scrapbook-linemarker>.<style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_inline02(self):
        """Convert legacy ScrapBook inline annotation."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body>Lorem ipsum dolor <span style="border-bottom: 2px dotted #FF3333; cursor: help;" class="scrapbook-inline" title="test inline annotation">sit amet, </span><b><span style="border-bottom: 2px dotted #FF3333; cursor: help;" class="scrapbook-inline" title="123">consectetur</span></b><span style="border-bottom: 2px dotted #FF3333; cursor: help;" class="scrapbook-inline" title="123"> adipiscing elit</span>.</body></html>"""  # noqa: E501

        expected = """<html><body>Lorem ipsum dolor <scrapbook-linemarker data-scrapbook-elem="linemarker" style="border-bottom: 2px dotted #FF3333; cursor: help;" title="test inline annotation">sit amet, </scrapbook-linemarker><b><scrapbook-linemarker data-scrapbook-elem="linemarker" style="border-bottom: 2px dotted #FF3333; cursor: help;" title="123">consectetur</scrapbook-linemarker></b><scrapbook-linemarker data-scrapbook-elem="linemarker" style="border-bottom: 2px dotted #FF3333; cursor: help;" title="123"> adipiscing elit</scrapbook-linemarker>.<style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_freenote01(self):
        """Convert freenote (absolute)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body><div data-sb-obj="freenote" style="cursor: help; overflow: visible; margin: 0px; border-width: 12px 1px 1px; border-style: solid; border-color: rgb(204, 204, 204); border-image: none; background: rgb(250, 255, 250) none repeat scroll 0% 0%; opacity: 0.95; padding: 0px; z-index: 500000; text-align: start; font-size: small; line-height: 1.2em; overflow-wrap: break-word; width: 337px; height: 179px; position: absolute; left: 144px; top: 481px;">Test freenote with <b>HTML</b> <u>markups</u>. <br><br>晱瓨扚醏碙螒劦一晹掁舁彾圢柂乜，凗兟兀衩臿趐匼犮屮肸慞垞毌呦。</div></body></html>"""  # noqa: E501

        expected = """<html><body><scrapbook-sticky data-scrapbook-elem="sticky" class="styled" style="width: 337px; height: 179px; left: 144px; top: 481px;">Test freenote with <b>HTML</b> <u>markups</u>. <br><br>晱瓨扚醏碙螒劦一晹掁舁彾圢柂乜，凗兟兀衩臿趐匼犮屮肸慞垞毌呦。</scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_freenote02(self):
        """Convert freenote (relative)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body><div data-sb-obj="freenote" style="cursor: help; overflow: visible; margin: 16px auto; border-width: 12px 1px 1px; border-style: solid; border-color: rgb(204, 204, 204); border-image: none; background: rgb(250, 255, 250) none repeat scroll 0% 0%; opacity: 0.95; padding: 0px; z-index: 500000; text-align: start; font-size: small; line-height: 1.2em; overflow-wrap: break-word; width: 233px; height: 89px; position: static;">This is a relative freenote.<br>Anchored between paragraphs.</div></body></html>"""  # noqa: E501

        expected = """<html><body><scrapbook-sticky data-scrapbook-elem="sticky" class="styled relative" style="width: 233px; height: 89px;">This is a relative freenote.<br>Anchored between paragraphs.</scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_sticky01(self):
        """Convert legacy ScrapBook sticky (absolute)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><head><link media="all" href="chrome://scrapbook/skin/annotation.css" type="text/css" id="scrapbook-sticky-css" rel="stylesheet"></head><body><div style="left: 376px; top: 107px; position: absolute; width: 240px; height: 79px;" class="scrapbook-sticky"><div class="scrapbook-sticky-header"></div>Sample sticky annotation.
Second line.</div></body></html>"""  # noqa: E501

        expected = """<html><head></head><body><scrapbook-sticky data-scrapbook-elem="sticky" class="styled plaintext" style="left: 376px; top: 107px; width: 240px; height: 79px;">Sample sticky annotation.
Second line.</scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_sticky02(self):
        """Convert legacy ScrapBook sticky (relative)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><head><link media="all" href="chrome://scrapbook/skin/annotation.css" type="text/css" id="scrapbook-sticky-css" rel="stylesheet"></head><body><div style="width: 511px; height: 70px;" class="scrapbook-sticky scrapbook-sticky-relative"><div class="scrapbook-sticky-header"></div>Relative sticky.
Second line.</div></body></html>"""  # noqa: E501

        expected = """<html><head></head><body><scrapbook-sticky data-scrapbook-elem="sticky" class="styled plaintext relative" style="width: 511px; height: 70px;">Relative sticky.
Second line.</scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_sticky03(self):
        """Convert improperly saved legacy ScrapBook sticky (absolute)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><head><div style="left: 303px; top: 212px; position: absolute; width: 250px; height: 100px;" class="scrapbook-sticky"><div class="scrapbook-sticky-header"></div><textarea style="height: 74px;"></textarea><div class="scrapbook-sticky-footer"><input src="chrome://scrapbook/skin/sticky_save.png" onclick="this.parentNode.parentNode.appendChild(document.createTextNode(this.parentNode.previousSibling.value));this.parentNode.parentNode.removeChild(this.parentNode.previousSibling);this.parentNode.parentNode.removeChild(this.parentNode);" type="image"><input src="chrome://scrapbook/skin/sticky_delete.png" onclick="this.parentNode.parentNode.parentNode.removeChild(this.parentNode.parentNode);" type="image"></div></div></body></html>"""  # noqa: E501

        expected = """<html><head><scrapbook-sticky data-scrapbook-elem="sticky" class="styled plaintext" style="left: 303px; top: 212px; width: 250px; height: 100px;"></scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_sticky04(self):
        """Convert improperly saved legacy ScrapBook sticky (relative)."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><head><div style="width: 640px; height: 92px;" class="scrapbook-sticky scrapbook-sticky-relative"><div class="scrapbook-sticky-header"></div><textarea style="height: 66px;"></textarea><div class="scrapbook-sticky-footer"><input src="chrome://scrapbook/skin/sticky_save.png" onclick="this.parentNode.parentNode.appendChild(document.createTextNode(this.parentNode.previousSibling.value));this.parentNode.parentNode.removeChild(this.parentNode.previousSibling);this.parentNode.parentNode.removeChild(this.parentNode);" type="image"><input src="chrome://scrapbook/skin/sticky_delete.png" onclick="this.parentNode.parentNode.parentNode.removeChild(this.parentNode.parentNode);" type="image"></div></div></body></html>"""  # noqa: E501

        expected = """<html><head><scrapbook-sticky data-scrapbook-elem="sticky" class="styled plaintext relative" style="width: 640px; height: 92px;"></scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_block_comment01(self):
        """Convert legacy ScrapBook block comment."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body><div class="scrapbook-block-comment" style="border: 1px dotted rgb(215, 221, 191) !important; margin: 10px !important; padding: 10px !important; font-size: 12px !important; font-weight: normal !important; line-height: 16px !important; text-decoration: none !important; color: rgb(96, 96, 96) !important; background-color: rgb(239, 248, 206) !important; cursor: pointer !important;">This is a sample of a very legacy block comment.</div></body></html>"""  # noqa: E501

        expected = """<html><body><scrapbook-sticky data-scrapbook-elem="sticky" class="plaintext relative" style="border: 1px dotted rgb(215, 221, 191) !important; margin: 10px !important; padding: 10px !important; font-size: 12px !important; font-weight: normal !important; line-height: 16px !important; text-decoration: none !important; color: rgb(96, 96, 96) !important; background-color: rgb(239, 248, 206) !important; cursor: pointer !important; white-space: pre-wrap;">This is a sample of a very legacy block comment.</scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_block_comment02(self):
        """Convert legacy ScrapBook block comment.

        - Do not add 'white-space: pre-wrap;' style if already exists.
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body><div class="scrapbook-block-comment" style="border: 1px dotted rgb(215, 221, 191) !important; margin: 10px !important; padding: 10px !important; font-size: 12px !important; font-weight: normal !important; line-height: 16px !important; text-decoration: none !important; color: rgb(96, 96, 96) !important; background-color: rgb(239, 248, 206) !important; WHITE-SPACE:PRE-WRAP !important; cursor: pointer !important;">This is a sample of a very legacy block comment.</div></body></html>"""  # noqa: E501

        expected = """<html><body><scrapbook-sticky data-scrapbook-elem="sticky" class="plaintext relative" style="border: 1px dotted rgb(215, 221, 191) !important; margin: 10px !important; padding: 10px !important; font-size: 12px !important; font-weight: normal !important; line-height: 16px !important; text-decoration: none !important; color: rgb(96, 96, 96) !important; background-color: rgb(239, 248, 206) !important; WHITE-SPACE:PRE-WRAP !important; cursor: pointer !important;">This is a sample of a very legacy block comment.</scrapbook-sticky><style data-scrapbook-elem="annotation-css">"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output[:len(expected)], expected)
            self.assertRegex(output, r'<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>')  # noqa: E501

    def test_data_annotations_other01(self):
        """Convert other legacy ScrapBook elements.
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
<head>
<title data-sb-obj="title">My page</title>
</head>
<body>
Donec nec lacus<span data-sb-obj="annotation">(my legacy <em>inline</em>annotation)</span> efficitur.
<a data-sb-obj="link-url" href="http://example.com">Suspendisse eget interdum quam</a>, eu semper <span data-sb-id="1577836800000">ipsum</span>.
</body>
</html>
"""

        expected = """\
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

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)

    def test_data_annotations_other02(self):
        """Don't error out if a legacy id is bad.
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
<head>
<title data-sb-obj="title">My page</title>
</head>
<body>
<span data-sb-id="">suscipit</span>
<span data-sb-id="999999999999999999999999999999999999999999999999999999999">finibus</span>
<span data-sb-id="abc">varius</span>
</body>
</html>
"""

        expected = """\
<!DOCTYPE html>
<html>
<head>
<title data-scrapbook-elem="title">My page</title>
</head>
<body>
<span data-scrapbook-id="">suscipit</span>
<span data-scrapbook-id="999999999999999999999999999999999999999999999999999999999">finibus</span>
<span data-scrapbook-id="abc">varius</span>
</body>
</html>
"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)

    def test_data_combine(self):
        """Convert legacy ScrapBook combine page."""
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Sample combine page</title>
<link rel="stylesheet" href="chrome://scrapbook/skin/combine.css" media="all">
<link rel="stylesheet" href="chrome://scrapbook/skin/annotation.css" media="all">
</head>
<body>

<!--Page1-->
<cite class="scrapbook-header">
\t<img src="chrome://scrapbook/skin/treeitem.png" height="16" width="16">
\t<a href="http://example.com">Page1</a>
</cite>
<div id="item20200101000000">
<div id="item20200101000000html">
<div id="item20200101000000body">
Page1 content
</div>
</div>
</div>

<!--Page2-->
<cite class="scrapbook-header">
\t<img src="chrome://scrapbook/skin/treeitem.png" height="16" width="16">
\t<a href="http://example.com">Page1</a>
</cite>
<div id="item20200101000000">
<div id="item20200101000000html">
<div id="item20200101000000body">
Page2 content
</div>
</div>
</div>

<!--Page3-->
<cite class="scrapbook-header">
\t<img src="chrome://scrapbook/skin/treenotex.png" height="16" width="16">
\t<a href="http://example.com">Page3</a>
</cite>
<div id="item20200102000000">
<div id="item20200102000000html">
<div id="item20200102000000body">
Page3 content
</div>
</div>
</div>
"""

        expected = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Sample combine page</title>
<style data-scrapbook-elem="custom-css">body { margin: 0px; background-color: #FFFFFF; } cite.scrapbook-header { clear: both; display: block; padding: 3px 6px; font-family: "MS UI Gothic","Tahoma","Verdana","Arial","Sans-Serif","Helvetica"; font-style: normal; font-size: 12px; background-color: InfoBackground; border: 1px solid ThreeDShadow; } cite.scrapbook-header img { vertical-align: middle; } cite.scrapbook-header a { color: InfoText; text-decoration: none; } cite.scrapbook-header a[href]:hover { color: #3388FF; } cite.scrapbook-header a.marked { font-weight: bold; } cite.scrapbook-header a.combine { color: blue; } cite.scrapbook-header a.bookmark { color: limegreen; } cite.scrapbook-header a.notex { color: rgb(80,0,32); } </style>

</head>
<body>

<!--Page1-->
<cite class="scrapbook-header">
\t<img src="treeitem.png" height="16" width="16">
\t<a href="http://example.com">Page1</a>
</cite>
<div id="item20200101000000">
<div id="item20200101000000html">
<div id="item20200101000000body">
Page1 content
</div>
</div>
</div>

<!--Page2-->
<cite class="scrapbook-header">
\t<img src="treeitem.png" height="16" width="16">
\t<a href="http://example.com">Page1</a>
</cite>
<div id="item20200101000000">
<div id="item20200101000000html">
<div id="item20200101000000body">
Page2 content
</div>
</div>
</div>

<!--Page3-->
<cite class="scrapbook-header">
\t<img src="treenotex-1.png" height="16" width="16">
\t<a href="http://example.com">Page3</a>
</cite>
<div id="item20200102000000">
<div id="item20200102000000html">
<div id="item20200102000000body">
Page3 content
</div>
</div>
</div>
"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        with open(os.path.join(self.test_input, '20200101000000000', 'treenotex.png'), 'wb'):
            pass

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        self.assertEqual(glob_files(self.test_output), {
            os.path.join(self.test_output, ''),
            os.path.join(self.test_output, '20200101000000000'),
            os.path.join(self.test_output, '20200101000000000', 'index.html'),
            os.path.join(self.test_output, '20200101000000000', 'treeitem.png'),
            os.path.join(self.test_output, '20200101000000000', 'treenotex.png'),
            os.path.join(self.test_output, '20200101000000000', 'treenotex-1.png'),
        })
        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)

    def test_data_other(self):
        """Convert other legacy ScrapBook attributes.
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
<head>
<title>My page</title>
<link rel="stylesheet" href="urn:scrapbook-download-error:https://example.com/style.css">
</head>
<body>
<blockquote><img src="urn:scrapbook-download-skip:https://example.com/picture.jpg"></blockquote>
<blockquote><a data-sb-orig-href="javascript:alert('hello');">script</a></blockquote>
<blockquote><a href="mypage.html" data-sb-indepth="true">in-depth</a></blockquote>
</body>
</html>
"""

        expected = """\
<!DOCTYPE html>
<html>
<head>
<title>My page</title>
<link rel="stylesheet" href="urn:scrapbook-download-error:https://example.com/style.css">
</head>
<body>
<blockquote><img src="urn:scrapbook-download-skip:https://example.com/picture.jpg"></blockquote>
<blockquote><a data-scrapbook-orig-attr-href="javascript:alert('hello');">script</a></blockquote>
<blockquote><a href="mypage.html" data-sb-indepth="true">in-depth</a></blockquote>
</body>
</html>
"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)

    def test_data_loaders_replace(self):
        """Replace old loaders if there's a change.
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body>
<span data-sb-obj="custom">foo</span>
<scrapbook-sticky data-scrapbook-elem="sticky" class="styled" style="width: 250px; height: 100px; left: 313px; top: 135px;">abc</scrapbook-sticky>
<style data-scrapbook-elem="annotation-css"></style>
<script data-scrapbook-elem="annotation-loader"></script>
</body></html>"""

        expected_regex = """<html><body>
<span data-scrapbook-elem="custom">foo</span>
<scrapbook-sticky data-scrapbook-elem="sticky" class="styled" style="width: 250px; height: 100px; left: 313px; top: 135px;">abc</scrapbook-sticky>


<style data-scrapbook-elem="annotation-css">(?:[^<]*(?:<(?!/style>)[^<]*)*)</style><script data-scrapbook-elem="annotation-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertRegex(output, expected_regex)

    def test_data_loaders_unchanged(self):
        """Don't update loaders if there's no change detected.
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body>
<style data-scrapbook-elem="annotation-css"></style>
<script data-scrapbook-elem="annotation-loader"></script>
</body></html>"""

        expected = """<html><body>
<style data-scrapbook-elem="annotation-css"></style>
<script data-scrapbook-elem="annotation-loader"></script>
</body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)

    def test_data_skip_special_tags(self):
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
<span data-sb-obj="annotation">foo</span>
</xmp>
<template>
<span data-sb-obj="annotation">foo</span>
</template>
<svg>
<text data-sb-obj="annotation">foo</text>
</svg>
<math>
<mtext data-sb-obj="annotation">foo</mtext>
</math>
</body>
</html>
"""

        expected = """\
<!DOCTYPE html>
<html>
<body>
<xmp>
<span data-sb-obj="annotation">foo</span>
</xmp>
<template>
<span data-sb-obj="annotation">foo</span>
</template>
<svg>
<text data-sb-obj="annotation">foo</text>
</svg>
<math>
<mtext data-sb-obj="annotation">foo</mtext>
</math>
</body>
</html>
"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_legacy=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)


class TestConvertDataFilesV1(Test):
    def test_skip_postit(self):
        """Do not touch postit items (even if HTML content happens to meet the criteria).
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': 'postit',
                'index': '20200101000000000/index.html',
            },
        })

        input = r"""\
<!DOCTYPE html><html><head>\
<meta charset="UTF-8">\
<meta name="viewport" content="width=device-width">\
<style>pre { white-space: pre-wrap; overflow-wrap: break-word; }</style>\
</head><body><pre>
postit page content
</pre><div data-scrapbook-shadowroot="{&quot;data&quot;:&quot;\n<div>Sub-content.</div>\n\n<p data-scrapbook-shadowroot=\&quot;{&amp;quot;data&amp;quot;:&amp;quot;\\n<div>Deep sub-content.</div>\\n&amp;quot;,&amp;quot;mode&amp;quot;:&amp;quot;open&amp;quot;}\&quot;>Hidden content.</p>&quot;,&quot;mode&quot;:&quot;open&quot;}">Hidden content.</div></body><script data-scrapbook-elem="basic-loader">dummy</script></html>"""  # noqa: E501

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, input)

    def test_folder_data_loaders_unchanged(self):
        """Don't update loaders if there's no change detected.
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body>
<style data-scrapbook-elem="annotation-css"></style>
<script data-scrapbook-elem="annotation-loader"></script>
</body></html>"""

        expected = """<html><body>
<style data-scrapbook-elem="annotation-css"></style>
<script data-scrapbook-elem="annotation-loader"></script>
</body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)

    def test_folder_data_canvas_loader(self):
        """Migrate [data-scrapbook-elem="canvas-loader"].
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body>foo</body><script data-scrapbook-elem="canvas-loader"></script></html>"""

        expected_regex = """<html><body>foo<script data-scrapbook-elem="basic-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertRegex(output, expected_regex)

    def test_folder_data_shadowroot_loader(self):
        """Migrate [data-scrapbook-elem="shadowroot-loader"].
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = """<html><body>foo</body><script data-scrapbook-elem="shadowroot-loader"></script></html>"""

        expected_regex = """<html><body>foo<script data-scrapbook-elem="basic-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertRegex(output, expected_regex)

    def test_folder_data_shadowroot(self):
        """Migrate [data-scrapbook-shadowroot].
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000/index.html',
            },
        })

        input = r"""<html><body>foo<div data-scrapbook-shadowroot="{&quot;data&quot;:&quot;\n<div>Sub-content.</div>\n\n<p data-scrapbook-shadowroot=\&quot;{&amp;quot;data&amp;quot;:&amp;quot;\\n<div>Deep sub-content.</div>\\n&amp;quot;,&amp;quot;mode&amp;quot;:&amp;quot;open&amp;quot;}\&quot;>Hidden content.</p>&quot;,&quot;mode&quot;:&quot;open&quot;}">Hidden content.</div></body><script data-scrapbook-elem="basic-loader">dummy</script></html>"""  # noqa: E501

        expected_regex = """<html><body>foo<div data-scrapbook-shadowdom="
&lt;div&gt;Sub-content.&lt;/div&gt;

&lt;p data-scrapbook-shadowdom=&quot;
&amp;lt;div&amp;gt;Deep sub-content.&amp;lt;/div&amp;gt;
&quot;&gt;Hidden content.&lt;/p&gt;">Hidden content.</div><script data-scrapbook-elem="basic-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertRegex(output, expected_regex)

    def test_folder_data_skip_special_tags(self):
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
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</xmp>
<template>
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</template>
<svg>
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</svg>
<math>
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</math>
</body>
</html>
"""

        expected = """\
<!DOCTYPE html>
<html>
<body>
<xmp>
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</xmp>
<template>
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</template>
<svg>
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</svg>
<math>
<div data-scrapbook-shadowroot='{"data":"foo", "mode": "open"}'></div>
</math>
</body>
</html>
"""

        index_file = os.path.join(self.test_input, '20200101000000000', 'index.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000', 'index.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertEqual(output, expected)

    def test_htz_data_shadowroot(self):
        """Migrate [data-scrapbook-shadowroot].
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000.htz',
            },
        })

        input = r"""<html><body>foo<div data-scrapbook-shadowroot="{&quot;data&quot;:&quot;\n<div>Sub-content.</div>\n\n<p data-scrapbook-shadowroot=\&quot;{&amp;quot;data&amp;quot;:&amp;quot;\\n<div>Deep sub-content.</div>\\n&amp;quot;,&amp;quot;mode&amp;quot;:&amp;quot;open&amp;quot;}\&quot;>Hidden content.</p>&quot;,&quot;mode&quot;:&quot;open&quot;}">Hidden content.</div></body><script data-scrapbook-elem="basic-loader">dummy</script></html>"""  # noqa: E501

        expected_regex = """<html><body>foo<div data-scrapbook-shadowdom="
&lt;div&gt;Sub-content.&lt;/div&gt;

&lt;p data-scrapbook-shadowdom=&quot;
&amp;lt;div&amp;gt;Deep sub-content.&amp;lt;/div&amp;gt;
&quot;&gt;Hidden content.&lt;/p&gt;">Hidden content.</div><script data-scrapbook-elem="basic-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000.htz')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with zipfile.ZipFile(index_file, 'w') as zh:
            zh.writestr('index.html', input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        index_file = os.path.join(self.test_output, '20200101000000000.htz')
        with zipfile.ZipFile(index_file, 'r') as zh:
            output = zh.read('index.html').decode('UTF-8')
            self.assertRegex(output, expected_regex)

    def test_htz_timestamp(self):
        """Don't touch ZIP file if no content is changed.
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000.htz',
            },
        })

        input = r"""<html><body>foo</body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000.htz')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with zipfile.ZipFile(index_file, 'w') as zh:
            zh.writestr('index.html', input)

        input_mtime = os.stat(index_file).st_mtime_ns

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        index_file = os.path.join(self.test_output, '20200101000000000.htz')
        with zipfile.ZipFile(index_file, 'r') as zh:
            output = zh.read('index.html').decode('UTF-8')

        output_mtime = os.stat(index_file).st_mtime_ns

        self.assertEqual(output, input)
        self.assertEqual(input_mtime, output_mtime)

    def test_maff_data_shadowroot(self):
        """Migrate [data-scrapbook-shadowroot].
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000.maff',
            },
        })

        input = r"""<html><body>foo<div data-scrapbook-shadowroot="{&quot;data&quot;:&quot;\n<div>Sub-content.</div>\n\n<p data-scrapbook-shadowroot=\&quot;{&amp;quot;data&amp;quot;:&amp;quot;\\n<div>Deep sub-content.</div>\\n&amp;quot;,&amp;quot;mode&amp;quot;:&amp;quot;open&amp;quot;}\&quot;>Hidden content.</p>&quot;,&quot;mode&quot;:&quot;open&quot;}">Hidden content.</div></body><script data-scrapbook-elem="basic-loader">dummy</script></html>"""  # noqa: E501

        expected_regex = """<html><body>foo<div data-scrapbook-shadowdom="
&lt;div&gt;Sub-content.&lt;/div&gt;

&lt;p data-scrapbook-shadowdom=&quot;
&amp;lt;div&amp;gt;Deep sub-content.&amp;lt;/div&amp;gt;
&quot;&gt;Hidden content.&lt;/p&gt;">Hidden content.</div><script data-scrapbook-elem="basic-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000.maff')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with zipfile.ZipFile(index_file, 'w') as zh:
            zh.writestr('20200101000000000/index.html', input)
            zh.writestr('20200101000000000/index.rdf', """dummy""")

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        index_file = os.path.join(self.test_output, '20200101000000000.maff')
        with zipfile.ZipFile(index_file, 'r') as zh:
            output = zh.read('20200101000000000/index.html').decode('UTF-8')
            self.assertRegex(output, expected_regex)

    def test_maff_timestamp(self):
        """Don't touch ZIP file if no content is changed.
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000.maff',
            },
        })

        input = r"""<html><body>foo</body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000.maff')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with zipfile.ZipFile(index_file, 'w') as zh:
            zh.writestr('20200101000000000/index.html', input)
            zh.writestr('20200101000000000/index.rdf', """dummy""")

        input_mtime = os.stat(index_file).st_mtime_ns

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        index_file = os.path.join(self.test_output, '20200101000000000.maff')
        with zipfile.ZipFile(index_file, 'r') as zh:
            output = zh.read('20200101000000000/index.html').decode('UTF-8')

        output_mtime = os.stat(index_file).st_mtime_ns

        self.assertEqual(output, input)
        self.assertEqual(input_mtime, output_mtime)

    def test_single_file_data_shadowroot(self):
        """Migrate [data-scrapbook-shadowroot].
        """
        self.init_book(self.test_input, meta={
            '20200101000000000': {
                'type': '',
                'index': '20200101000000000.html',
            },
        })

        input = r"""<html><body>foo<div data-scrapbook-shadowroot="{&quot;data&quot;:&quot;\n<div>Sub-content.</div>\n\n<p data-scrapbook-shadowroot=\&quot;{&amp;quot;data&amp;quot;:&amp;quot;\\n<div>Deep sub-content.</div>\\n&amp;quot;,&amp;quot;mode&amp;quot;:&amp;quot;open&amp;quot;}\&quot;>Hidden content.</p>&quot;,&quot;mode&quot;:&quot;open&quot;}">Hidden content.</div></body><script data-scrapbook-elem="basic-loader">dummy</script></html>"""  # noqa: E501

        expected_regex = """<html><body>foo<div data-scrapbook-shadowdom="
&lt;div&gt;Sub-content.&lt;/div&gt;

&lt;p data-scrapbook-shadowdom=&quot;
&amp;lt;div&amp;gt;Deep sub-content.&amp;lt;/div&amp;gt;
&quot;&gt;Hidden content.&lt;/p&gt;">Hidden content.</div><script data-scrapbook-elem="basic-loader">(?:[^<]*(?:<(?!/script>)[^<]*)*)</script></body></html>"""

        index_file = os.path.join(self.test_input, '20200101000000000.html')
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='UTF-8') as fh:
            fh.write(input)

        for _info in migrate.run(self.test_input, self.test_output, convert_v1=True):
            pass

        with open(os.path.join(self.test_output, '20200101000000000.html'), encoding='UTF-8') as fh:
            output = fh.read()
            self.assertRegex(output, expected_regex)


if __name__ == '__main__':
    unittest.main()
