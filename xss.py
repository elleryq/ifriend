import re
from html.parser import HTMLParser
from html import escape
from urllib.parse import urlparse
from html.entities import entitydefs
from xml.sax.saxutils import quoteattr


class XssFilter(HTMLParser):
    """繼承 HTMLParser，利用 HTMLParser 遍訪所有 tag 並進行處理。"""

    def __init__(self):
        HTMLParser.__init__(self)
        self.result = ""
        self.start = []
        self.open_tags = []

        # 允許的 tag
        self.permitted_tags = [
            'a', 'img', 'br', 'strong', 'b', 'code', 'pre',
            'p', 'div', 'em', 'span', 'h1', 'h2', 'h3', 'h4',
            'h5', 'h6', 'blockquote', 'ul', 'ol', 'tr', 'th', 'td',
            'hr', 'li', 'u', 's', 'table', 'thead', 'tbody',
            'caption', 'small', 'q', 'sup', 'sub', 'cite', 'i',
        ]

        # 沒有 close 的 tag
        self.requires_no_close = [
            'img',
            'hr',
            'br',
        ]

        # 有些 tag 會需要 attribute，只讓允許的 attribute 通過。
        # 沒有列在這裡的，不允許有 attribute
        self.allowed_attributes = {
            'a': ['href', 'target', 'rel', 'title'],
            'img': ['src', 'width', 'height', 'alt', 'align'],
            'blockquote': ['type'],
            'table': ['border', 'cellpadding', 'cellspacing'],
        }
        self.common_attrs = ["style", "class", "name"]

        # 只允許指定的 schema 出現。
        self.allowed_schemes = ['http','https','ftp']

        # 預先編譯 regular expression
        self._regex_url = re.compile(r'^(http|https|ftp)://.*', re.I | re.S)
        self._regex_style_1 = re.compile(r'(\\|&#|/\*|\*/)', re.I)
        self._regex_style_2 = re.compile(r'e.*x.*p.*r.*e.*s.*s.*i.*o.*n', re.I | re.S)

    def handle_data(self, data):
        """處理 element 內容"""
        if data:
            self.result += self._htmlspecialchars(data)

    def handle_charref(self, ref):
        """處理特殊字元"""
        if len(ref) < 7 and ref.isdigit():
            self.result += f'&#{ref};'
        else:
            self.result += self._htmlspecialchars(f'&#{ref}')

    def handle_entityref(self, ref):
        """處理實體參考"""
        if ref in entitydefs:
            self.result += f'&{ref};'
        else:
            self.result += self._htmlspecialchars(f'&{ref}')

    def handle_comment(self, comment):
        """處理註解"""
        if comment:
            self.result += self._htmlspecialchars(f"<!--{comment}-->")

    def handle_startendtag(self, tag, attrs):
        """處理有開始跟結束的 tag"""
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        """處理開始 tag"""

        # 不在白名單內，移除
        if tag not in self.permitted_tags:
            return

        # 檢查是否需要加上 close tag
        end_diagonal = ' /' if tag in self.requires_no_close else ''
        if not end_diagonal:
            self.start.append(tag)

        # 清理 attributes
        attdict = {}
        for attr in attrs:
            attdict[attr[0]] = attr[1]
        attdict = self._strip_attr(attdict, tag)

        # 有指定的 node 要處理，這裡檢查是否有對應的 node_xxx 函式，有就呼叫。
        # 沒有則呼叫 node_default
        if hasattr(self, f"node_{tag}"):
            attdict = getattr(self, f"node_{tag}")(attdict)
        else:
            attdict = self.node_default(attdict)

        # 加上 tag
        attrs = []
        for (key, value) in attdict.items():
            attrs.append('{}="{}"'.format(key, self._htmlspecialchars(value)))
        attrs = (' ' + ' '.join(attrs)) if attrs else ''
        self.result += f'<{tag}{attrs}{end_diagonal}>'

    def handle_endtag(self, tag):
        """處理 close tag"""
        if self.start and tag == self.start[len(self.start) - 1]:
            self.result += f'</{tag}>'
            self.start.pop()

    def node_a(self, attrs):
        """處理 a tag"""
        attrs = self._common_attr(attrs)
        attrs = self._get_link(attrs, "href")
        attrs = self._set_attr_default(attrs, "target", "_blank")
        attrs = self._limit_attr(attrs, {
            "target": ["_blank", "_self"]
        })
        return attrs

    def node_default(self, attrs):
        """處理一般 tag"""
        attrs = self._common_attr(attrs)
        return attrs

    def strip(self, rawstring):
        """
        清理掉可能有傷害的HTML/Javascript並回傳結果。

        Args:
          rawstring: Raw HTML

        Returns:
          str: 清理後的結果
        """
        self.result = ""
        self.feed(rawstring)
        for endtag in self.open_tags:
            if endtag not in self.requires_no_close:
                self.result += f"</{endtag}>"
        return self.result

    def _htmlspecialchars(self, html):
        """Escape 特殊字元"""
        return escape(html, quote=True).replace(':','&#58;')

    def _common_attr(self, attrs):
        """處理一般的 attribute"""
        attrs = self._get_style(attrs)
        return attrs

    def _strip_attr(self, attrs, tag):
        """清理掉不在白名單內的 attribute"""
        if tag in self.allowed_attributes:
            other = self.allowed_attributes.get(tag)
        else:
            other = []

        _attrs = {}
        if attrs:
            for (key, value) in attrs.items():
                if key in self.common_attrs + other:
                    _attrs[key] = value
        return _attrs

    def _get_style(self, attrs):
        """確定 style 內容是正確的"""
        if "style" in attrs:
            attrs["style"] = self._true_style(attrs.get("style"))
        return attrs

    def _true_style(self, style):
        """處理 style"""
        if style:
            style = self._regex_style_1.sub('_', style)
            style = self._regex_style_2.sub('_', style)
        return style

    def _get_link(self, attrs, name):
        """處理 url"""
        if name in attrs:
            attrs[name] = self._true_url(attrs[name])
        return attrs

    def _true_url(self, url):
        """檢查並修正 url"""
        if self._regex_url.match(url):
            return url
        else:
            return "http://%s" % url

    def _set_attr_default(self, attrs, name, default=''):
        """設置 attribute 的值"""
        if name not in attrs:
            attrs[name] = default
        return attrs

    def _limit_attr(self, attrs, limit={}):
        """限制 attribute 的值，若不允許，則刪除"""
        for (key, value) in limit.items():
            if key in attrs and attrs[key] not in value:
                del attrs[key]
        return attrs


if __name__ == "__main__":
    # test cases
    cases = [
        '<html code>',
        '''<p><img src=1 onerror=alert(/xss/)></p><div class="left"><a href='javascript:prompt(1)'><br />hehe</a></div><p id="test" onmouseover="alert(1)">&gt;M<svg><a href="https://www.baidu.com" target="self" >MM</a></p>''',
    ]
    for case in cases:
        parser = XssFilter()
        print(parser.strip(case))

