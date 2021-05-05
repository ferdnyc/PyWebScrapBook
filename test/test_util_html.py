from unittest import mock
import unittest
import os
from webscrapbook.util.html import Markup, MarkupTag, HtmlRewriter

root_dir = os.path.abspath(os.path.dirname(__file__))

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = 8192

class TestMarkupTag(Test):
    def test_html01(self):
        m = MarkupTag(
            type='starttag',
            tag='input',
            attrs=[
                ('type', 'checkbox'),
                ('checked', None),
                ],
            )
        self.assertEqual(str(m), '<input type="checkbox" checked>')

    def test_html02(self):
        m = MarkupTag(
            type='starttag',
            tag='div',
            attrs=[
                ('title', '中文<span title="foo">bar</span>'),
                ],
            )
        self.assertEqual(str(m), '<div title="中文&lt;span title=&quot;foo&quot;&gt;bar&lt;/span&gt;">')

    def test_xhtml01(self):
        m = MarkupTag(
            is_xhtml=True,
            type='starttag',
            tag='input',
            attrs=[
                ('type', 'checkbox'),
                ('checked', None),
                ],
            is_self_end=True,
            )
        self.assertEqual(str(m), '<input type="checkbox" checked="checked" />')

    def test_xhtml02(self):
        m = MarkupTag(
            is_xhtml=True,
            type='starttag',
            tag='div',
            attrs=[
                ('title', '中文<span title="foo">bar</span>'),
                ],
            )
        self.assertEqual(str(m), '<div title="中文&lt;span title=&quot;foo&quot;&gt;bar&lt;/span&gt;">')

class TestHtmlRewriter(Test):
    def test_loads_html01(self):
        input = """<!DOCTYPE html>"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html02(self):
        input = """<meta charset="UTF-8">"""
        parsed = """<meta charset="UTF-8"></meta>"""
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html03(self):
        input = """\
<style>
<!--/*--><![CDATA[/*><!--*/
body::after { content: "<my> <" "/style> & godness"; }
/*]]>*/-->
</style>
"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html04(self):
        input = """\
<script>
<!--//--><![CDATA[//><!--
console.log('test <my> <' + '/script> & tag');
//--><!]]>
</script>
"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html05(self):
        input = """\
foo&nbsp;&nbsp;&nbsp;中文<br>
King&apos;s &quot;123&quot; &lt; &amp; &gt; 456 (escaped)<br>
King's "123" < & > 456 (unescaped)<br>
"""
        parsed = """\
foo&nbsp;&nbsp;&nbsp;中文<br></br>
King&apos;s &quot;123&quot; &lt; &amp; &gt; 456 (escaped)<br></br>
King's "123" < & > 456 (unescaped)<br></br>
"""
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html06(self):
        input = """<input type="checkbox" checked>"""
        parsed = """<input type="checkbox" checked></input>"""
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html07(self):
        input = """<textarea>plain <div> text may be escaped &lt; &amp; &gt;</textarea>"""
        parsed = """<textarea>plain <div> text may be escaped &lt; &amp; &gt;</textarea>"""
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html08(self):
        input = """<SPaN TITLE="mytitle">Tag with mixed case</SpAN>"""
        parsed = input
        reserialized = """<span title="mytitle">Tag with mixed case</span>"""

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html09(self):
        input = """<input type="number"/>"""
        parsed = """<input type="number"/></input>"""
        reserialized = """<input type="number" /></input>"""

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html10(self):
        input = """<div/>non-void-html-element-start-tag-with-trailing-solidus</div>"""
        parsed = input
        reserialized = """<div />non-void-html-element-start-tag-with-trailing-solidus</div>"""

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html11(self):
        input = """<!UNKONWN decl>"""
        parsed = input
        reserialized = """<!--UNKONWN decl-->"""

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html12(self):
        input = """<![CDATA[x<y]]>"""
        parsed = input
        reserialized = """<!CDATA[x<y>"""

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html13(self):
        input = """<![if sth]>"""
        parsed = input
        reserialized = """<!if sth>"""

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html14(self):
        input = """<svg><circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" /><text x="25" y="40">demo</text></svg>"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html15(self):
        input = """<svg><circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow"><text x="25" y="40">demo</text></svg>"""
        parsed = """<svg><circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow"><text x="25" y="40">demo</text></circle></svg>"""
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html16(self):
        input = """<svg><br/></svg>"""
        parsed = input
        reserialized = """<svg><br /></svg>"""

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html17(self):
        input = """<svg><br></svg>"""
        parsed = """<svg><br></br></svg>"""
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_html18(self):
        input = """\
<math>
  <mrow>
    <mi>x</mi>
    <mo>=</mo>
    <mfrac>
      <mrow>
        <mo form="prefix">&#x2212;<!-- − --></mo>
        <mi>b</mi>
        <mo>&#x00B1;<!-- &PlusMinus; --></mo>
        <msqrt>
          <msup>
            <mi>b</mi>
            <mn>2</mn>
          </msup>
          <mo>&#x2212;<!-- − --></mo>
          <mn>4</mn>
          <mo>&#x2062;<!-- &InvisibleTimes; --></mo>
          <mi>a</mi>
          <mo>&#x2062;<!-- &InvisibleTimes; --></mo>
          <mi>c</mi>
        </msqrt>
      </mrow>
      <mrow>
        <mn>2</mn>
        <mo>&#x2062;<!-- &InvisibleTimes; --></mo>
        <mi>a</mi>
      </mrow>
    </mfrac>
  </mrow>
</math>
"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter().loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml01(self):
        input = """<?xml version="1.0" encoding="UTF-8"?>"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml02(self):
        input = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml03(self):
        input = """<meta charset="UTF-8" />"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml04(self):
        input = """\
<style>
<!--/*--><![CDATA[/*><!--*/
body::after { content: "<my> <" "/style> & godness"; }
/*]]>*/-->
</style>
"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml05(self):
        input = """\
<script type="text/javascript">
<!--//--><![CDATA[//><!--
console.log('test <my> <' + '/script> & tag');
//--><!]]>
</script>
"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml06(self):
        input = """\
foo&nbsp;&nbsp;&nbsp;中文<br/>
King&apos;s &quot;123&quot; &lt; &amp; &gt; 456 (escaped)<br/>
"""
        parsed = input
        reserialized = """\
foo&nbsp;&nbsp;&nbsp;中文<br />
King&apos;s &quot;123&quot; &lt; &amp; &gt; 456 (escaped)<br />
"""

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml07(self):
        input = """<input type="checkbox" checked="checked" />"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml08(self):
        input = """<textarea>text need escaped &lt; &amp; &gt;</textarea>"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml09(self):
        input = """<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" /><text x="25" y="40">demo</text></svg>"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml10(self):
        input = """<svg xmlns="http://www.w3.org/2000/svg"><br/></svg>"""
        parsed = input
        reserialized = """<svg xmlns="http://www.w3.org/2000/svg"><br /></svg>"""

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml11(self):
        input = """<svg xmlns="http://www.w3.org/2000/svg"><br></br></svg>"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)

    def test_loads_xhtml12(self):
        input = """\
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mrow>
    <mi>x</mi>
    <mo>=</mo>
    <mfrac>
      <mrow>
        <mo form="prefix">&#x2212;<!-- − --></mo>
        <mi>b</mi>
        <mo>&#x00B1;<!-- &PlusMinus; --></mo>
        <msqrt>
          <msup>
            <mi>b</mi>
            <mn>2</mn>
          </msup>
          <mo>&#x2212;<!-- − --></mo>
          <mn>4</mn>
          <mo>&#x2062;<!-- &InvisibleTimes; --></mo>
          <mi>a</mi>
          <mo>&#x2062;<!-- &InvisibleTimes; --></mo>
          <mi>c</mi>
        </msqrt>
      </mrow>
      <mrow>
        <mn>2</mn>
        <mo>&#x2062;<!-- &InvisibleTimes; --></mo>
        <mi>a</mi>
      </mrow>
    </mfrac>
  </mrow>
</math>
"""
        parsed = input
        reserialized = parsed

        markups = HtmlRewriter(is_xhtml=True).loads(input)
        self.assertEqual(''.join(str(m) for m in markups if not m.hidden), input)
        self.assertEqual(''.join(str(m) for m in markups), parsed)
        for m in markups: m.src = None
        self.assertEqual(''.join(str(m) for m in markups), reserialized)


if __name__ == '__main__':
    unittest.main()
