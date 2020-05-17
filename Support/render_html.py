#!/usr/bin/env python3
# encoding: utf-8
"""Print out an HTML document representing pycodestyle output."""


import sys
import os
import urllib.parse
import html
import shlex
import subprocess

TM_SUPPORT_PATH = os.environ.get("TM_SUPPORT_PATH")
TM_BUNDLE_SUPPORT = os.environ.get("TM_BUNDLE_SUPPORT")


def parse_lines(filename, lines):
    """Parse the output of pycodestyle

    Parameters
    ----------
    filename : str
        name of the file being evaluated
    lines : list of strings
        pycodestyle output, with --show-source and --show-pep8 set.

    Returns
    -------
    messages : list
        each item in the list is a dict containing information about a warning
        or error generated by pycodestyle.
    """
    messages = []
    message = {}
    count = 0
    for line in lines:
        count += 1
        if line.startswith(filename):
            if message:
                messages.append(message)
            count = 0
            filename, line_no, col, txt = line.split(':', maxsplit=3)
            txt_code, txt_msg = txt.strip().split(' ', maxsplit=1)
            message = {'filename': filename, 'line_no': int(line_no),
                       'col': int(col), 'txt_msg': txt_msg,
                       'txt_code': txt_code, 'code': [],
                       'pep8': []}
            continue
        if count in (1, 2):
            # the source line, and the carat showing the column location
            message['code'].append(line)
        else:
            message['pep8'].append(line)
    if message:
        messages.append(message)
    return messages


def render_html_header(title, subtitle):
    """Print standard Textmate HTML top matter"""
    # modernized $TM_SUPPORT_PATH/lib/webpreview.py
    script = shlex.quote(f"{TM_SUPPORT_PATH}/lib/webpreview.sh")
    cmd = f'source {script}; html_header "{title}" "{subtitle}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, check=True)
    print(result.stdout.decode('utf-8'), end='')


# a static block of HTML for showing or hiding parts of error messages
OPTIONS = """
      <p style="float:right;">
        <input type="checkbox" id="view_source" title="view source"
          onchange="view(this);" checked="checked" />
        <label for="view_source" title="view source">view source</label>
        <input type="checkbox" id="view_pep" title="view PEP"
          onchange="view(this);" checked="checked" />
        <label for="view_pep" title="view PEP">view PEP</label>
        <br/>
        <label for="filter_codes" title="list of error codes to hide">
          hide:
        </label>
        <input type="text" id="filter_codes" value="" size="22"
          placeholder="list of error code" title="list of error codes to hide"
          onkeyup="update_list();"/>
      </p>
"""


def render_error(msg, filename):
    """Print and HTML representation of an error message"""
    txt_code = msg['txt_code']
    url_file = urllib.parse.quote(filename)
    lig = msg['line_no']
    col = msg['col']
    txt_msg = msg['txt_msg']
    code_python = render_code(msg['code'], col)
    print(f'        <li class="{txt_code}">')
    print('          <code><a href="txmt://open/?url=file://', end='')
    print(f'{url_file}&line={lig}&column={col}"><b>{lig:4d}</b>:', end='')
    print(f'{col:<3d}</a></code>')
    print(f'          <code><i>{txt_code}</i></code> : {txt_msg}')
    print(f'          <pre class="view_source">{code_python}</pre>')
    print('          <blockquote class="view_pep">')
    render_pep(msg['pep8'])
    print('          </blockquote>')
    print('        </li>')


def render_code(line, offset):
    """Return a string of a line of code, with the error highlighted"""
    source = line[0].strip('\n')
    if offset > len(source):
        source += ' ' * (offset - len(source))
    start = html.escape(source[:offset - 1])
    error = html.escape(source[offset - 1:offset])
    end = html.escape(source[offset:])
    return f'{start}<span class=caret>{error}</span>{end}'


def render_pep(lines):
    """Print the HTML version of a PEP-8 explanation"""
    doc = ''.join(lines).lstrip('\n').rstrip()
    for line in html.escape(doc).splitlines():
        if line:
            print('        ', end='')
            print(line)
        print('            <br/>')


def render_alternate(messages):
    """Print statistics about the messages handled"""
    if not messages:
        print('        <h2>No errors</h2>')
        return
    stats = collect_alternate_stats(messages)
    print('        <ul>')
    render_alternate_stats(stats)
    print('        </ul>')


def collect_alternate_stats(messages):
    """Count how many of each type of error"""
    stats = {}
    for msg in messages:
        if msg['txt_code'] in stats:
            stats[msg['txt_code']]['count'] += 1
            stats[msg['txt_code']]['msg'].append(msg['txt_msg'])
        else:
            stats[msg['txt_code']] = {'count': 1, 'msg': [msg['txt_msg']]}
    return stats


def render_alternate_stats(stats):
    """For each type of error, print HTML showing statistics about it"""
    codes = sorted(list(stats.keys()))
    for code in codes:
        count = stats[code]['count']
        msg = sorted(stats[code]['msg'])[0]
        print('          <li>')
        print(f'            <code><b>{count:4d}</b>    </code>')
        print(f'            <code><i>{code}</i></code> : {msg}')
        print('          </li>')


def render_pycodestyle(lines):
    """Print out an HTML document representing pycodestyle output"""
    fn_path = os.environ['TM_FILEPATH']
    base_filename = os.path.basename(fn_path)
    messages = parse_lines(fn_path, lines)
    js_script = os.path.join(TM_BUNDLE_SUPPORT, "txmt_pep8.js")
    page_title = "pycodestyle"
    sub_title = "Python style checker"
    render_html_header(page_title, sub_title)
    print(f'    <script src="file://{js_script}"')
    print('      type="text/javascript" charset="utf-8">')
    print('    </script>')
    print(OPTIONS.strip('\n'))
    print(f'      <h2>File: {base_filename}</h2>')
    print('      <ul>')
    for message in messages:
        render_error(message, fn_path)
    print("      </ul>")
    print("      <p>&nbsp;</p>")
    print('      <div class="alternate">')
    render_alternate(messages)
    print('      </div>')
    print('    </div>')
    print('  </body>')
    print('</html>')


if __name__ == "__main__":
    sys.exit(render_pycodestyle(sys.stdin.readlines()))
