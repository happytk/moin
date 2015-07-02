"""
    MoinMoin - Parser for Markdown

    Syntax:

        To use in a code block:
    
            {{{{#!text_markdown
            <add markdown text here>
            }}}}

        To use for an entire page:

            #format text_markdown
            <add markdown text here>

    @copyright: 2009 by Jason Fruit (JasonFruit at g mail dot com)
    @license: GNU GPL, see http://www.gnu.org/licenses/gpl for details

"""


import hashlib, re
import markdown as markdown_lib


Dependencies = ['user']

def gfm(text):
    """Processes Markdown according to GitHub Flavored Markdown spec."""
    extractions = {}

    def extract_pre_block(matchobj):
        match = matchobj.group(0)
        hashed_match = hashlib.md5(match.encode('utf-8')).hexdigest()
        extractions[hashed_match] = match
        result = "{gfm-extraction-%s}" % hashed_match
        return result

    def escape_underscore(matchobj):
        match = matchobj.group(0)

        if match.count('_') > 1:
            return re.sub('_', '\_', match)
        else:
            return match

    def newlines_to_brs(matchobj):
        match = matchobj.group(0)
        if re.search("\n{2}", match):
            return match
        else:
            match = match.strip()
            return match + "  \n"

    def insert_pre_block(matchobj):
        string = "\n\n" + extractions[matchobj.group(1)]
        return string

    def wikiword(matchobj):
        string = matchobj.group(0)
        return '[[%s]]' % string

    # text = re.sub("<pre>.*?<\/pre>", extract_pre_block, text, flags=re.S)
    # text = re.sub("(^(?! {4}|\t)\w+_\w+_\w[\w_]*)", escape_underscore, text)
    # text = re.sub("^[\w\<][^\n]*\n+", newlines_to_brs, text, flags=re.M)
    # text = re.sub("\{gfm-extraction-([0-9a-f]{32})\}", insert_pre_block, text)
    text = re.sub("([A-Z][a-z0-9]+){2,}", wikiword, text)

    return text

def markdown(request, text):
    """Processes GFM then converts it to HTML."""
    text = gfm(text)
    # text = markdown_lib.markdown(text, extensions=['extra', 'toc', 'fenced_code', 'codehilite', 'nl2br', 'wikilinks' 'sane_lists'])
    extensions = ['extra', 'toc', 'fenced_code', 'codehilite', 'nl2br','sane_lists', 'wikilinks']
    extension_configs = {'wikilinks': [
                                     ('base_url', request.getScriptname() + '/'), 
                                     ('end_url', ''),
                                     ('html_class', 'wiki') ]}
    text = markdown_lib.markdown(text, extensions=extensions, extension_configs=extension_configs)
    return text

class Parser:
    """
    A thin wrapper around a Python implementation
    (http://www.freewisdom.org/projects/python-markdown/) of John
    Gruber's Markdown (http://daringfireball.net/projects/markdown/)
    to make it suitable for use with MoinMoin.
    """
    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
    def format(self, formatter):
        text = markdown(self.request, self.raw)
        try:
           self.request.write(formatter.rawHTML(text))
        except:
            self.request.write(formatter.escapedText(text))
        # self.request.write(output_html)