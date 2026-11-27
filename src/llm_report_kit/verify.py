"""Check the structured news report against its source facts after rendering."""
import re
from itertools import zip_longest

import fitz
from pptx import Presentation

from .deck import day_label, n
from .layout import inspect_layout
from .report import previous_period, query_period


def expected_pages(inputs, source_url):
    query, facts = inputs['query'], inputs['facts']
    if not inputs['data_available']:
        return [([query['keyword'].title(), query_period(query), 'Dataset ' + query['snapshot'],
                  'Data belum tersedia untuk rentang yang diminta.', *inputs['warnings']],
                 [], {source_url})]
    peak, change = facts['peak'], facts['change']
    stories = facts['top_stories'][:3]
    volume_text = ['Volume berita dan tren harian', 'judul tercatat']
    limits_text = ['Batasan data', 'Cakupan sumber', 'Pengelompokan berita']
    if change is None:
        volume_text.append('Perbandingan dengan periode sebelumnya berada di luar cakupan.')
        limits_text.append(previous_period(query) + ' berada di luar cakupan snapshot.')
    else:
        volume_text.append('Periode sebelumnya mencatat %s judul.' % n(change['previous_total']))
    peak_text = ['Puncak dan contoh berita']
    if peak:
        peak_text.extend(['judul pada ' + day_label(peak['at']), *(story['text'] for story in stories)])
    else:
        peak_text.append('Pencarian menghasilkan nol judul dalam periode ini.')
    return [
        ([query['keyword'].title(), query_period(query), 'Dataset ' + query['snapshot']], [], {source_url}),
        (volume_text, [n(facts['total'])], set()),
        (peak_text, [n(peak['count'])] if peak else [], {story['url'] for story in stories}),
        (limits_text, [], {source_url}),
    ]


def check_page(artifact, page, text, links, expected, add):
    phrases, figures, required_links = expected
    lines = {' '.join(line.split()) for line in text.splitlines()}
    normalized = ' '.join(text.split())
    for phrase in phrases:
        if ' '.join(phrase.split()) not in normalized:
            add('figures', artifact, page, 'Expected text missing: %s' % phrase)
    for figure in figures:
        if figure not in lines:
            add('figures', artifact, page, 'Expected displayed figure missing: %s' % figure)
    for link in sorted(links - required_links):
        add('links', artifact, page, 'Unexpected link: %s' % link)
    for link in sorted(required_links - links):
        add('links', artifact, page, 'Required link missing: %s' % link)


def check_chart(chart, facts, page, add):
    if len(chart.series) != 1:
        add('figures', 'pptx', page, 'Daily chart must contain one series')
        return
    labels = [cat.label for cat in chart.plots[0].categories]
    values = chart.series[0].values
    expected = facts['daily_trend']
    for entry, label, count in zip_longest(expected, labels, values):
        if entry is None:
            add('figures', 'pptx', page, 'Unexpected chart point %s: %s' % (label, count))
        elif (label, count) != (day_label(entry['date']), entry['count']):
            add('figures', 'pptx', page, 'Chart point %s expected %s, found %s: %s' %
                (entry['date'], entry['count'], label, count))
    if any(count is None for count in values) or sum(values) != facts['total']:
        add('figures', 'pptx', page, 'Chart series does not sum to %s headlines' % facts['total'])


def check_pptx(pptx, inputs, expected, add):
    deck = Presentation(pptx)
    facts = inputs['facts']
    if len(deck.slides) != len(expected):
        add('layout', 'pptx', None, 'Expected %d slides, found %d' % (len(expected), len(deck.slides)))
    for number, slide in enumerate(deck.slides, 1):
        shapes = slide.shapes
        if number <= len(expected):
            text = '\n'.join(shape.text_frame.text for shape in shapes if shape.has_text_frame)
            links = {rel.target_ref for rel in slide.part.rels.values() if rel.is_external}
            page = expected[number - 1]
            check_page('pptx', number, text, links, page, add)
            allowed = [*page[0], *page[1]]
            numeric = r'\d+(?:[.,]\d+)*'
            unsupported = set(re.findall(numeric, text)) - set(re.findall(numeric, ' '.join(allowed)))
            for value in sorted(unsupported):
                add('figures', 'pptx', number, 'Unsupported number in slide text: %s' % value)
        charts = [shape.chart for shape in shapes if shape.has_chart]
        if inputs['data_available'] and number == 2:
            if len(charts) == 1:
                check_chart(charts[0], facts, number, add)
            else:
                add('figures', 'pptx', number, 'Expected one daily chart, found %d' % len(charts))
        elif charts:
            add('figures', 'pptx', number, 'Unexpected chart on slide')
        for shape in shapes:
            if (shape.left < 0 or shape.top < 0 or shape.left + shape.width > deck.slide_width or
                    shape.top + shape.height > deck.slide_height):
                add('layout', 'pptx', number, 'Object outside slide bounds: %s' % shape.name)


def audit(inputs, pptx, pdf, source_url):
    issues = []

    def add(kind, artifact, page, message):
        issues.append({'kind': kind, 'artifact': artifact, 'page': page, 'message': message})

    expected = expected_pages(inputs, source_url)
    check_pptx(pptx, inputs, expected, add)
    with fitz.open(pdf) as doc:
        if len(doc) != len(expected):
            add('layout', 'pdf', None, 'Expected %d pages, found %d' % (len(expected), len(doc)))
        for number, (page, required) in enumerate(zip(doc, expected), 1):
            links = {link.get('uri') or link.get('file') for link in page.get_links()
                     if link.get('uri') or link.get('file')}
            text = page.get_text()
            check_page('pdf', number, text, links, required, add)
            if inputs['data_available'] and number == 2 and 'Jumlah judul per hari (WIB)' not in ' '.join(text.split()):
                add('figures', 'pdf', number, 'Daily chart label missing from PDF')

    layout = inspect_layout(pdf)
    for page in layout:
        for message in page['issues']:
            add('layout', 'pdf', page['page'], message)

    status = 'fail' if issues else 'pass'
    facts = inputs['facts']
    return {
        'status': status,
        'expected': {'slides': len(expected), 'data_available': inputs['data_available'],
                     'total': facts.get('total'), 'peak': facts.get('peak'),
                     'daily_chart_points': len(facts.get('daily_trend', [])),
                     'headline_links': len(expected[2][2]) if inputs['data_available'] else 0},
        'layout': layout,
        'issues': issues,
    }
