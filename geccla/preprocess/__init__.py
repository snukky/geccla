import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


MOSES_ENTITIES = "&amp; &#124; &lt; &gt; &apos; &quot; &#91; &#93;".split()


def deescape_moses_entities_in_files(input_file, output_file):
    output_io = open(output_file, 'w')
    with open(input_file, 'r') as input_io:
        for line in input_io:
            output_io.write(deescape_moses_entities(line))
    output_io.close()


def escape_moses_entities(text):
    if any(entity in text for entity in MOSES_ENTITIES):
        return text
    return (
        text.replace('&', '&amp;')
            .replace('|', '&#124;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace("'", '&apos;')
            .replace('"', '&quot;')
            .replace('[', '&#91;')
            .replace(']', '&#93;')
        )

def deescape_moses_entities(text):
    return (  
        text.replace('&amp;',  '&')
            .replace('&#124;', '|')
            .replace('&lt;',   '<')
            .replace('&gt;',   '>')
            .replace('&apos;', "'")
            .replace('&quot;', '"')
            .replace('&#91;',  '[')
            .replace('&#93;',  ']')
        )
