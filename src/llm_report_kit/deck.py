"""PowerPoint primitives used by the public news-report template."""
from datetime import date

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Pt

MONTHS = "Jan Feb Mar Apr Mei Jun Jul Agu Sep Okt Nov Des".split()


def rgb(color):
    return RGBColor.from_string(color)


def n(value):
    return f"{value:,}".replace(",", ".")


def day_label(value):
    day = date.fromisoformat(value)
    return f"{day.day} {MONTHS[day.month - 1]}"


def period_label(bounds):
    start, end = bounds["first_day"], bounds["last_day"]
    first = day_label(start)
    if start[:4] != end[:4]:
        first += f" {start[:4]}"
    return f"{first} - {day_label(end)} {end[:4]}"


class Deck:
    def __init__(self, style):
        self.prs = Presentation()
        self.w, self.h = Emu(12192000), Emu(6858000)
        self.prs.slide_width, self.prs.slide_height = self.w, self.h
        self.s = {**style, "font": "Liberation Sans"}

    def x(self, fraction):
        return round(self.w * fraction)

    def y(self, fraction):
        return round(self.h * fraction)

    def text(self, slide, x, y, w, h, text, size, bold=False, color="dark", align=PP_ALIGN.LEFT):
        box = slide.shapes.add_textbox(x, y, w, h)
        frame = box.text_frame
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = Pt(2)
        lines = [text] if isinstance(text, str) else text
        for index, line in enumerate(lines):
            paragraph = frame.add_paragraph() if index else frame.paragraphs[0]
            paragraph.alignment = align
            paragraph.space_after = Pt(3)
            run = paragraph.add_run()
            run.text = line
            run.font.name, run.font.size, run.font.bold = self.s["font"], Pt(size), bold
            run.font.color.rgb = rgb(self.s[color])
        return box

    def daily_chart(self, slide, kind, labels, counts, x, y, w, h):
        data = CategoryChartData()
        data.categories = labels
        data.add_series("Judul", counts)
        shape = slide.shapes.add_chart(kind, self.x(x), self.y(y), self.x(w), self.y(h), data)
        chart = shape.chart
        chart.has_legend = False
        chart.font.name, chart.font.size = self.s["font"], Pt(10)
        fill = chart.series[0].format.fill
        fill.solid()
        fill.fore_color.rgb = rgb(self.s["primary"])
        return chart
