"""Render a four-slide news report from social-listening-mcp's structured facts."""
from datetime import date, timedelta
from textwrap import wrap
from urllib.parse import urlsplit

from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from .deck import Deck, day_label, n, period_label, rgb

STYLE = {'primary': '176458', 'accent': 'AE4634', 'dark': '152B29', 'muted': '47625F',
         'light': 'EDF5F2', 'line': 'BCD0CB'}


def linked_text(deck, slide, x, y, w, h, label, url, size):
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.netloc:
        raise ValueError('report links must be HTTP or HTTPS')
    box = deck.text(slide, deck.x(x), deck.y(y), deck.x(w), deck.y(h), label, size, color='primary')
    for paragraph in box.text_frame.paragraphs:
        paragraph.space_after = Pt(0)
        run = paragraph.runs[0]
        run.hyperlink.address = url
        run.font.color.rgb = rgb(deck.s['primary'])
        run.font.underline = False


def new_slide(deck, title=None, background='FFFFFF'):
    slide = deck.prs.slides.add_slide(deck.prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(deck.s.get(background, background))
    if title:
        deck.text(slide, deck.x(.065), deck.y(.075), deck.x(.87), deck.y(.115), title, 30, True)
    return slide


def line(deck, slide, x0, x1, y):
    rule = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, deck.x(x0), deck.y(y), deck.x(x1), deck.y(y))
    rule.shadow.inherit = False
    rule.line.color.rgb = rgb(deck.s['line'])
    rule.line.width = Pt(.75)


def query_period(query):
    return period_label({'first_day': query['start_date'], 'last_day': query['end_date']}) + ' (WIB)'


def previous_period(query):
    start, end = (date.fromisoformat(query[key]) for key in ('start_date', 'end_date'))
    return period_label({'first_day': (start - (end - start) - timedelta(days=1)).isoformat(),
                         'last_day': (start - timedelta(days=1)).isoformat()})


def coverage(deck, query, period, source_name, source_url):
    slide = new_slide(deck, background='light')
    deck.text(slide, deck.x(.065), deck.y(.17), deck.x(.85), deck.y(.06), 'CAKUPAN BERITA', 14, True, 'primary')
    deck.text(slide, deck.x(.065), deck.y(.27), deck.x(.85), deck.y(.16), query['keyword'].title(), 58, True)
    deck.text(slide, deck.x(.067), deck.y(.47), deck.x(.85), deck.y(.08), period, 22)
    line(deck, slide, .067, .93, .72)
    deck.text(slide, deck.x(.067), deck.y(.77), deck.x(.44), deck.y(.08),
              'Dataset ' + query['snapshot'], 14, color='muted')
    linked_text(deck, slide, .60, .77, .33, .08, 'Data dari ' + source_name, source_url, 14)


def show_volume(deck, facts):
    slide = new_slide(deck, 'Volume berita dan tren harian')
    series = facts['daily_trend']
    peak = facts['peak']
    deck.text(slide, deck.x(.735), deck.y(.075), deck.x(.194), deck.y(.097), n(facts['total']), 33, True,
              'primary', PP_ALIGN.RIGHT)
    deck.text(slide, deck.x(.735), deck.y(.176), deck.x(.194), deck.y(.054), 'judul tercatat', 12,
              color='muted', align=PP_ALIGN.RIGHT)
    chart = deck.daily_chart(slide, XL_CHART_TYPE.COLUMN_CLUSTERED, [day_label(row['date']) for row in series],
                             [row['count'] for row in series], .067, .241, .866, .587)
    chart.has_title = True
    chart.chart_title.text_frame.text = 'Jumlah judul per hari (WIB)'
    title = chart.chart_title.text_frame.paragraphs[0].runs[0]
    title.font.name, title.font.size = deck.s['font'], Pt(14)
    title.font.color.rgb = rgb(deck.s['muted'])
    chart.value_axis.minimum_scale = 0
    chart.value_axis.major_gridlines.format.line.color.rgb = rgb(deck.s['line'])
    if peak is not None:
        point = next(index for index, row in enumerate(series) if row['date'] == peak['at'])
        fill = chart.series[0].points[point].format.fill
        fill.solid()
        fill.fore_color.rgb = rgb(deck.s['accent'])
    summary = 'Perbandingan dengan periode sebelumnya berada di luar cakupan.'
    if facts['change'] is not None:
        change = facts['change']
        summary = ('Periode sebelumnya mencatat %s judul.' % n(change['previous_total']))
    deck.text(slide, deck.x(.068), deck.y(.876), deck.x(.86), deck.y(.06), summary, 13, color='muted')


def show_peak(deck, facts):
    slide = new_slide(deck, 'Puncak dan contoh berita')
    peak = facts['peak']
    if peak is None:
        deck.text(slide, deck.x(.068), deck.y(.26), deck.x(.8), deck.y(.16),
                  'Pencarian menghasilkan nol judul dalam periode ini.', 22)
        return
    deck.text(slide, deck.x(.066), deck.y(.23), deck.x(.27), deck.y(.19), n(peak['count']), 59, True, 'accent')
    deck.text(slide, deck.x(.07), deck.y(.435), deck.x(.27), deck.y(.10), 'judul pada ' + day_label(peak['at']),
              19, True)
    for index, story in enumerate(facts['top_stories'][:3]):
        y = .218 + index * .171
        deck.text(slide, deck.x(.392), deck.y(y), deck.x(.54), deck.y(.043), story['source'], 11, True, 'muted')
        headline = wrap(story['text'], width=65, break_long_words=False, break_on_hyphens=False)
        linked_text(deck, slide, .392, y + .045, .54, .108, headline, story['url'], 16)
        line(deck, slide, .392, .93, y + .152)


def limitations(deck, query, facts, source_name, source_url):
    slide = new_slide(deck, 'Batasan data', 'light')
    rows = [('Cakupan sumber', 'Dataset ini berisi judul berita. Volume menunjukkan intensitas pemberitaan.'),
            ('Pengelompokan berita', 'Judul dikelompokkan berdasarkan kemiripan teks. Hasilnya bersifat perkiraan.')]
    if facts['change'] is None:
        rows.append(('Periode pembanding', previous_period(query) + ' berada di luar cakupan snapshot.'))
    for index, (label, detail) in enumerate(rows):
        y = .24 + index * .165
        line(deck, slide, .068, .93, y)
        deck.text(slide, deck.x(.068), deck.y(y + .028), deck.x(.335), deck.y(.1), label, 16, True)
        deck.text(slide, deck.x(.41), deck.y(y + .026), deck.x(.52), deck.y(.104), detail, 15)
    linked_text(deck, slide, .068, .856, .5, .058, 'Data dari ' + source_name, source_url, 13)


def build_report(inputs, out_path, source_name, source_url):
    """Render the approved outline. A missing range produces a coverage-only slide."""
    query, facts = inputs['query'], inputs['facts']
    period = query_period(query)
    deck = Deck(STYLE)
    if not inputs['data_available']:
        slide = new_slide(deck, 'Cakupan data', 'light')
        deck.text(slide, deck.x(.066), deck.y(.215), deck.x(.86), deck.y(.075),
                  query['keyword'].title(), 25, True)
        deck.text(slide, deck.x(.066), deck.y(.305), deck.x(.86), deck.y(.075), period, 21)
        deck.text(slide, deck.x(.067), deck.y(.39), deck.x(.82), deck.y(.16),
                  'Data belum tersedia untuk rentang yang diminta.', 24)
        deck.text(slide, deck.x(.068), deck.y(.59), deck.x(.82), deck.y(.14), inputs['warnings'], 15, color='muted')
        deck.text(slide, deck.x(.066), deck.y(.76), deck.x(.55), deck.y(.065),
                  'Dataset ' + query['snapshot'], 13, color='muted')
        linked_text(deck, slide, .068, .856, .5, .058, 'Data dari ' + source_name, source_url, 13)
    else:
        daily = facts['daily_trend']
        if sum(row['count'] for row in daily) != facts['total']:
            raise ValueError('daily headline counts do not add up to the report total')
        peak = facts['peak']
        if peak is not None and max(daily, key=lambda row: row['count']) != {'date': peak['at'], 'count': peak['count']}:
            raise ValueError('the reported peak does not match the daily series')
        coverage(deck, query, period, source_name, source_url)
        show_volume(deck, facts)
        show_peak(deck, facts)
        limitations(deck, query, facts, source_name, source_url)
    deck.prs.save(out_path)
    return len(deck.prs.slides)
