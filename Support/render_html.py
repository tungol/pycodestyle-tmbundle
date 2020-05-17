#!/usr/bin/env python3
# encoding: utf-8

import sys
import os
import urllib.parse
import html
import shlex
import subprocess

TM_SUPPORT_PATH = os.environ.get("TM_SUPPORT_PATH")


def html_header(title, subtitle):
    # modernized $TM_SUPPORT_PATH/lib/webpreview.py
    script = shlex.quote(f"{TM_SUPPORT_PATH}/lib/webpreview.sh")
    cmd = f'source {script}; html_header "{title}" "{subtitle}"'
    p = subprocess.run(cmd, shell=True, capture_output=True)
    print(p.stdout.decode('utf-8'))


def get_js():
    script_src = os.path.join(os.path.dirname(__file__), "txmt_pep8.js")
    return urllib.parse.quote(script_src)


def parse_lines(fn, lines):
    messages = []
    message = {}
    count = 0
    for line in lines:
        count += 1
        if line.startswith(fn):
            if message:
                messages.append(message)
            count = 0
            fn, lig, col, txt = line.split(':', maxsplit=3)
            txt_code, txt_msg = txt.strip().split(' ', maxsplit=1)
            message = {'filename': fn, 'line_no': int(lig),
                       'col': int(col) - 1, 'txt_msg': txt_msg,
                       'txt_code': txt_code, 'code': [],
                       'pep8': []}
            continue
        if count in (1, 2):
            message['code'].append(line)
        else:
            message['pep8'].append(line)
    if message:
        messages.append(message)
    return messages


def render_pep(lines):
    print('                    ', end='')
    doc = ''.join(lines).lstrip('\n').rstrip()
    for line in html.escape(doc).splitlines():
        if line:
            print(line)
        else:
            print('<br /><br />')


def render_code(line, col):
    offset = col
    code_python = line[0].strip('\n')
    code_python_formated = ('%s<span class=caret>%s</span>%s' %
                            (html.escape(code_python[:offset]),
                             html.escape(code_python[offset:(offset + 1)]),
                             html.escape(code_python[(offset + 1):])))
    return code_python_formated


def render_error(msg, fn):
    txt_code = msg['txt_code']
    url_file = urllib.parse.quote(fn)
    lig = msg['line_no']
    col = msg['col']
    txt_msg = msg['txt_msg']
    code_python = render_code(msg['code'], col)
    print('        ')
    print(f'            <li class="{txt_code}">')
    print('                <code><a href="txmt://open/?url=file://', end='')
    print(f'{url_file}&line={lig}&column={col}"><b>{lig:4d}</b>:', end='')
    print(f'{col:<3d}</a></code>')
    print(f'                   <code><i>{txt_code}</i></code> : {txt_msg}')
    print(f'                <pre class="view_source">{code_python}</pre>')
    print('                <blockquote class="view_pep">')
    render_pep(msg['pep8'])
    print('                </blockquote>')
    print('            </li>')


def render_alternate(messages):
    if not messages:
        print('                <h2>No error</h2>')
        return
    print('                <ul>')
    stats = {}
    for m in messages:
        if m['txt_code'] in stats:
            stats[m['txt_code']]['count'] += 1
            stats[m['txt_code']]['msg'].append(m['txt_msg'])
        else:
            stats[m['txt_code']] = {'count': 1, 'msg': [m['txt_msg']]}

    codes = sorted(list(stats.keys()))
    for code in codes:
        count = stats[code]['count']
        msg = sorted(stats[code]['msg'])[0]
        print()
        print('            <li>')
        print(f'                <code><b>{count:4d}</b>    </code>')
        print(f'                <code><i>{code}</i></code>')
        print(f'                : {msg}')
        print('            </li>')
        print('            ')
    print('</ul>')


OPTIONS = """
        <p style="float:right;">
            <input type="checkbox" id="view_source" title="view source"
                onchange="view(this);" checked="checked" /><label
             for="view_source" title="view source"> view source</label>
            <input type="checkbox" id="view_pep" title="view PEP"
                onchange="view(this);" checked="checked" /><label
             for="view_pep" title="view PEP"> view PEP</label>
            <br />
            <label for="filter_codes"
                title="list of error code to hide">hide :</label>
            <input type="text" id="filter_codes" value="" size="22"
                placeholder="list of error code"
                title="list of error code to hide"
                onkeyup="update_list();"/>
        </p>
"""


def main():
    fn_path = os.environ['TM_FILEPATH']
    fn = os.path.basename(fn_path)
    lines = sys.stdin.readlines()
    messages = parse_lines(fn_path, lines)
    page_title = "PEP-8 Python"
    sub_title = "Python style checker"
    print()
    print('    ', end='')
    html_header(page_title, sub_title)
    print(f'        <script src="file://{get_js()}"')
    print('            type="text/javascript" charset="utf-8">')
    print('        </script>')
    print(OPTIONS.strip('\n'))
    print(f'        <h2>File : {fn}</h2>')
    print('            <ul>')
    for m in messages:
        render_error(m, fn_path)
    print('        ')
    print("            </ul>")
    print("            <p>&nbsp;</p>")
    print('            <div class="alternate">')
    render_alternate(messages)
    print('            </div>')
    print('        </div>')
    print('        </body>')
    print('        </html>')
    print('        ', end='')


if __name__ == "__main__":
    sys.exit(main())
